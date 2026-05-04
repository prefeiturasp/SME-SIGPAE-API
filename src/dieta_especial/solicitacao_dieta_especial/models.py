import datetime

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
from src.dados_comuns.fluxo_status import FluxoDietaEspecialPartindoDaEscola
from src.dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem
from src.dados_comuns.utils import convert_base64_to_contentfile
from src.escola.api.serializers import AlunoSerializer
from src.escola.models import Aluno

PENDENTES_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.INICIO_FLUXO,
    LogSolicitacoesUsuario.INICIO_FLUXO_INATIVACAO,
    LogSolicitacoesUsuario.INICIO_FLUXO_ALTERACAO_UE_DIETA_ESPECIAL,
]

AUTORIZADO_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.CODAE_AUTORIZOU,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
    LogSolicitacoesUsuario.INICIO_FLUXO,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_ALTERACAO_UE_DIETA_ESPECIAL,
]

NEGADOS_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.CODAE_NEGOU,
    LogSolicitacoesUsuario.CODAE_NEGOU_INATIVACAO,
    LogSolicitacoesUsuario.CODAE_NEGOU_CANCELAMENTO,
    LogSolicitacoesUsuario.CODAE_NEGOU_ALTERACAO_UE_DIETA_ESPECIAL,
]

CANCELADOS_EVENTO_DIETA_ESPECIAL = [
    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL,
    LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA,
    LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
    LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    LogSolicitacoesUsuario.CANCELADO_ENCERRAMENTO_MATRICULA,
]

CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP = [
    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
    LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
    LogSolicitacoesUsuario.CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL,
    LogSolicitacoesUsuario.CANCELADO_ENCERRAMENTO_MATRICULA,
]


class MotivoNegacao(Descritivel):
    CANCELAMENTO = "CANCELAMENTO"
    INCLUSAO = "INCLUSAO"

    PROCESSO_CHOICES = (
        (CANCELAMENTO, "Solicitação de Cancelamento"),
        (INCLUSAO, "Solicitação de Inclusão"),
    )

    processo = models.CharField(
        choices=PROCESSO_CHOICES, default=INCLUSAO, blank=False, max_length=20
    )

    def __str__(self):
        return self.descricao


class MotivoAlteracaoUE(Descritivel, Nomeavel, TemChaveExterna, Ativavel):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motivo Alteração U.E"
        verbose_name_plural = "Motivo Alteração U.E"


class AlergiaIntolerancia(Descritivel):
    def __str__(self):
        return self.descricao


class ClassificacaoDieta(Descritivel, Nomeavel):
    def __str__(self):
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
        "escola.Escola", blank=True, null=True, on_delete=models.CASCADE
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
        cls, solicitacoes: QuerySet, status: list
    ):
        uuids = set(list(solicitacoes.values_list("uuid", flat=True)))
        return len(
            set(
                LogSolicitacoesUsuario.objects.filter(
                    uuid_original__in=uuids, status_evento__in=status
                ).values_list("uuid_original", flat=True)
            )
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_pendentes(cls, solicitacoes):
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, PENDENTES_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_autorizadas(cls, solicitacoes):
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, AUTORIZADO_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_negadas(cls, solicitacoes):
        return cls._get_quantidade_solicitacoes_que_ja_estiveram_nos_status(
            solicitacoes, NEGADOS_EVENTO_DIETA_ESPECIAL
        )

    @classmethod
    def quantidade_solicitacoes_que_ja_estiveram_canceladas(cls, solicitacoes):
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
    def get_totais_gerencial_dietas(cls, queryset=None):
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
        cls, aluno, dieta_alterada, motivo_recreio_ferias
    ):
        return cls.objects.filter(
            aluno=aluno,
            dieta_alterada=dieta_alterada,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            tipo_solicitacao="ALTERACAO_UE",
            motivo_alteracao_ue=motivo_recreio_ferias,
        ).exists()

    @classmethod
    def aluno_possui_dieta_especial_pendente(cls, aluno):
        return cls.objects.filter(
            aluno=aluno, status=cls.workflow_class.CODAE_A_AUTORIZAR
        ).exists()

    @property
    def DESCRICAO(self):
        descricao = self.DESCRICAO_SOLICITACAO.get(self.status)
        return f"Dieta Especial - {descricao}" if descricao else "Dieta Especial"

    # Property necessária para retornar dados no serializer de criação de
    # Dieta Especial
    @property
    def aluno_json(self):
        return AlunoSerializer(self.aluno).data

    @property
    def anexos(self):
        return self.anexo_set.all()

    @property
    def numero_alunos(self):
        return ""

    @property
    def escola(self):
        return self.rastro_escola

    def cria_anexos_inativacao(self, anexos):
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
    def substituicoes(self):
        return self.substituicaoalimento_set.all()

    @property
    def str_dre_lote_escola(self):
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

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(tipo=TemplateMensagem.DIETA_ESPECIAL)
        template_troca = {
            "@id": self.id_externo,
            "@criado_em": str(self.criado_em),
            "@criado_por": str(self.criado_por),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "https://teste.com",
        }
        corpo = template.template_html
        for chave, valor in template_troca.items():
            corpo = corpo.replace(chave, valor)
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
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
    def display_nutricionista_with_registro_funcional(self):
        usuario = self.logs.get(
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
        ).usuario
        if usuario.registro_funcional:
            return f"Elaborado por {usuario.nome} - RF {usuario.registro_funcional}"
        return self.registro_funcional_nutricionista

    @property
    def data_ultimo_log(self):
        return (
            datetime.datetime.strftime(self.logs.last().criado_em, "%d/%m/%Y")
            if self.logs
            else None
        )

    @property
    def get_log_autorizado(self):
        try:
            return self.logs.get(
                Q(status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU)
                | Q(
                    status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_ALTERACAO_UE_DIETA_ESPECIAL
                )
            )
        except LogSolicitacoesUsuario.DoesNotExist:
            return None

    def clean(self):
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

    def __str__(self):
        if self.aluno:
            return f"{self.aluno.codigo_eol}: {self.aluno.nome}"
        return f"Solicitação #{self.id_externo}"


class Anexo(ExportModelOperationsMixin("anexo"), models.Model):
    solicitacao_dieta_especial = models.ForeignKey(
        SolicitacaoDietaEspecial, on_delete=models.CASCADE
    )
    nome = models.CharField(max_length=100, blank=True)
    arquivo = models.FileField()
    eh_laudo_alta = models.BooleanField(default=False)

    def __str__(self):
        return self.nome


class SolicitacoesDietaEspecialAtivasInativasPorAluno(models.Model):
    aluno = models.OneToOneField(Aluno, on_delete=models.DO_NOTHING, primary_key=True)
    ativas = models.IntegerField()
    inativas = models.IntegerField()

    class Meta:
        managed = False
        db_table = "dietas_ativas_inativas_por_aluno"
