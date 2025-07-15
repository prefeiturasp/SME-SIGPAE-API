import datetime
import os
import uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.db.models.fields.files import FileField

from .constants import (
    LIMITE_INFERIOR,
    LIMITE_SUPERIOR,
    PRIORITARIO,
    StatusProcessamentoArquivo,
)
from .models import LogSolicitacoesUsuario
from .utils import eh_dia_util, obter_dias_uteis_apos, ordena_dias_semana_comeca_domingo


class Iniciais(models.Model):
    iniciais = models.CharField("Iniciais", blank=True, max_length=20)

    class Meta:
        abstract = True


class Descritivel(models.Model):
    descricao = models.TextField("Descricao", blank=True)

    class Meta:
        abstract = True


class Nomeavel(models.Model):
    nome = models.CharField("Nome", blank=True, max_length=100)

    class Meta:
        abstract = True


class TemNomeMaior(models.Model):
    nome = models.CharField("Nome", blank=True, max_length=250)

    class Meta:
        abstract = True


class Motivo(models.Model):
    motivo = models.TextField("Motivo", blank=True)

    class Meta:
        abstract = True


class Justificativa(models.Model):
    justificativa = models.TextField("Motivo", blank=False)

    class Meta:
        abstract = True


class Ativavel(models.Model):
    ativo = models.BooleanField("Está ativo?", default=True)

    class Meta:
        abstract = True


class ApenasAtivosManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=True)


class StatusAtivoInativo(models.Model):
    ATIVO = "Ativo"
    INATIVO = "Inativo"

    STATUS_CHOICES = (
        (True, ATIVO),
        (False, INATIVO),
    )
    status = models.BooleanField("Status", choices=STATUS_CHOICES, default=True)

    objects = models.Manager()
    ativos = ApenasAtivosManager()

    class Meta:
        abstract = True


class CriadoEm(models.Model):
    criado_em = models.DateTimeField("Criado em", editable=False, auto_now_add=True)

    class Meta:
        abstract = True


class TemAlteradoEm(models.Model):
    alterado_em = models.DateTimeField("Alterado em", editable=False, auto_now=True)

    class Meta:
        abstract = True


class IntervaloDeTempo(models.Model):
    data_hora_inicial = models.DateTimeField("Data/hora inicial")
    data_hora_final = models.DateTimeField("Data/hora final")

    class Meta:
        abstract = True


class IntervaloDeDia(models.Model):
    data_inicial = models.DateField("Data inicial")
    data_final = models.DateField("Data final")

    class Meta:
        abstract = True


class TemData(models.Model):
    data = models.DateField("Data")

    class Meta:
        abstract = True


class TemChaveExterna(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    @classmethod
    def by_uuid(cls, uuid):
        return cls.objects.get(uuid=uuid)

    class Meta:
        abstract = True


class TemCodigoEOL(models.Model):
    codigo_eol = models.CharField(
        "Código EOL", max_length=6, unique=True, validators=[MinLengthValidator(6)]
    )

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
        (SEGUNDA, "Segunda"),
        (TERCA, "Terça"),
        (QUARTA, "Quarta"),
        (QUINTA, "Quinta"),
        (SEXTA, "Sexta"),
        (SABADO, "Sábado"),
        (DOMINGO, "Domingo"),
    )

    dias_semana = ArrayField(
        models.PositiveSmallIntegerField(
            choices=DIAS, default=[], null=True, blank=True
        ),
        null=True,
        blank=True,
    )

    def dias_semana_display(self):
        result = ""
        choices = dict(self.DIAS)
        for index, value in enumerate(
            ordena_dias_semana_comeca_domingo(self.dias_semana)
        ):
            result += "{0}".format(choices[value])
            if not index == len(self.dias_semana) - 1:
                result += ", "
        return result

    class Meta:
        abstract = True


class TempoPasseio(models.Model):
    QUATRO = 0
    CINCO_A_SETE = 1
    OITO_OU_MAIS = 2

    HORAS = (
        (QUATRO, "Quatro horas"),
        (CINCO_A_SETE, "Cinco a sete horas"),
        (OITO_OU_MAIS, "Oito horas"),
    )
    tempo_passeio = models.PositiveSmallIntegerField(
        choices=HORAS, null=True, blank=True
    )

    class Meta:
        abstract = True


class CriadoPor(models.Model):
    # TODO: futuramente deixar obrigatorio esse campo
    criado_por = models.ForeignKey(
        "perfil.Usuario", on_delete=models.DO_NOTHING, null=True, blank=True
    )

    class Meta:
        abstract = True


class TemObservacao(models.Model):
    observacao = models.TextField("Observação", blank=True)

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

    def get_dias_suspensao_por_prioridade(self):
        from sme_sigpae_api.escola.models import DiaSuspensaoAtividades, Escola
        from sme_sigpae_api.kit_lanche.models import SolicitacaoKitLancheUnificada
        from sme_sigpae_api.paineis_consolidados.models import MoldeConsolidado

        dias_suspensao_prioritario = 0
        dias_suspensao_inferior = 0
        dias_suspensao_superior = 0

        escola = None
        if isinstance(self, MoldeConsolidado):
            escola = Escola.objects.get(uuid=self.escola_uuid)
        elif hasattr(self, "escola"):
            escola = self.escola

        if escola:
            dias_suspensao_prioritario = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                    escola, PRIORITARIO
                )
            )
            dias_suspensao_inferior = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                    escola, LIMITE_INFERIOR
                )
            )
            dias_suspensao_superior = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                    escola, LIMITE_SUPERIOR
                )
            )
        elif isinstance(self, SolicitacaoKitLancheUnificada):
            dias_suspensao_prioritario = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_solicitacao_unificada(
                    self.diretoria_regional, PRIORITARIO
                )
            )
            dias_suspensao_inferior = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_solicitacao_unificada(
                    self.diretoria_regional, LIMITE_INFERIOR
                )
            )
            dias_suspensao_superior = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_solicitacao_unificada(
                    self.diretoria_regional, LIMITE_SUPERIOR
                )
            )
        return (
            dias_suspensao_prioritario,
            dias_suspensao_inferior,
            dias_suspensao_superior,
        )

    @property
    def prioridade(self):
        descricao = "VENCIDO"
        hoje = datetime.date.today()
        try:
            data_pedido = self.data_evento
        except AttributeError:
            data_pedido = self.data
        ultimo_dia_util = self._get_ultimo_dia_util(data_pedido)
        (
            dias_suspensao_prioritario,
            dias_suspensao_inferior,
            dias_suspensao_superior,
        ) = self.get_dias_suspensao_por_prioridade()
        minimo_dias_para_pedido = obter_dias_uteis_apos(
            hoje, (PRIORITARIO + dias_suspensao_prioritario)
        )
        dias_uteis_limite_inferior = obter_dias_uteis_apos(
            hoje, (LIMITE_INFERIOR + dias_suspensao_inferior)
        )
        dias_uteis_limite_superior = obter_dias_uteis_apos(
            hoje, (LIMITE_SUPERIOR + dias_suspensao_superior)
        )

        if ultimo_dia_util and minimo_dias_para_pedido >= ultimo_dia_util >= hoje:
            descricao = "PRIORITARIO"
        elif (
            ultimo_dia_util
            and dias_uteis_limite_superior >= data_pedido >= dias_uteis_limite_inferior
        ):
            descricao = "LIMITE"
        elif ultimo_dia_util and ultimo_dia_util >= dias_uteis_limite_superior:
            descricao = "REGULAR"
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
        return LogSolicitacoesUsuario.objects.filter(uuid_original=self.uuid).order_by(
            "criado_em"
        )

    @property
    def log_mais_recente(self):
        return self.logs.last()

    @property
    def data_autorizacao(self):
        if LogSolicitacoesUsuario.objects.filter(
            uuid_original=self.uuid
        ).first().solicitacao_tipo in [
            LogSolicitacoesUsuario.SUSPENSAO_DE_CARDAPIO,
            LogSolicitacoesUsuario.SUSPENSAO_ALIMENTACAO_CEI,
        ]:
            return (
                self.logs.first().criado_em.strftime("%d/%m/%Y")
                if self.logs.exists()
                else ""
            )
        if LogSolicitacoesUsuario.objects.filter(
            uuid_original=self.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        ).exists():
            log = LogSolicitacoesUsuario.objects.filter(
                uuid_original=self.uuid,
                status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            )
            if log:
                return log.last().criado_em.strftime("%d/%m/%Y")
        return ""

    @property
    def data_cancelamento(self):
        if LogSolicitacoesUsuario.objects.filter(
            uuid_original=self.uuid,
            status_evento__in=[
                LogSolicitacoesUsuario.ESCOLA_CANCELOU,
                LogSolicitacoesUsuario.DRE_CANCELOU,
            ],
        ).exists():
            log = LogSolicitacoesUsuario.objects.filter(
                uuid_original=self.uuid,
                status_evento__in=[
                    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
                    LogSolicitacoesUsuario.DRE_CANCELOU,
                ],
            )
            if log:
                return log.last().criado_em.strftime("%d/%m/%Y")
        return ""

    @property
    def data_negacao(self):
        if LogSolicitacoesUsuario.objects.filter(
            uuid_original=self.uuid,
            status_evento__in=[
                LogSolicitacoesUsuario.CODAE_NEGOU,
                LogSolicitacoesUsuario.DRE_NAO_VALIDOU,
            ],
        ).exists():
            log = LogSolicitacoesUsuario.objects.filter(
                uuid_original=self.uuid,
                status_evento__in=[
                    LogSolicitacoesUsuario.CODAE_NEGOU,
                    LogSolicitacoesUsuario.DRE_NAO_VALIDOU,
                ],
            )
            if log:
                return log.last().criado_em.strftime("%d/%m/%Y")
        return ""


class TemVinculos(models.Model):
    vinculos = GenericRelation("perfil.Vinculo")

    class Meta:
        abstract = True


class SolicitacaoForaDoPrazo(models.Model):
    foi_solicitado_fora_do_prazo = models.BooleanField(
        "Solicitação foi criada em cima da hora (5 dias úteis ou menos)?", default=False
    )

    class Meta:
        abstract = True


class TemFaixaEtariaEQuantidade(models.Model):
    faixa_etaria = models.ForeignKey("escola.FaixaEtaria", on_delete=models.DO_NOTHING)
    quantidade = models.PositiveSmallIntegerField()

    class Meta:
        abstract = True


class ModeloBase(TemChaveExterna, CriadoEm, TemAlteradoEm):
    class Meta:
        abstract = True


class ArquivoCargaBase(ModeloBase):
    conteudo = models.FileField(blank=True, default="")
    status = models.CharField(
        "status",
        max_length=35,
        choices=StatusProcessamentoArquivo.choices(),
        default=StatusProcessamentoArquivo.PENDENTE.value,
    )
    log = models.TextField(blank=True, default="")

    def inicia_processamento(self):
        self.status = StatusProcessamentoArquivo.PROCESSANDO.value
        self.save()

    def processamento_com_sucesso(self):
        self.status = StatusProcessamentoArquivo.SUCESSO.value
        self.save()

    def processamento_com_erro(self):
        self.status = StatusProcessamentoArquivo.PROCESSADO_COM_ERRO.value
        self.save()

    def erro_no_processamento(self):
        self.status = StatusProcessamentoArquivo.ERRO.value
        self.save()

    def removido(self):
        if self.conteudo:
            self.conteudo.storage.delete(self.conteudo.name)
        self.status = StatusProcessamentoArquivo.REMOVIDO.value
        self.save()

    class Meta:
        abstract = True


class TemTerceirizadaConferiuGestaoAlimentacao(models.Model):
    """Indicação de que a terceirizada realizou avaliação da solicitação na gestão de alimentação."""

    terceirizada_conferiu_gestao = models.BooleanField(
        "Terceirizada conferiu?", default=False
    )

    class Meta:
        abstract = True


class TemAno(models.Model):
    ano = models.CharField("Ano", max_length=4)

    class Meta:
        abstract = True


class TemMes(models.Model):
    mes = models.CharField("Mes", max_length=2)

    class Meta:
        abstract = True


class TemDia(models.Model):
    dia = models.CharField("Dia", max_length=2)

    class Meta:
        abstract = True


class TemSemana(models.Model):
    semana = models.CharField("Semana", max_length=1, blank=True)

    class Meta:
        abstract = True


class MatriculadosQuandoCriado(models.Model):
    matriculados_quando_criado = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        abstract = True


class CanceladoIndividualmente(models.Model):
    cancelado = models.BooleanField("Esta cancelado?", default=False)
    cancelado_justificativa = models.CharField(
        "Porque foi cancelado individualmente", blank=True, max_length=1500
    )
    cancelado_em = models.DateTimeField("Cancelado em", null=True, blank=True)
    cancelado_por = models.ForeignKey(
        "perfil.Usuario", on_delete=models.DO_NOTHING, null=True, blank=True
    )

    class Meta:
        abstract = True


class Posicao(models.Model):
    posicao = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], blank=True, null=True
    )

    class Meta:
        abstract = True


class EhCopia(models.Model):
    eh_copia = models.BooleanField(default=False)

    class Meta:
        abstract = True


class AcessoModuloMedicaoInicial(models.Model):
    acesso_modulo_medicao_inicial = models.BooleanField(default=False)

    class Meta:
        abstract = True


class PerfilDiretorSupervisao(models.Model):
    DIRETOR = "DIRETOR"
    SUPERVISAO = "SUPERVISAO"

    PERFIS = (
        (DIRETOR, "DIRETOR"),
        (SUPERVISAO, "SUPERVISAO"),
    )

    perfis = ArrayField(
        models.CharField(choices=PERFIS, default=[], blank=True),
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class TemArquivosDeletaveis(models.Model):
    """Busca campos do tipo FileField e apaga os arquivos durante ao deletar a instância"""

    def delete(self, *args, **kwargs):
        file_fields = [
            field.name for field in self._meta.fields if isinstance(field, FileField)
        ]

        for field_name in file_fields:
            field = getattr(self, field_name)
            if os.path.isfile(field.path):
                os.remove(field.path)

        super().delete(*args, **kwargs)

    class Meta:
        abstract = True


class Grupo(models.Model):
    grupo = models.PositiveSmallIntegerField("Grupo de respostas", default=1)

    class Meta:
        abstract = True
