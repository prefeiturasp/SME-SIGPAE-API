import datetime
import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinLengthValidator
from django.db import models

from .constants import LIMITE_INFERIOR, LIMITE_SUPERIOR, PRIORITARIO, REGULAR
from .models import LogSolicitacoesUsuario
from .utils import eh_dia_util, obter_dias_uteis_apos, ordena_dias_semana_comeca_domingo


class Iniciais(models.Model):
    iniciais = models.CharField('Iniciais', blank=True, max_length=10)

    class Meta:
        abstract = True


class Descritivel(models.Model):
    descricao = models.TextField('Descricao', blank=True)

    class Meta:
        abstract = True


class Nomeavel(models.Model):
    nome = models.CharField('Nome', blank=True, max_length=100)

    class Meta:
        abstract = True


class Motivo(models.Model):
    motivo = models.TextField('Motivo', blank=True)

    class Meta:
        abstract = True


class Justificativa(models.Model):
    justificativa = models.TextField('Motivo', blank=False)

    class Meta:
        abstract = True


class Ativavel(models.Model):
    ativo = models.BooleanField('Está ativo?', default=True)

    class Meta:
        abstract = True


class CriadoEm(models.Model):
    criado_em = models.DateTimeField('Criado em', editable=False, auto_now_add=True)

    class Meta:
        abstract = True


class TemAlteradoEm(models.Model):
    alterado_em = models.DateTimeField('Alterado em', editable=False, auto_now=True)

    class Meta:
        abstract = True


class IntervaloDeTempo(models.Model):
    data_hora_inicial = models.DateTimeField('Data/hora inicial')
    data_hora_final = models.DateTimeField('Data/hora final')

    class Meta:
        abstract = True


class IntervaloDeDia(models.Model):
    data_inicial = models.DateField('Data inicial')
    data_final = models.DateField('Data final')

    class Meta:
        abstract = True


class TemData(models.Model):
    data = models.DateField('Data')

    class Meta:
        abstract = True


class TemChaveExterna(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        abstract = True


class TemCodigoEOL(models.Model):
    codigo_eol = models.CharField('Código EOL', max_length=6, unique=True, validators=[MinLengthValidator(6)])

    class Meta:
        abstract = True


class DiasSemana(models.Model):
    SEGUNDA = 0
    TERCA = 1
    QUARTA = 2
    QUINTA = 3
    SEXTA = 4
    SABADO = 5
    DOMINGO = 6

    DIAS = (
        (SEGUNDA, 'Segunda'),
        (TERCA, 'Terça'),
        (QUARTA, 'Quarta'),
        (QUINTA, 'Quinta'),
        (SEXTA, 'Sexta'),
        (SABADO, 'Sábado'),
        (DOMINGO, 'Domingo'),
    )

    dias_semana = ArrayField(
        models.PositiveSmallIntegerField(choices=DIAS,
                                         default=[],
                                         null=True, blank=True
                                         )
    )

    def dias_semana_display(self):
        result = ''
        choices = dict(self.DIAS)
        for index, value in enumerate(ordena_dias_semana_comeca_domingo(self.dias_semana)):
            result += '{0}'.format(choices[value])
            if not index == len(self.dias_semana) - 1:
                result += ', '
        return result

    class Meta:
        abstract = True


class TempoPasseio(models.Model):
    QUATRO = 0
    CINCO_A_SETE = 1
    OITO_OU_MAIS = 2

    HORAS = (
        (QUATRO, 'Quatro horas'),
        (CINCO_A_SETE, 'Cinco a sete horas'),
        (OITO_OU_MAIS, 'Oito horas'),
    )
    tempo_passeio = models.PositiveSmallIntegerField(choices=HORAS,
                                                     null=True, blank=True)

    class Meta:
        abstract = True


class CriadoPor(models.Model):
    # TODO: futuramente deixar obrigatorio esse campo
    criado_por = models.ForeignKey('perfil.Usuario', on_delete=models.DO_NOTHING,
                                   null=True, blank=True)

    class Meta:
        abstract = True


class TemObservacao(models.Model):
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        abstract = True


class TemIdentificadorExternoAmigavel(object):
    """Gera uma chave externa amigável, não única.

    Somente para identificar externamente.
    Obrigatoriamente o objeto deve ter um uuid
    """

    @property
    def id_externo(self):
        uuid = str(self.uuid)
        return uuid.upper()[:5]


class TemPrioridade(object):
    """Exibe o tipo de prioridade do objeto de acordo com as datas que ele tem.

    Quando o objeto implementa o TemPrioridade, ele deve ter um property data
    """

    @property
    def data(self):
        raise NotImplementedError('Deve implementar um property @data')

    @property  # noqa
    def prioridade(self):
        descricao = 'VENCIDO'
        hoje = datetime.date.today()
        try:
            data_pedido = self.data_evento
        except AttributeError:
            data_pedido = self.data
        ultimo_dia_util = self._get_ultimo_dia_util(data_pedido)
        minimo_dias_para_pedido = obter_dias_uteis_apos(hoje, PRIORITARIO)
        dias_uteis_limite_inferior = obter_dias_uteis_apos(hoje, LIMITE_INFERIOR)
        dias_uteis_limite_superior = obter_dias_uteis_apos(hoje, LIMITE_SUPERIOR)
        dias_de_prazo_regular_em_diante = obter_dias_uteis_apos(hoje, REGULAR)

        if ultimo_dia_util and minimo_dias_para_pedido >= ultimo_dia_util >= hoje:
            descricao = 'PRIORITARIO'
        elif ultimo_dia_util and dias_uteis_limite_superior >= ultimo_dia_util >= dias_uteis_limite_inferior:
            descricao = 'LIMITE'
        elif ultimo_dia_util and ultimo_dia_util >= dias_de_prazo_regular_em_diante:
            descricao = 'REGULAR'
        return descricao

    def _get_ultimo_dia_util(self, data: datetime.date) -> datetime.date:
        """Assumindo que é sab, dom ou feriado volta para o dia util anterior."""
        data_retorno = data
        if data_retorno:
            while not eh_dia_util(data_retorno):
                data_retorno -= datetime.timedelta(days=1)
            if isinstance(data_retorno, datetime.datetime):
                return data_retorno.date()
        return data_retorno


class Logs(object):
    @property
    def logs(self):
        return LogSolicitacoesUsuario.objects.filter(uuid_original=self.uuid)

    @property
    def log_mais_recente(self):
        return self.logs.last()


class TemVinculos(models.Model):
    vinculos = GenericRelation('perfil.Vinculo')

    class Meta:
        abstract = True


class SolicitacaoForaDoPrazo(models.Model):
    foi_solicitado_fora_do_prazo = models.BooleanField(
        'Solicitação foi criada em cima da hora (5 dias úteis ou menos)?',
        default=False)

    class Meta:
        abstract = True


class TemFaixaEtariaEQuantidade(models.Model):
    faixa_etaria = models.ForeignKey('escola.FaixaEtaria', on_delete=models.DO_NOTHING)
    quantidade = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class ModeloBase(TemChaveExterna, CriadoEm, TemAlteradoEm):
    class Meta:
        abstract = True
