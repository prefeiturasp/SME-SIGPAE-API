from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinLengthValidator
from django.db import models
from multiselectfield import MultiSelectField

from src.dados_comuns.behaviors import Logs, TemIdentificadorExternoAmigavel
from src.dados_comuns.constants import MODEL_USUARIO, StringsVerboseNameModels
from src.dados_comuns.fluxo_status import (
    FluxoSolicitacaoDeAlteracao,
    FluxoSolicitacaoRemessa,
    GuiaRemessaWorkFlow,
    SolicitacaoRemessaWorkFlow,
)
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.terceirizada.models import Terceirizada

from ...dados_comuns.behaviors import ModeloBase


class SolicitacaoRemessaManager(models.Manager):
    def create_solicitacao(
        self, StrCnpj, StrNumSol, IntSeqenv, IntQtGuia, distribuidor=None
    ):
        return self.create(
            cnpj=StrCnpj,
            numero_solicitacao=StrNumSol,
            sequencia_envio=IntSeqenv,
            quantidade_total_guias=IntQtGuia,
            distribuidor=distribuidor,
        )


class SolicitacaoRemessa(
    ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoSolicitacaoRemessa
):
    ATIVA = "ATIVA"
    ARQUIVADA = "ARQUIVADA"

    SITUACAO_CHOICES = (
        (ATIVA, "Ativa"),
        (ARQUIVADA, "Arquivada"),
    )

    distribuidor = models.ForeignKey(
        Terceirizada,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="solicitacoes",
    )
    cnpj = models.CharField(
        StringsVerboseNameModels.CNPJ.value,
        validators=[MinLengthValidator(14)],
        max_length=14,
    )
    numero_solicitacao = models.CharField(
        StringsVerboseNameModels.NUMERO_DA_SOLICITACAO.value,
        blank=True,
        max_length=100,
        unique=True,
    )
    quantidade_total_guias = models.IntegerField(
        StringsVerboseNameModels.QTD_TOTAL_DE_GUIAS_NA_REQUISICAO.value, null=True
    )
    sequencia_envio = models.IntegerField(
        StringsVerboseNameModels.SEQUENCIA_DE_ENVIO_ATRIBUIDO_PELO_PAPA.value, null=True
    )
    situacao = models.CharField(choices=SITUACAO_CHOICES, max_length=10, default=ATIVA)

    objects = SolicitacaoRemessaManager()

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_REMESSA_PAPA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )
        return log_transicao

    @classmethod
    def arquivar_requisicao(cls, uuid):
        requisicao = SolicitacaoRemessa.objects.get(uuid=uuid)
        requisicao.situacao = SolicitacaoRemessa.ARQUIVADA
        requisicao.save()

    @classmethod
    def desarquivar_requisicao(cls, uuid):
        requisicao = SolicitacaoRemessa.objects.get(uuid=uuid)
        requisicao.situacao = SolicitacaoRemessa.ATIVA
        requisicao.save()

    @property
    def todas_as_guias_canceladas(self):
        total_guias = self.guias.count()
        total_guias_canceladas = self.guias.filter(
            status=GuiaRemessaWorkFlow.CANCELADA
        ).count()
        return total_guias == total_guias_canceladas

    @property
    def cancelada(self):
        return self.status == SolicitacaoRemessaWorkFlow.PAPA_CANCELA

    def __str__(self):
        return f"Solicitação: {self.numero_solicitacao} - Status: {self.get_status_display()}"

    class Meta:
        verbose_name = StringsVerboseNameModels.SOLICITACAO_REMESSA.value
        verbose_name_plural = StringsVerboseNameModels.SOLICITACOES_REMESSAS.value


class SolicitacaoDeAlteracaoRequisicao(
    ModeloBase, TemIdentificadorExternoAmigavel, FluxoSolicitacaoDeAlteracao
):
    # Motivo Choice
    MOTIVO_ALTERAR_DATA_ENTREGA = "ALTERAR_DATA_ENTREGA"
    MOTIVO_ALTERAR_QTD_ALIMENTO = "ALTERAR_QTD_ALIMENTO"
    MOTIVO_ALTERAR_ALIMENTO = "ALTERAR_ALIMENTO"
    MOTIVO_OUTROS = "OUTROS"

    MOTIVO_NOMES = {
        MOTIVO_ALTERAR_DATA_ENTREGA: "Alterar data de entrega",
        MOTIVO_ALTERAR_QTD_ALIMENTO: "Alterar quantidade de alimento",
        MOTIVO_ALTERAR_ALIMENTO: "Alterar alimento",
        MOTIVO_OUTROS: "Outros",
    }

    MOTIVO_CHOICES = (
        (MOTIVO_ALTERAR_DATA_ENTREGA, MOTIVO_NOMES[MOTIVO_ALTERAR_DATA_ENTREGA]),
        (MOTIVO_ALTERAR_QTD_ALIMENTO, MOTIVO_NOMES[MOTIVO_ALTERAR_QTD_ALIMENTO]),
        (MOTIVO_ALTERAR_ALIMENTO, MOTIVO_NOMES[MOTIVO_ALTERAR_ALIMENTO]),
        (MOTIVO_OUTROS, MOTIVO_NOMES[MOTIVO_OUTROS]),
    )

    requisicao = models.ForeignKey(
        SolicitacaoRemessa,
        on_delete=models.CASCADE,
        related_name="solicitacoes_de_alteracao",
    )
    motivo = MultiSelectField(choices=MOTIVO_CHOICES)
    justificativa = models.TextField(
        StringsVerboseNameModels.JUSTIFICATIVA_DE_SOLICITACAO_PELO_DISTRIBUIDOR.value,
        blank=True,
    )
    justificativa_aceite = models.TextField(
        StringsVerboseNameModels.JUSTIFICATIVA_DE_ACEITE_PELA_DILOG.value, blank=True
    )
    justificativa_negacao = models.TextField(
        StringsVerboseNameModels.JUSTIFICATIVA_DE_NEGACAO_PELA_DILOG.value, blank=True
    )
    usuario_solicitante = models.ForeignKey(MODEL_USUARIO, on_delete=models.DO_NOTHING)
    numero_solicitacao = models.CharField(
        StringsVerboseNameModels.NUMERO_DA_SOLICITACAO.value,
        blank=True,
        max_length=50,
        unique=True,
    )

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        resposta_sim_nao = kwargs.get("resposta_sim_nao", False)
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_DE_ALTERACAO_REQUISICAO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao,
        )
        return log_transicao

    def __str__(self):
        return f"Solicitação de alteração: {self.numero_solicitacao}"

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.SOLICITACAO_DE_ALTERACAO_DE_REQUISICAO.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.SOLICITACOES_DE_ALTERACAO_DE_REQUISICAO.value
        )


class SolicitacaoCancelamentoException(Exception):
    pass


class LogSolicitacaoDeCancelamentoPeloPapa(ModeloBase):
    requisicao = models.ForeignKey(
        SolicitacaoRemessa,
        on_delete=models.CASCADE,
        related_name="solicitacoes_de_cancelamento",
    )
    guias = ArrayField(models.CharField(max_length=100))
    sequencia_envio = models.IntegerField(
        StringsVerboseNameModels.SEQUENCIA_DE_ENVIO_ATRIBUIDA_PELO_PAPA.value
    )
    foi_confirmada = models.BooleanField(default=False)

    def __str__(self):
        return f"Sol. de cancelamento {self.sequencia_envio}"

    @classmethod
    def registrar_solicitacao(cls, requisicao, guias, sequencia_envio):
        if not requisicao or not guias or not sequencia_envio:
            raise SolicitacaoCancelamentoException(
                "É necessário informar a requisição, lista das guias e o número de "
                "sequencia do cancelamento."
            )

        solicitacao = cls.objects.create(
            requisicao=requisicao, guias=guias, sequencia_envio=sequencia_envio
        )
        return solicitacao

    def confirmar_cancelamento(self):
        self.foi_confirmada = True
        self.save()

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.LOG_DE_SOLICITACAO_DE_CANCELAMENTO_DO_PAPA.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.LOGS_DE_SOLICITACOES_DE_CANCELAMENTO_DO_PAPA.value
        )
