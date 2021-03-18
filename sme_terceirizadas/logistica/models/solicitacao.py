from django.core.validators import MinLengthValidator
from django.db import models
from multiselectfield import MultiSelectField

from sme_terceirizadas.dados_comuns.behaviors import Logs, TemIdentificadorExternoAmigavel
from sme_terceirizadas.dados_comuns.fluxo_status import FluxoSolicitacaoDeAlteracao, FluxoSolicitacaoRemessa
from sme_terceirizadas.dados_comuns.models import LogSolicitacoesUsuario
from sme_terceirizadas.terceirizada.models import Terceirizada

from ...dados_comuns.behaviors import ModeloBase


class SolicitacaoRemessaManager(models.Manager):

    def create_solicitacao(self, StrCnpj, StrNumSol, IntQtGuia, distribuidor=None):
        return self.create(
            cnpj=StrCnpj,
            numero_solicitacao=StrNumSol,
            quantidade_total_guias=IntQtGuia,
            distribuidor=distribuidor
        )


class SolicitacaoRemessa(ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoSolicitacaoRemessa):
    distribuidor = models.ForeignKey(
        Terceirizada, on_delete=models.CASCADE, blank=True, null=True, related_name='solicitacoes')
    cnpj = models.CharField('CNPJ', validators=[MinLengthValidator(14)], max_length=14)
    numero_solicitacao = models.CharField('Número da solicitação', blank=True, max_length=100, unique=True)
    quantidade_total_guias = models.IntegerField('Qtd total de guias na requisição', null=True)

    objects = SolicitacaoRemessaManager()

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get('justificativa', '')
        resposta_sim_nao = kwargs.get('resposta_sim_nao', False)
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_REMESSA_PAPA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao
        )
        return log_transicao

    def __str__(self):
        return f'Solicitação: {self.numero_solicitacao} - Status: {self.get_status_display()}'

    class Meta:
        verbose_name = 'Solicitação Remessa'
        verbose_name_plural = 'Solicitações Remessas'


class SolicitacaoDeAlteracaoRequisicao(ModeloBase, TemIdentificadorExternoAmigavel, FluxoSolicitacaoDeAlteracao):
    # Motivo Choice
    MOTIVO_ALTERAR_DATA_ENTREGA = 'ALTERAR_DATA_ENTREGA'
    MOTIVO_ALTERAR_QTD_ALIMENTO = 'ALTERAR_QTD_ALIMENTO'
    MOTIVO_ALTERAR_ALIMENTO = 'ALTERAR_ALIMENTO'
    MOTIVO_OUTROS = 'OUTROS'

    MOTIVO_NOMES = {
        MOTIVO_ALTERAR_DATA_ENTREGA: 'Alterar data de entrega',
        MOTIVO_ALTERAR_QTD_ALIMENTO: 'Alterar quantidade de alimento',
        MOTIVO_ALTERAR_ALIMENTO: 'Alterar alimento',
        MOTIVO_OUTROS: 'Outros',
    }

    MOTIVO_CHOICES = (
        (MOTIVO_ALTERAR_DATA_ENTREGA, MOTIVO_NOMES[MOTIVO_ALTERAR_DATA_ENTREGA]),
        (MOTIVO_ALTERAR_QTD_ALIMENTO, MOTIVO_NOMES[MOTIVO_ALTERAR_QTD_ALIMENTO]),
        (MOTIVO_ALTERAR_ALIMENTO, MOTIVO_NOMES[MOTIVO_ALTERAR_ALIMENTO]),
        (MOTIVO_OUTROS, MOTIVO_NOMES[MOTIVO_OUTROS]),
    )

    requisicao = models.ForeignKey(SolicitacaoRemessa, on_delete=models.CASCADE,
                                   related_name='solicitacoes_de_alteracao')
    motivo = MultiSelectField(choices=MOTIVO_CHOICES)
    justificativa = models.TextField('Justificativa de solicitação pelo distribuidor', blank=True)
    justificativa_aceite = models.TextField('Justificativa de aceite pela dilog', blank=True)
    justificativa_negacao = models.TextField('Justificativa de negacao pela dilog', blank=True)
    usuario_solicitante = models.ForeignKey('perfil.Usuario', on_delete=models.DO_NOTHING)
    numero_solicitacao = models.CharField('Número da solicitação', blank=True, max_length=50, unique=True)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get('justificativa', '')
        resposta_sim_nao = kwargs.get('resposta_sim_nao', False)
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_DE_ALTERACAO_REQUISICAO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
            resposta_sim_nao=resposta_sim_nao
        )
        return log_transicao

    def __str__(self):
        return f'Solicitação de alteração: {self.numero_solicitacao}'

    class Meta:
        verbose_name = 'Solicitação de Alteração de Requisição'
        verbose_name_plural = 'Solicitações de Alteração de Requisição'
