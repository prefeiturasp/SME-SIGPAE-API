from django.db import models
from django.db.models import Sum

from src.cardapio.base.models import TipoAlimentacao
from src.cardapio.suspensao_alimentacao.managers.suspensao_alimentacao_managers import (
    GrupoSuspensaoAlimentacaoDestaSemanaManager,
    GrupoSuspensaoAlimentacaoDesteMesManager,
)
from src.dados_comuns.behaviors import (
    CanceladoIndividualmente,
    CriadoEm,
    CriadoPor,
    Logs,
    Nomeavel,
    TemChaveExterna,
    TemData,
    TemIdentificadorExternoAmigavel,
    TemObservacao,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
)
from src.dados_comuns.fluxo_status import FluxoInformativoPartindoDaEscola
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dados_comuns.prometheus_mixin import ExportModelOperationsMixin
from src.dados_comuns.utils import patch_docs


class MotivoSuspensao(
    ExportModelOperationsMixin("motivo_suspensao"), Nomeavel, TemChaveExterna
):
    """Motivo de Suspensão de um dia letivo em uma unidade educacional.

    Exemplos:
            - Unidade sem atendimento
            - Parada Pedagógica
        - Outro
    """

    def __str__(self):
        """Retorna a representação textual do motivo de suspensão.

        Returns:
            str: Nome do motivo de suspensão.
        """
        return self.nome

    class Meta:
        verbose_name = "Motivo de suspensão de alimentação"
        verbose_name_plural = "Motivo de suspensão de alimentação"


class SuspensaoAlimentacao(
    ExportModelOperationsMixin("suspensao_alimentacao"),
    TemData,
    TemChaveExterna,
    CanceladoIndividualmente,
):
    """Tabela auxiliar de uma Solicitação de Suspensão de Alimentação.

    Uma Solicitação de Suspensão de Alimentação pode ter N datas.

    Cada linha da tabela armazena um par data/motivo da solicitação.
    """

    prioritario = models.BooleanField(default=False)
    motivo = models.ForeignKey(MotivoSuspensao, on_delete=models.DO_NOTHING)
    outro_motivo = models.CharField("Outro motivo", blank=True, max_length=500)
    grupo_suspensao = models.ForeignKey(
        "GrupoSuspensaoAlimentacao",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="suspensoes_alimentacao",
    )

    def __str__(self):
        """Retorna a representação textual da suspensão de alimentação.

        Returns:
            str: Descrição do motivo associado a esta suspensão.
        """
        return f"{self.motivo}"

    class Meta:
        verbose_name = "Suspensão de alimentação"
        verbose_name_plural = "Suspensões de alimentação"


class QuantidadePorPeriodoSuspensaoAlimentacao(
    ExportModelOperationsMixin("quantidade_periodo"), TemChaveExterna
):
    """Tabela auxiliar de uma Solicitação de Suspensão de Alimentação.

    Uma Solicitação de Suspensão de Alimentação pode ter N períodos escolares.

    Cada linha da tabela armazena um período escolar da UE, a quantidade de alunos sem alimentação e os tipos de alimentação que estão suspensos.

    Normalmente, em uma solicitação são escolhidos todos os períodos escolares, todos os tipos de alimentação e todos os alunos matriculados, dado que, normalmente, é um dia sem aula na unidade inteira.

    O campo `CEI_OU_EMEI_CHOICES` é necessário apenas para solicitações de unidades educacionais com tipo de unidade escolar CEMEI/CEU CEMEI.
      - nele, armazenamos se a suspensão é destinada aos alunos CEI, EMEI ou ambos.
    """

    CEI_OU_EMEI_CHOICES = [
        ("TODOS", "Todos"),
        ("CEI", "CEI"),
        ("EMEI", "EMEI"),
    ]
    numero_alunos = models.SmallIntegerField()
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar", on_delete=models.DO_NOTHING
    )
    grupo_suspensao = models.ForeignKey(
        "GrupoSuspensaoAlimentacao",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="quantidades_por_periodo",
    )
    tipos_alimentacao = models.ManyToManyField(TipoAlimentacao)
    alunos_cei_ou_emei = models.CharField(
        max_length=10, choices=CEI_OU_EMEI_CHOICES, blank=True
    )

    def __str__(self):
        """Retorna a representação textual com a quantidade de alunos.

        Returns:
            str: Texto informando a quantidade de alunos sem alimentação.
        """
        return f"Quantidade de alunos: {self.numero_alunos}"

    class Meta:
        verbose_name = "Quantidade por período de suspensão de alimentação"
        verbose_name_plural = "Quantidade por período de suspensão de alimentação"


class GrupoSuspensaoAlimentacao(
    ExportModelOperationsMixin("grupo_suspensao_alimentacao"),
    TemChaveExterna,
    CriadoPor,
    TemIdentificadorExternoAmigavel,
    CriadoEm,
    TemObservacao,
    FluxoInformativoPartindoDaEscola,
    Logs,
    TemPrioridade,
    TemTerceirizadaConferiuGestaoAlimentacao,
):
    """Solicitação de Suspensão de Alimentação.

    **Objetivo**: informar à empresa que atende a unidade educacional que um dia previamente letivo não haverá aula por força maior.

    **Motivos mais comuns**:
      - Unidade sem atendimento
      - Parada Pedagógica
    """

    DESCRICAO = "Suspensão de Alimentação"
    escola = models.ForeignKey("escola.Escola", on_delete=models.DO_NOTHING)
    objects = models.Manager()  # Manager Padrão
    desta_semana = GrupoSuspensaoAlimentacaoDestaSemanaManager()
    deste_mes = GrupoSuspensaoAlimentacaoDesteMesManager()

    @classmethod
    def get_informados(cls):
        """Retorna as solicitações de suspensão com status INFORMADO.

        Returns:
            django.db.models.QuerySet: Queryset contendo as solicitações da
                classe com status de informado.
        """
        return cls.objects.filter(status=cls.workflow_class.INFORMADO)

    @classmethod
    def get_tomados_ciencia(cls):
        """Retorna as solicitações de suspensão com status TERCEIRIZADA_TOMOU_CIENCIA.

        Returns:
            django.db.models.QuerySet: Queryset contendo as solicitações da
                classe com status de terceirizada tomou ciência.
        """
        return cls.objects.filter(status=cls.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA)

    @classmethod
    def get_rascunhos_do_usuario(cls, usuario):
        """Retorna as solicitações de suspensão com status RASCUNHO de um usuário.

        Args:
            usuario (django.contrib.auth.models.AbstractUser): Usuário autor das
                solicitações.

        Returns:
            django.db.models.QuerySet: Queryset contendo as solicitações da
                classe com status de rascunho criadas pelo usuário informado.
        """
        return cls.objects.filter(
            criado_por=usuario, status=cls.workflow_class.RASCUNHO
        )

    @property  # type: ignore
    def quantidades_por_periodo(self):
        """Retorna as quantidades de alunos por período associadas à solicitação.

        Returns:
            django.db.models.QuerySet: Queryset com as quantidades por período
                da solicitação.
        """
        return self.quantidades_por_periodo

    @property  # type: ignore
    def suspensoes_alimentacao(self):
        """Retorna as datas de suspensão associadas à solicitação.

        Returns:
            django.db.models.QuerySet: Queryset com as datas de suspensão da
                solicitação.
        """
        return self.suspensoes_alimentacao

    @property
    def tipo(self):
        """Retorna a descrição textual do tipo da solicitação.

        Returns:
            str: String ``"Suspensão de Alimentação"``.
        """
        return "Suspensão de Alimentação"

    @property
    def path(self):
        """Retorna o caminho relativo do relatório desta solicitação no frontend.

        Returns:
            str: URL relativa do frontend para a tela de relatório da
                solicitação de suspensão.
        """
        return f"suspensao-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def data(self):
        """Retorna a primeira data da suspensão ordenada cronologicamente.

        Returns:
            datetime.date: Data da primeira suspensão.
        """
        query = self.suspensoes_alimentacao.order_by("data")
        return query.first().data

    @property
    def datas(self):
        """Retorna as datas de suspensão formatadas para exibição em relatórios.

        As datas são ordenadas cronologicamente e exibidas no formato
        ``dd/mm/YYYY``, separadas por vírgula.

        Returns:
            str: String com as datas formatadas e separadas por ``", "``.
        """
        return ", ".join(
            [
                data.strftime("%d/%m/%Y")
                for data in self.suspensoes_alimentacao.order_by("data").values_list(
                    "data", flat=True
                )
            ]
        )

    @property
    def numero_alunos(self):
        """Retorna o total de alunos sem alimentação na solicitação.

        Soma as quantidades de todos os períodos escolares associados.

        Returns:
            int: Número total de alunos sem alimentação.
        """
        return self.quantidades_por_periodo.aggregate(Sum("numero_alunos"))[
            "numero_alunos__sum"
        ]

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        """Monta o dicionário usado na geração do relatório da solicitação.

        Args:
            label_data (str): Rótulo textual da data exibida no relatório.
            data_log (datetime.date): Data do log de referência exibida no
                relatório.
            instituicao (object): Instituição solicitante. Mantido por
                compatibilidade de interface, sem uso direto no método.

        Returns:
            dict: Dicionário com os campos utilizados no relatório.
        """
        datas = list(
            self.suspensoes_alimentacao.order_by("data").values_list("data", flat=True)
        )
        datas = [d.strftime("%d/%m/%Y") for d in datas]
        datas = " ".join(datas)
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome_historico(self.data),
            "terceirizada": self.rastro_terceirizada,
            "tipo_doc": "Suspensão de Alimentação",
            "data_evento": datas,
            "numero_alunos": self.numero_alunos,
            "label_data": label_data,
            "data_log": data_log,
            "dias_motivos": self.suspensoes_alimentacao,
            "quantidades_periodo": self.quantidades_por_periodo,
            "datas": self.datas,
            "observacao": self.observacao,
            "id_externo": self.id_externo,
            "existe_dia_cancelado": self.existe_dia_cancelado,
        }

    @property
    def existe_dia_cancelado(self):
        """Verifica se a solicitação possui algum dia de suspensão cancelado.

        Returns:
            bool: ``True`` se houver ao menos uma suspensão cancelada,
                ``False`` caso contrário.
        """
        return self.suspensoes_alimentacao.all().filter(cancelado=True).exists()

    def __str__(self):
        """Retorna a representação textual resumida da solicitação.

        Returns:
            str: Texto da observação da solicitação.
        """
        return f"{self.observacao}"

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        """Registra no log a transição de status da solicitação.

        Cria uma entrada em ``LogSolicitacoesUsuario`` associada a esta
        solicitação de suspensão de alimentação.

        Args:
            status_evento (int): Código do evento de status que será registrado.
            usuario (django.contrib.auth.models.AbstractUser): Usuário
                responsável pela transição.
            **kwargs: Parâmetros opcionais do log.
                `justificativa` (str): Texto justificando a transição.

        Returns:
            None: O método apenas persiste o log da transição.
        """
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            justificativa=justificativa,
            solicitacao_tipo=LogSolicitacoesUsuario.SUSPENSAO_DE_CARDAPIO,
            usuario=usuario,
            uuid_original=self.uuid,
        )

    class Meta:
        verbose_name = "Grupo de suspensão de alimentação"
        verbose_name_plural = "Grupo de suspensão de alimentação"


patch_docs(GrupoSuspensaoAlimentacao)
