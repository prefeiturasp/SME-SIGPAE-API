"""Modelos do submódulo de solicitações de dieta especial.

Define o modelo central :class:`SolicitacaoDietaEspecial`, os catálogos de
apoio (motivos de negação, motivos de alteração de U.E., alergias e
intolerâncias, classificações de dieta), o :class:`Anexo` e a view não
gerenciada :class:`SolicitacoesDietaEspecialAtivasInativasPorAluno`.

As listas de constantes no topo do módulo agrupam os eventos de log
(:class:`~src.dados_comuns.models.LogSolicitacoesUsuario`) que caracterizam
cada situação da solicitação (pendente, autorizada, negada ou cancelada).
"""

from __future__ import annotations

import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.db.models import Q, QuerySet
from django_prometheus.models import ExportModelOperationsMixin

from src.dados_comuns.behaviors import (
    Ativavel,
    CriadoEm,
    CriadoPor,
    Descritivel,
    Logs,
    Nomeavel,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    TemPrioridade,
)
from src.dados_comuns.constants import MODEL_ESCOLA
from src.dados_comuns.fluxo_status import FluxoDietaEspecialPartindoDaEscola
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dados_comuns.utils import convert_base64_to_contentfile
from src.escola.api.serializers import AlunoSerializer
from src.escola.models import Aluno, Escola

PENDENTES_EVENTO_DIETA_ESPECIAL: list[int] = [
    LogSolicitacoesUsuario.INICIO_FLUXO,
    LogSolicitacoesUsuario.INICIO_FLUXO_INATIVACAO,
    LogSolicitacoesUsuario.INICIO_FLUXO_ALTERACAO_UE_DIETA_ESPECIAL,
]

AUTORIZADO_EVENTO_DIETA_ESPECIAL: list[int] = [
    LogSolicitacoesUsuario.CODAE_AUTORIZOU,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
    LogSolicitacoesUsuario.INICIO_FLUXO,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_ALTERACAO_UE_DIETA_ESPECIAL,
]

NEGADOS_EVENTO_DIETA_ESPECIAL: list[int] = [
    LogSolicitacoesUsuario.CODAE_NEGOU,
    LogSolicitacoesUsuario.CODAE_NEGOU_INATIVACAO,
    LogSolicitacoesUsuario.CODAE_NEGOU_CANCELAMENTO,
    LogSolicitacoesUsuario.CODAE_NEGOU_ALTERACAO_UE_DIETA_ESPECIAL,
]

CANCELADOS_EVENTO_DIETA_ESPECIAL: list[int] = [
    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL,
    LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA,
    LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
    LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    LogSolicitacoesUsuario.CANCELADO_ENCERRAMENTO_MATRICULA,
]

CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP: list[int] = [
    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
    LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL,
    LogSolicitacoesUsuario.CANCELADO_ENCERRAMENTO_MATRICULA,
]


class MotivoNegacao(Descritivel):
    """Catálogo de motivos de negação de uma solicitação de dieta especial.

    Attributes:
        processo (str): Processo ao qual o motivo se aplica. Pode ser
            ``CANCELAMENTO`` (solicitação de cancelamento de uma dieta especial ativa) ou ``INCLUSAO``
            (solicitação de inclusão de uma nova dieta especial).
    """

    CANCELAMENTO = "CANCELAMENTO"
    INCLUSAO = "INCLUSAO"

    PROCESSO_CHOICES = (
        (CANCELAMENTO, "Solicitação de Cancelamento"),
        (INCLUSAO, "Solicitação de Inclusão"),
    )

    processo = models.CharField(
        choices=PROCESSO_CHOICES, default=INCLUSAO, blank=False, max_length=20
    )

    def __str__(self) -> str:
        """Retorna a descrição do motivo de negação."""
        return self.descricao


class MotivoAlteracaoUE(Descritivel, Nomeavel, TemChaveExterna, Ativavel):
    """Catálogo de motivos de alteração de unidade educacional da dieta.

    Motivos possíveis:

    - **Recreio nas Férias**: a criança vai passar alguns dias em outra
      unidade educacional durante as férias escolares e precisa da sua dieta
      especial atendida nessa outra unidade.
    - **Outro**: a criança vai passar alguns dias em outra unidade educacional
      por algum outro motivo e precisa da sua dieta especial atendida nessa
      outra unidade.
    """

    def __str__(self) -> str:
        """Retorna o nome do motivo de alteração de U.E."""
        return self.nome

    class Meta:
        verbose_name = "Motivo Alteração U.E"
        verbose_name_plural = "Motivo Alteração U.E"


class AlergiaIntolerancia(Descritivel):
    """Catálogo de alergias e intolerâncias alimentares (diagnósticos).

    Exemplos de diagnósticos:

    - Alergias (ovo, leite, amendoim)
    - TEA
    - Diabetes
    - Doenças
    - Intolerâncias
    """

    def __str__(self) -> str:
        """Retorna a descrição da alergia/intolerância."""
        return self.descricao


class ClassificacaoDieta(Descritivel, Nomeavel):
    """Catálogo de classificações de dieta especial.

    Classificações possíveis:

    - **Tipo A**: alimentos diferenciados mais caros para troca; a troca vale
      apenas para o lanche.
    - **Tipo A Enteral / Aminoácidos**: alimentos caros para troca igual ao
      tipo A; a troca vale para lanche e refeição.
    - **Tipo B**: alimentos diferenciados, com menor custo que os do tipo A.
    - **Tipo C**: apenas altera algum ingrediente por outro, sem custo
      adicional. Ex.: troca peixe por carne.
    """

    def __str__(self) -> str:
        """Retorna o nome da classificação de dieta."""
        return self.nome


class SolicitacaoDietaEspecial(
    ExportModelOperationsMixin("dieta_especial"),
    TemChaveExterna,
    CriadoEm,
    CriadoPor,
    FluxoDietaEspecialPartindoDaEscola,
    TemPrioridade,
    Logs,
    TemIdentificadorExternoAmigavel,
    Ativavel,
):
    """Solicitação de dieta especial de um aluno.

    Modelo central do módulo de dieta especial. Representa a solicitação de
    dieta especial de um aluno e percorre um fluxo de autorização que envolve
    a escola e a CODAE. Pode ser uma inclusão comum, uma alteração de U.E.,
    um cancelamento de dieta ou uma solicitação para aluno não matriculado.
    """

    COMUM = "COMUM"
    ALUNO_NAO_MATRICULADO = "ALUNO_NAO_MATRICULADO"
    ALTERACAO_UE = "ALTERACAO_UE"
    CANCELAMENTO_DIETA = "CANCELAMENTO_DIETA"

    DESCRICAO_SOLICITACAO = {
        "CODAE_A_AUTORIZAR": "Solicitação de Inclusão",
        "CODAE_NEGOU_PEDIDO": "Negada a Inclusão",
        "CODAE_AUTORIZADO": "Autorizada",
        "ESCOLA_SOLICITOU_INATIVACAO": "Solicitação de Cancelamento",
        "CODAE_NEGOU_INATIVACAO": "Negada o Cancelamento",
        "CODAE_AUTORIZOU_INATIVACAO": "Cancelamento Autorizado",
        "ESCOLA_CANCELOU": "Cancelada pela Unidade Escolar",
    }

    TIPO_SOLICITACAO_CHOICES = [
        (COMUM, "Comum"),
        (ALUNO_NAO_MATRICULADO, "Aluno não matriculado"),
        (ALTERACAO_UE, "Alteração U.E"),
        (CANCELAMENTO_DIETA, "Cancelamento de dieta especial"),
    ]

    aluno = models.ForeignKey(
        "escola.Aluno",
        null=True,
        on_delete=models.PROTECT,
        related_name="dietas_especiais",
    )
    nome_completo_pescritor = models.CharField(
        "Nome completo do pescritor da receita",
        max_length=200,
        validators=[MinLengthValidator(6)],
        blank=True,
    )
    registro_funcional_pescritor = models.CharField(
        "Registro funcional do pescritor da receita",
        help_text="CRN/CRM/CRFa...",
        max_length=200,
        validators=[MinLengthValidator(4), MaxLengthValidator(6)],
        blank=True,
    )
    registro_funcional_nutricionista = models.CharField(
        "Registro funcional do nutricionista",
        help_text="CRN/CRM/CRFa...",
        max_length=200,
        validators=[MinLengthValidator(6)],
        blank=True,
    )
    # Preenchido pela Escola
    observacoes = models.TextField("Observações", blank=True)

    # Preenchido pela_ CODAE ao autorizar a dieta
    informacoes_adicionais = models.TextField("Informações Adicionais", blank=True)

    protocolo_padrao = models.ForeignKey(
        "ProtocoloPadraoDietaEspecial",
        on_delete=models.PROTECT,
        related_name="solicitacoes_dietas_especiais",
        blank=True,
        null=True,
    )

    nome_protocolo = models.TextField("Nome do Protocolo", blank=True)

    # Preenchido pela NutriCODAE ao autorizar a dieta
    orientacoes_gerais = models.TextField("Orientações Gerais", blank=True)

    # TODO: Confirmar se PROTECT é a melhor escolha para o campos abaixo
    classificacao = models.ForeignKey(
        "ClassificacaoDieta", blank=True, null=True, on_delete=models.PROTECT
    )
    alergias_intolerancias = models.ManyToManyField("AlergiaIntolerancia", blank=True)

    # TODO: Confirmar se PROTECT é a melhor escolha para o campos abaixo
    motivo_negacao = models.ForeignKey(
        "MotivoNegacao", on_delete=models.PROTECT, null=True
    )

    # TODO: Mover essa justificativa para o log de transição de status
    justificativa_negacao = models.TextField(blank=True)

    data_termino = models.DateField(null=True)

    motivo_alteracao_ue = models.ForeignKey(
        "MotivoAlteracaoUE", blank=True, null=True, on_delete=models.CASCADE
    )

    escola_destino = models.ForeignKey(
        MODEL_ESCOLA, blank=True, null=True, on_delete=models.CASCADE
    )

    dieta_alterada = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.CASCADE
    )

    data_inicio = models.DateField(null=True, blank=True)

    tipo_solicitacao = models.CharField(
        max_length=30,
        choices=TIPO_SOLICITACAO_CHOICES,
        default="COMUM",
    )

    observacoes_alteracao = models.TextField("Observações Alteração", blank=True)

    caracteristicas_do_alimento = models.TextField(
        "Características dos alimentos", blank=True
    )

    conferido = models.BooleanField("Marcar como conferido?", default=False)

    eh_importado = models.BooleanField("Proveniente de importacao?", default=False)

    dieta_para_recreio_ferias = models.BooleanField(
        "Dieta para Recreio nas Férias", default=False
    )

    @classmethod
    def _get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
        cls, solicitacoes: QuerySet[SolicitacaoDietaEspecial], status: list[int]
    ) -> int:
        """Conta quantas solicitações distintas já passaram pelos status informados.

        Args:
            solicitacoes (QuerySet[SolicitacaoDietaEspecial]): Queryset de
                solicitações a analisar.
            status (list[int]): Eventos de log que caracterizam os status.

        Returns:
            int: Quantidade de solicitações que já estiveram em ao menos um
            dos status informados.
        """
        uuids = set(list(solicitacoes.values_list("uuid", flat=True)))
        return len(
            set(
                LogSolicitacoesUsuario.objects.filter(
                    uuid_original__in=uuids, status_evento__in=status
                ).values_list("uuid_original", flat=True)
            )
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_pendentes(
        cls, solicitacoes: QuerySet[SolicitacaoDietaEspecial]
    ) -> int:
        """Conta quantas solicitações do queryset já estiveram pendentes.

        Args:
            solicitacoes (QuerySet[SolicitacaoDietaEspecial]): Queryset de
                solicitações a analisar.

        Returns:
            int: Quantidade de solicitações que já estiveram pendentes.
        """
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, PENDENTES_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_autorizadas(
        cls, solicitacoes: QuerySet[SolicitacaoDietaEspecial]
    ) -> int:
        """Conta quantas solicitações do queryset já estiveram autorizadas.

        Args:
            solicitacoes (QuerySet[SolicitacaoDietaEspecial]): Queryset de
                solicitações a analisar.

        Returns:
            int: Quantidade de solicitações que já estiveram autorizadas.
        """
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, AUTORIZADO_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_negadas(
        cls, solicitacoes: QuerySet[SolicitacaoDietaEspecial]
    ) -> int:
        """Conta quantas solicitações do queryset já estiveram negadas.

        Args:
            solicitacoes (QuerySet[SolicitacaoDietaEspecial]): Queryset de
                solicitações a analisar.

        Returns:
            int: Quantidade de solicitações que já estiveram negadas.
        """
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, NEGADOS_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_canceladas(
        cls, solicitacoes: QuerySet[SolicitacaoDietaEspecial]
    ) -> int:
        """Conta quantas solicitações do queryset já estiveram canceladas.

        Considera apenas solicitações do tipo ``ALTERACAO_UE`` e ``COMUM``.

        Args:
            solicitacoes (QuerySet[SolicitacaoDietaEspecial]): Queryset de
                solicitações a analisar.

        Returns:
            int: Quantidade de solicitações que já estiveram canceladas.
        """
        solicitacoes = solicitacoes.filter(
            tipo_solicitacao__in=["ALTERACAO_UE", "COMUM"]
        )
        status = (
            CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP + CANCELADOS_EVENTO_DIETA_ESPECIAL
        )
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, status
        )

    @classmethod
    def get_totais_gerencial_dietas(
        cls, queryset: QuerySet[SolicitacaoDietaEspecial] | None = None
    ) -> dict[str, int]:
        """Calcula os totais gerenciais de dietas (solicitadas e por situação).

        Args:
            queryset (QuerySet[SolicitacaoDietaEspecial] | None): Queryset
                opcional de solicitações. Se ``None``, usa todas as
                solicitações.

        Returns:
            dict[str, int]: Dicionário com os totais de solicitações,
            autorizadas, negadas e canceladas.
        """
        queryset = (
            SolicitacaoDietaEspecial.objects.all() if queryset is None else queryset
        )

        total_solicitacoes = (
            SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_pendentes(
                queryset
            )
        )
        total_autorizadas = SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_autorizadas(
            queryset
        )
        total_negadas = (
            SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_negadas(
                queryset
            )
        )
        total_canceladas = SolicitacaoDietaEspecial.quantidade_solicitacoes_que_ja_estiveram_canceladas(
            queryset
        )

        return {
            "total_solicitacoes": total_solicitacoes,
            "total_autorizadas": total_autorizadas,
            "total_negadas": total_negadas,
            "total_canceladas": total_canceladas,
        }

    @classmethod
    def aluno_possui_dieta_especial_autorizada_alteracao_ue_recreio_ferias(
        cls,
        aluno: Aluno,
        dieta_alterada: SolicitacaoDietaEspecial,
        motivo_recreio_ferias: MotivoAlteracaoUE,
    ) -> bool:
        """Verifica se o aluno já possui alteração de U.E. autorizada para recreio nas férias.

        Args:
            aluno (Aluno): Aluno a verificar.
            dieta_alterada (SolicitacaoDietaEspecial): Dieta alterada
                (solicitação original).
            motivo_recreio_ferias (MotivoAlteracaoUE): Motivo de alteração de
                U.E. de recreio nas férias.

        Returns:
            bool: ``True`` se já existir alteração de U.E. autorizada com o
            motivo informado; ``False`` caso contrário.
        """
        return cls.objects.filter(
            aluno=aluno,
            dieta_alterada=dieta_alterada,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            tipo_solicitacao="ALTERACAO_UE",
            motivo_alteracao_ue=motivo_recreio_ferias,
        ).exists()

    @classmethod
    def aluno_possui_dieta_especial_pendente(cls, aluno: Aluno) -> bool:
        """Verifica se o aluno possui alguma dieta especial pendente de autorização.

        Args:
            aluno (Aluno): Aluno a verificar.

        Returns:
            bool: ``True`` se existir dieta especial com status
            ``CODAE_A_AUTORIZAR``; ``False`` caso contrário.
        """
        return cls.objects.filter(
            aluno=aluno, status=cls.workflow_class.CODAE_A_AUTORIZAR
        ).exists()

    @property
    def DESCRICAO(self) -> str:
        """Retorna a descrição legível da solicitação conforme o status atual.

        Returns:
            str: Texto no formato ``"Dieta Especial - {descricao}"``, ou
            ``"Dieta Especial"`` quando não há descrição mapeada.
        """
        descricao = self.DESCRICAO_SOLICITACAO.get(self.status)
        return f"Dieta Especial - {descricao}" if descricao else "Dieta Especial"

    # Property necessária para retornar dados no serializer de criação de
    # Dieta Especial
    @property
    def aluno_json(self) -> dict:
        """Retorna os dados do aluno serializados.

        Returns:
            dict: Dicionário com os dados do aluno retornados pelo
            :class:`~src.escola.api.serializers.AlunoSerializer`.
        """
        return AlunoSerializer(self.aluno).data

    @property
    def anexos(self) -> QuerySet[Anexo]:
        """Retorna os anexos associados à solicitação.

        Returns:
            QuerySet[Anexo]: Queryset com os anexos da solicitação.
        """
        return self.anexo_set.all()

    @property
    def numero_alunos(self) -> str:
        """Retorna a quantidade de alunos associada à solicitação.

        Returns:
            str: String vazia (mantida por compatibilidade com o serializer).
        """
        return ""

    @property
    def escola(self) -> Escola | None:
        """Retorna a escola vinculada ao rastro da solicitação.

        Returns:
            Escola | None: Escola associada ao rastro da solicitação, ou
            ``None`` se não houver rastro.
        """
        return self.rastro_escola

    def cria_anexos_inativacao(self, anexos: list[dict[str, Any]]) -> None:
        """Cria os anexos de laudo de alta para a inativação da dieta.

        Args:
            anexos (list[dict[str, Any]]): Lista de anexos, em que cada item
                possui as chaves ``base64`` (conteúdo do arquivo) e ``nome``
                (nome do arquivo).

        Raises:
            AssertionError: Se ``anexos`` não for uma lista não vazia.
        """
        assert isinstance(anexos, list), "anexos precisa ser uma lista"  # nosec
        assert len(anexos) > 0, "anexos não pode ser vazio"  # nosec
        for anexo in anexos:
            data = convert_base64_to_contentfile(anexo.get("base64"))
            Anexo.objects.create(
                solicitacao_dieta_especial=self,
                arquivo=data,
                nome=anexo.get("nome", ""),
                eh_laudo_alta=True,
            )

    @property
    def substituicoes(self) -> QuerySet:
        """Retorna as substituições de alimento associadas à solicitação.

        Returns:
            QuerySet: Queryset de :class:`~src.dieta_especial.protocolo_padrao.models.SubstituicaoAlimento`.
        """
        return self.substituicaoalimento_set.all()

    @property
    def str_dre_lote_escola(self) -> str:
        """Monta uma string legível com DRE, lote e escola de destino.

        Returns:
            str: Texto no formato ``"DRE X - LOTE - ESCOLA"``, usando
            ``"SEM DRE"``, ``"SEM LOTE"`` e ``"SEM ESCOLA"`` quando os dados
            não estiverem disponíveis.
        """
        dre = "SEM DRE"
        lote = "SEM LOTE"
        escola = "SEM ESCOLA"
        if self.escola_destino:
            escola = f"{self.escola_destino.nome}"
            if self.escola_destino.diretoria_regional:
                dre = (
                    f'DRE {self.escola_destino.diretoria_regional.nome.split(" ")[-1]}'
                )
            if self.escola_destino.lote:
                lote = f"{self.escola_destino.lote.nome}"
        return f"{dre}  - {lote} - {escola}"

    def salvar_log_transicao(
        self, status_evento: int, usuario: Any, **kwargs: Any
    ) -> None:
        """Registra um log de transição de status da solicitação.

        Args:
            status_evento (int): Evento de log (transição de status) a gravar.
            usuario (perfil.Usuario): Usuário responsável pela transição.
            **kwargs (Any): Argumentos extras. Aceita ``justificativa``
                (str) para a transição.
        """
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    @property
    def display_nutricionista_with_registro_funcional(self) -> str:
        """Retorna o nome do nutricionista que autorizou a dieta, com registro funcional.

        Returns:
            str: Texto ``"Elaborado por {nome} - RF {registro}"`` ou, quando o
            usuário não possui registro funcional, o registro funcional
            informado na solicitação.
        """
        usuario = self.logs.get(
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
        ).usuario
        if usuario.registro_funcional:
            return f"Elaborado por {usuario.nome} - RF {usuario.registro_funcional}"
        return self.registro_funcional_nutricionista

    @property
    def data_ultimo_log(self) -> str | None:
        """Retorna a data do último log da solicitação.

        Returns:
            str | None: Data formatada ``DD/MM/AAAA`` do último log, ou
            ``None`` se não houver logs.
        """
        return (
            datetime.datetime.strftime(self.logs.last().criado_em, "%d/%m/%Y")
            if self.logs
            else None
        )

    @property
    def get_log_autorizado(self) -> LogSolicitacoesUsuario | None:
        """Retorna o log de autorização da solicitação, se existir.

        Returns:
            LogSolicitacoesUsuario | None: Log de autorização (``CODAE_AUTORIZOU``
            ou ``CODAE_AUTORIZOU_ALTERACAO_UE_DIETA_ESPECIAL``), ou ``None``
            se a solicitação ainda não foi autorizada.
        """
        try:
            return self.logs.get(
                Q(status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU)
                | Q(
                    status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_ALTERACAO_UE_DIETA_ESPECIAL
                )
            )
        except LogSolicitacoesUsuario.DoesNotExist:
            return None

    def clean(self) -> None:
        """Valida os campos da solicitação antes de salvar.

        Raises:
            ValidationError: Se a dieta for para recreio nas férias e não
                possuir período preenchido, ou se a data final for anterior
                à data inicial.
        """
        super().clean()
        if self.dieta_para_recreio_ferias:
            if not self.data_inicio or not self.data_termino:
                raise ValidationError(
                    "Os campos de período são obrigatórios quando dieta para recreio nas férias está selecionada."
                )
            if self.data_termino < self.data_inicio:
                raise ValidationError(
                    "A data final não pode ser anterior à data inicial."
                )

    class Meta:
        ordering = ("-ativo", "-criado_em")
        verbose_name = "Solicitação de dieta especial"
        verbose_name_plural = "Solicitações de dieta especial"

    def __str__(self) -> str:
        """Retorna a representação legível da solicitação.

        Returns:
            str: ``"{código_eol}: {nome}"`` do aluno, ou
            ``"Solicitação #{id_externo}"`` quando não há aluno vinculado.
        """
        if self.aluno:
            return f"{self.aluno.codigo_eol}: {self.aluno.nome}"
        return f"Solicitação #{self.id_externo}"


class Anexo(ExportModelOperationsMixin("anexo"), models.Model):
    """Anexo (arquivo) vinculado a uma solicitação de dieta especial.

    Attributes:
        solicitacao_dieta_especial (SolicitacaoDietaEspecial): Solicitação à
            qual o anexo pertence.
        nome (str): Nome do arquivo.
        arquivo (FileField): Arquivo enviado.
        eh_laudo_alta (bool): Indica se o anexo é um laudo de alta.
    """

    solicitacao_dieta_especial = models.ForeignKey(
        SolicitacaoDietaEspecial, on_delete=models.CASCADE
    )
    nome = models.CharField(max_length=100, blank=True)
    arquivo = models.FileField()
    eh_laudo_alta = models.BooleanField(default=False)

    def __str__(self) -> str:
        """Retorna o nome do anexo."""
        return self.nome


class SolicitacoesDietaEspecialAtivasInativasPorAluno(models.Model):
    """View não gerenciada com a quantidade de dietas ativas e inativas por aluno.

    Attributes:
        aluno (Aluno): Aluno referenciado (chave primária).
        ativas (int): Quantidade de dietas ativas do aluno.
        inativas (int): Quantidade de dietas inativas do aluno.
    """

    aluno = models.OneToOneField(Aluno, on_delete=models.DO_NOTHING, primary_key=True)
    ativas = models.IntegerField()
    inativas = models.IntegerField()

    class Meta:
        managed = False
        db_table = "dietas_ativas_inativas_por_aluno"
