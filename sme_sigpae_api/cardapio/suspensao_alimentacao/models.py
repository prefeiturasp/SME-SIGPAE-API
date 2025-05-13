from django.db import models
from django.db.models import Sum
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.cardapio.managers import (
    GrupoSuspensaoAlimentacaoDestaSemanaManager,
    GrupoSuspensaoAlimentacaoDesteMesManager,
)
from sme_sigpae_api.dados_comuns.behaviors import (
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
from sme_sigpae_api.dados_comuns.fluxo_status import FluxoInformativoPartindoDaEscola
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario, TemplateMensagem


class MotivoSuspensao(
    ExportModelOperationsMixin("motivo_suspensao"), Nomeavel, TemChaveExterna
):
    """Trabalha em conjunto com SuspensaoAlimentacao.

    Exemplos:
        - greve
        - reforma
    """

    def __str__(self):
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
    """Trabalha em conjunto com GrupoSuspensaoAlimentacao."""

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
        return f"{self.motivo}"

    class Meta:
        verbose_name = "Suspensão de alimentação"
        verbose_name_plural = "Suspensões de alimentação"


class QuantidadePorPeriodoSuspensaoAlimentacao(
    ExportModelOperationsMixin("quantidade_periodo"), TemChaveExterna
):
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
    # TODO: SUBSTITUIR POR COMBOS DO TIPO DE ALIMENTACAO
    tipos_alimentacao = models.ManyToManyField(TipoAlimentacao)
    alunos_cei_ou_emei = models.CharField(
        max_length=10, choices=CEI_OU_EMEI_CHOICES, blank=True
    )

    def __str__(self):
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
    """Serve para agrupar suspensões.

    Vide SuspensaoAlimentacao e QuantidadePorPeriodoSuspensaoAlimentacao
    """

    DESCRICAO = "Suspensão de Alimentação"
    escola = models.ForeignKey("escola.Escola", on_delete=models.DO_NOTHING)
    objects = models.Manager()  # Manager Padrão
    desta_semana = GrupoSuspensaoAlimentacaoDestaSemanaManager()
    deste_mes = GrupoSuspensaoAlimentacaoDesteMesManager()

    @classmethod
    def get_informados(cls):
        return cls.objects.filter(status=cls.workflow_class.INFORMADO)

    @classmethod
    def get_tomados_ciencia(cls):
        return cls.objects.filter(status=cls.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA)

    @classmethod
    def get_rascunhos_do_usuario(cls, usuario):
        return cls.objects.filter(
            criado_por=usuario, status=cls.workflow_class.RASCUNHO
        )

    @property  # type: ignore
    def quantidades_por_periodo(self):
        return self.quantidades_por_periodo

    @property  # type: ignore
    def suspensoes_alimentacao(self):
        return self.suspensoes_alimentacao

    @property
    def tipo(self):
        return "Suspensão de Alimentação"

    @property
    def path(self):
        return f"suspensao-de-alimentacao/relatorio?uuid={self.uuid}&tipoSolicitacao=solicitacao-normal"

    @property
    def data(self):
        query = self.suspensoes_alimentacao.order_by("data")
        return query.first().data

    @property
    def datas(self):
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
        return self.quantidades_por_periodo.aggregate(Sum("numero_alunos"))[
            "numero_alunos__sum"
        ]

    def solicitacao_dict_para_relatorio(self, label_data, data_log, instituicao):
        datas = list(
            self.suspensoes_alimentacao.order_by("data").values_list("data", flat=True)
        )
        datas = [d.strftime("%d/%m/%Y") for d in datas]
        datas = " ".join(datas)
        return {
            "lote": f"{self.rastro_lote.diretoria_regional.iniciais} - {self.rastro_lote.nome}",
            "unidade_educacional": self.rastro_escola.nome,
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
        return self.suspensoes_alimentacao.all().filter(cancelado=True).exists()

    def __str__(self):
        return f"{self.observacao}"

    @property
    def template_mensagem(self):
        template = TemplateMensagem.objects.get(
            tipo=TemplateMensagem.SUSPENSAO_ALIMENTACAO
        )
        template_troca = {  # noqa
            "@id": self.id,
            "@criado_em": str(self.criado_em),
            "@criado_por": str(self.criado_por),
            "@status": str(self.status),
            # TODO: verificar a url padrão do pedido
            "@link": "http://teste.com",
        }
        corpo = template.template_html
        return template.assunto, corpo

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
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


class SuspensaoAlimentacaoNoPeriodoEscolar(
    ExportModelOperationsMixin("suspensao_periodo_escolar"), TemChaveExterna
):
    suspensao_alimentacao = models.ForeignKey(
        SuspensaoAlimentacao,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="suspensoes_periodo_escolar",
    )
    qtd_alunos = models.PositiveSmallIntegerField(default=0)
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        on_delete=models.PROTECT,
        related_name="suspensoes_periodo_escolar",
    )
    tipos_alimentacao = models.ManyToManyField(
        "TipoAlimentacao", related_name="suspensoes_periodo_escolar"
    )

    def __str__(self):
        return f"Suspensão de alimentação da Alteração de Cardápio: {self.suspensao_alimentacao}"

    class Meta:
        verbose_name = "Suspensão de alimentação no período"
        verbose_name_plural = "Suspensões de alimentação no período"
