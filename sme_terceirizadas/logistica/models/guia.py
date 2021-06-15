from django.db import models
from multiselectfield import MultiSelectField

from ...dados_comuns.behaviors import CriadoPor, ModeloBase
from ...dados_comuns.fluxo_status import FluxoGuiaRemessa
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...escola.models import Escola
from .solicitacao import SolicitacaoRemessa


class GuiaManager(models.Manager):

    def create_guia(self, StrNumGui, DtEntrega, StrCodUni, StrNomUni,
                    StrEndUni, StrNumUni, StrBaiUni, StrCepUni,
                    StrCidUni, StrEstUni, StrConUni, StrTelUni,
                    solicitacao, escola):
        return self.create(
            numero_guia=StrNumGui,
            data_entrega=DtEntrega,
            codigo_unidade=StrCodUni,
            nome_unidade=StrNomUni,
            endereco_unidade=StrEndUni,
            numero_unidade=StrNumUni,
            bairro_unidade=StrBaiUni,
            cep_unidade=StrCepUni,
            cidade_unidade=StrCidUni,
            estado_unidade=StrEstUni,
            contato_unidade=StrConUni,
            telefone_unidade=StrTelUni,
            solicitacao=solicitacao,
            escola=escola
        )


class Guia(ModeloBase, FluxoGuiaRemessa):
    numero_guia = models.CharField('Número da guia', blank=True, max_length=100, unique=True)
    solicitacao = models.ForeignKey(
        SolicitacaoRemessa, on_delete=models.CASCADE, blank=True, null=True, related_name='guias')
    data_entrega = models.DateField('Data da entrega')
    codigo_unidade = models.CharField('Código da unidade', blank=True, max_length=10)
    nome_unidade = models.CharField('Nome da unidade', blank=True, max_length=150)
    escola = models.ForeignKey(Escola, on_delete=models.SET_NULL, blank=True, null=True)
    endereco_unidade = models.CharField('Endereço da unidade', blank=True, max_length=300)
    numero_unidade = models.CharField('Número da unidade', blank=True, max_length=10)
    bairro_unidade = models.CharField('Bairro da unidade', blank=True, max_length=100)
    cep_unidade = models.CharField('CEP da unidade', blank=True, max_length=20)
    cidade_unidade = models.CharField('Cidade da unidade', blank=True, max_length=100)
    estado_unidade = models.CharField('Estado da unidade', blank=True, max_length=2)
    contato_unidade = models.CharField('Contato na unidade', blank=True, max_length=150)
    telefone_unidade = models.CharField('Telefone da unidade', blank=True, default='', max_length=20)

    objects = GuiaManager()

    def as_dict(self):
        return dict((f.name, getattr(self, f.name)) for f in self._meta.fields)

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
        return f'Guia: {self.numero_guia} - {self.status} da solicitação: {self.solicitacao.numero_solicitacao}'

    class Meta:
        verbose_name = 'Guia de Remessa'
        verbose_name_plural = 'Guias de Remessas'


class ConferenciaGuia(ModeloBase, CriadoPor):
    guia = models.ForeignKey(
        Guia, on_delete=models.PROTECT, related_name='conferencias')
    data_recebimento = models.DateField('Data de recebimento')
    hora_recebimento = models.TimeField('Hora do recebimento')
    nome_motorista = models.CharField('Nome do motorista', max_length=100)
    placa_veiculo = models.CharField('Placa do veículo', max_length=7)
    eh_reposicao = models.BooleanField(default=False)

    def __str__(self):
        return f'Conferência da guia {self.guia.numero_guia}'

    class Meta:
        verbose_name = 'Conferência da Guia de Remessa'
        verbose_name_plural = 'Conferência das Guias de Remessas'


class ConferenciaIndividualPorAlimento(ModeloBase):
    # Status Alimento Choice
    STATUS_ALIMENTO_RECEBIDO = 'RECEBIDO'
    STATUS_ALIMENTO_PARCIAL = 'PARCIAL'
    STATUS_ALIMENTO_NAO_RECEBIDO = 'NAO_RECEBIDO'

    STATUS_ALIMENTO_NOMES = {
        STATUS_ALIMENTO_RECEBIDO: 'Recebido',
        STATUS_ALIMENTO_PARCIAL: 'Parcial',
        STATUS_ALIMENTO_NAO_RECEBIDO: 'Não recebido',
    }

    STATUS_ALIMENTO_CHOICES = (
        (STATUS_ALIMENTO_RECEBIDO, STATUS_ALIMENTO_NOMES[STATUS_ALIMENTO_RECEBIDO]),
        (STATUS_ALIMENTO_PARCIAL, STATUS_ALIMENTO_NOMES[STATUS_ALIMENTO_PARCIAL]),
        (STATUS_ALIMENTO_NAO_RECEBIDO, STATUS_ALIMENTO_NOMES[STATUS_ALIMENTO_NAO_RECEBIDO]),
    )

    # Tipo Embalagem Choice
    FECHADA = 'FECHADA'
    FRACIONADA = 'FRACIONADA'

    TIPO_EMBALAGEM_CHOICES = (
        (FECHADA, 'Fechada'),
        (FRACIONADA, 'Fracionada'),
    )

    # Status Ocorrencia Choice
    OCORRENCIA_QTD_MENOR = 'QTD_MENOR'
    OCORRENCIA_PROBLEMA_QUALIDADE = 'PROBLEMA_QUALIDADE'
    OCORRENCIA_ALIMENTO_DIFERENTE = 'ALIMENTO_DIFERENTE'
    OCORRENCIA_EMBALAGEM_DANIFICADA = 'EMBALAGEM_DANIFICADA'
    OCORRENCIA_EMBALAGEM_VIOLADA = 'EMBALAGEM_VIOLADA'
    OCORRENCIA_VALIDADE_EXPIRADA = 'VALIDADE_EXPIRADA'
    OCORRENCIA_ATRASO_ENTREGA = 'ATRASO_ENTREGA'
    OCORRENCIA_AUSENCIA_PRODUTO = 'AUSENCIA_PRODUTO'

    OCORRENCIA_NOMES = {
        OCORRENCIA_QTD_MENOR: 'Quantidade menor que a prevista',
        OCORRENCIA_PROBLEMA_QUALIDADE: 'Problema de qualidade do produto',
        OCORRENCIA_ALIMENTO_DIFERENTE: 'Alimento diferente do previsto',
        OCORRENCIA_EMBALAGEM_DANIFICADA: 'Embalagem danificada',
        OCORRENCIA_EMBALAGEM_VIOLADA: 'Embalagem violada',
        OCORRENCIA_VALIDADE_EXPIRADA: 'Prazo de validade expirado',
        OCORRENCIA_ATRASO_ENTREGA: 'Atraso na entrega',
        OCORRENCIA_AUSENCIA_PRODUTO: 'Ausência do produto',
    }

    OCORRENCIA_CHOICES = (
        (OCORRENCIA_QTD_MENOR, OCORRENCIA_NOMES[OCORRENCIA_QTD_MENOR]),
        (OCORRENCIA_PROBLEMA_QUALIDADE, OCORRENCIA_NOMES[OCORRENCIA_PROBLEMA_QUALIDADE]),
        (OCORRENCIA_ALIMENTO_DIFERENTE, OCORRENCIA_NOMES[OCORRENCIA_ALIMENTO_DIFERENTE]),
        (OCORRENCIA_EMBALAGEM_DANIFICADA, OCORRENCIA_NOMES[OCORRENCIA_EMBALAGEM_DANIFICADA]),
        (OCORRENCIA_EMBALAGEM_VIOLADA, OCORRENCIA_NOMES[OCORRENCIA_EMBALAGEM_VIOLADA]),
        (OCORRENCIA_VALIDADE_EXPIRADA, OCORRENCIA_NOMES[OCORRENCIA_VALIDADE_EXPIRADA]),
        (OCORRENCIA_ATRASO_ENTREGA, OCORRENCIA_NOMES[OCORRENCIA_ATRASO_ENTREGA]),
        (OCORRENCIA_AUSENCIA_PRODUTO, OCORRENCIA_NOMES[OCORRENCIA_AUSENCIA_PRODUTO]),
    )

    conferencia = models.ForeignKey(
        ConferenciaGuia, on_delete=models.PROTECT, related_name='conferencia_dos_alimentos')
    tipo_embalagem = models.CharField(choices=TIPO_EMBALAGEM_CHOICES, max_length=15, default=FECHADA)
    nome_alimento = models.CharField('Nome do alimento/produto', max_length=100)
    qtd_recebido = models.PositiveSmallIntegerField('Quantidade recebido')
    observacao = models.TextField('Observação', max_length=500, blank=True)
    status_alimento = models.CharField(choices=STATUS_ALIMENTO_CHOICES, max_length=40, default=STATUS_ALIMENTO_RECEBIDO)
    ocorrencia = MultiSelectField(choices=OCORRENCIA_CHOICES, blank=True)
    tem_ocorrencia = models.BooleanField(default=False)
    arquivo = models.FileField(blank=True)

    def __str__(self):
        return f'Conferencia do alimento {self.nome_alimento} da guia {self.conferencia.guia.numero_guia}'

    class Meta:
        verbose_name = 'Conferência Individual por Alimento'
        verbose_name_plural = 'Conferências Individuais por Alimentos'


class InsucessoEntregaGuia(ModeloBase, CriadoPor):
    # Motivo Choice
    MOTIVO_UNIDADE_FECHADA = 'UNIDADE_FECHADA'
    MOTIVO_OUTROS = 'OUTROS'

    MOTIVO_NOMES = {
        MOTIVO_UNIDADE_FECHADA: 'Unidade educacional fechada',
        MOTIVO_OUTROS: 'Outros',
    }

    MOTIVO_CHOICES = (
        (MOTIVO_UNIDADE_FECHADA, MOTIVO_NOMES[MOTIVO_UNIDADE_FECHADA]),
        (MOTIVO_OUTROS, MOTIVO_NOMES[MOTIVO_OUTROS]),
    )

    guia = models.ForeignKey(
        Guia, on_delete=models.PROTECT, related_name='insucessos')
    hora_tentativa = models.TimeField('Hora da tentativa de entrega')
    nome_motorista = models.CharField('Nome do motorista', max_length=100)
    placa_veiculo = models.CharField('Placa do veículo', max_length=7)
    justificativa = models.TextField('Justificativa', max_length=500)
    arquivo = models.FileField(blank=True)
    motivo = models.CharField(
        'Motivo do insucesso',
        max_length=25,
        choices=MOTIVO_CHOICES,
        default=MOTIVO_UNIDADE_FECHADA
    )

    def __str__(self):
        return f'Insucesso de entrega da guia {self.guia.numero_guia}'

    class Meta:
        verbose_name = 'Insucesso de Entrega da Guia'
        verbose_name_plural = 'Insucessos de Entregas das Guias'
