from __future__ import annotations

import datetime
import logging
import uuid
from collections import Counter
from copy import deepcopy
from datetime import date
from enum import Enum

import environ
import redis
import unidecode
from dateutil.relativedelta import relativedelta
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.validators import (
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.db import models, transaction
from django.db.models import F, Q, Sum
from django_prometheus.models import ExportModelOperationsMixin
from rest_framework import status

from ..cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ..cardapio.alteracao_tipo_alimentacao_cei.models import AlteracaoCardapioCEI
from ..cardapio.alteracao_tipo_alimentacao_cemei.models import AlteracaoCardapioCEMEI
from ..cardapio.base.models import TipoAlimentacao
from ..cardapio.inversao_dia_cardapio.models import InversaoCardapio
from ..cardapio.suspensao_alimentacao.models import GrupoSuspensaoAlimentacao
from ..dados_comuns.behaviors import (
    AcessoModuloMedicaoInicial,
    ArquivoCargaBase,
    Ativavel,
    CriadoEm,
    CriadoPor,
    Iniciais,
    Justificativa,
    Nomeavel,
    Posicao,
    TemAlteradoEm,
    TemChaveExterna,
    TemCodigoEOL,
    TemData,
    TemFaixaEtariaEQuantidade,
    TemObservacao,
    TemVinculos,
)
from ..dados_comuns.constants import (
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    DIRETOR_UE,
    obter_dias_uteis_apos_hoje,
)
from ..dados_comuns.fluxo_status import (
    FluxoAprovacaoPartindoDaEscola,
    FluxoDietaEspecialPartindoDaEscola,
    FluxoInformativoPartindoDaEscola,
    SolicitacaoMedicaoInicialWorkflow,
)
from ..dados_comuns.utils import (
    clonar_objeto,
    copiar_logs,
    cria_copias_fk,
    cria_copias_m2m,
    datetime_range,
    eh_fim_de_semana,
    get_ultimo_dia_mes,
    quantidade_meses,
    queryset_por_data,
    subtrai_meses_de_data,
)
from ..eol_servico.utils import EOLServicoSGP, dt_nascimento_from_api
from ..escola.constants import PERIODOS_ESPECIAIS_CEI_CEU_CCI
from ..inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from ..kit_lanche.models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEMEI,
    SolicitacaoKitLancheUnificada,
)
from .constants import CEI_OU_EMEI, PERIODOS_ESPECIAIS_CEMEI
from .services import NovoSGPServicoLogado
from .utils import deletar_alunos_periodo_parcial_outras_escolas, faixa_to_string

env = environ.Env()
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")
REDIS_DB = env("REDIS_DB")
REDIS_PREFIX = env("REDIS_PREFIX")

logger = logging.getLogger("sigpae.EscolaModels")
redis_conn = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    encoding="utf-8",
    decode_responses=True,
)


class DiretoriaRegional(
    ExportModelOperationsMixin("diretoria_regional"),
    Nomeavel,
    Iniciais,
    TemChaveExterna,
    TemCodigoEOL,
    TemVinculos,
    AcessoModuloMedicaoInicial,
):
    @property
    def editais(self):
        return [
            str(uuid_)
            for uuid_ in set(
                list(
                    set(
                        self.escolas.filter(
                            lote__isnull=False,
                            lote__contratos_do_lote__edital__isnull=False,
                            lote__contratos_do_lote__encerrado=False,
                        ).values_list(
                            "lote__contratos_do_lote__edital__uuid", flat=True
                        )
                    )
                )
            )
        ]

    @property
    def vinculos_que_podem_ser_finalizados(self):
        return self.vinculos.filter(
            Q(data_inicial=None, data_final=None, ativo=False)
            | Q(  # noqa W504 esperando ativacao
                data_inicial__isnull=False, data_final=None, ativo=True
            )  # noqa W504 ativo
        )

    @property
    def quantidade_alunos(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=self.escolas.all(), tipo_turma="REGULAR"
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    #
    # Inclusões continuas e normais
    #

    @property
    def inclusoes_continuas_autorizadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inclusoes_normais_autorizadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inclusoes_continuas_reprovadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            escola__in=self.escolas.all(),
            status=InclusaoAlimentacaoContinua.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
        )

    @property
    def inclusoes_normais_reprovadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            escola__in=self.escolas.all(),
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
        )

    def filtra_solicitacoes_minhas_escolas_a_validar_por_data(
        self, filtro_aplicado, model
    ):
        queryset = queryset_por_data(filtro_aplicado, model)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=SolicitacaoKitLancheAvulsa.workflow_class.DRE_A_VALIDAR,
        )

    def solicitacoes_kit_lanche_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, SolicitacaoKitLancheAvulsa
        )

    def solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, SolicitacaoKitLancheCEIAvulsa
        )

    def solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
        self, filtro_aplicado
    ):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, SolicitacaoKitLancheCEMEI
        )

    def alteracoes_cardapio_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, AlteracaoCardapio
        )

    def alteracoes_cardapio_cei_das_minhas_escolas_a_validar(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, AlteracaoCardapioCEI
        )

    def inclusoes_alimentacao_continua_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, InclusaoAlimentacaoContinua
        )

    def grupos_inclusoes_alimentacao_normal_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, GrupoInclusaoAlimentacaoNormal
        )

    def inclusoes_alimentacao_de_cei_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, InclusaoAlimentacaoDaCEI
        )

    def inclusoes_alimentacao_cemei_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, InclusaoDeAlimentacaoCEMEI
        )

    #
    # Alterações de cardápio
    #

    @property
    def alteracoes_cardapio_pendentes_das_minhas_escolas(self):
        return AlteracaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
        )

    @property
    def alteracoes_cardapio_autorizadas(self):
        return AlteracaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
                AlteracaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def solicitacao_kit_lanche_avulsa_autorizadas(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheAvulsa.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def solicitacao_kit_lanche_avulsa_reprovados(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            escola__in=self.escolas.all(),
            status=SolicitacaoKitLancheAvulsa.workflow_class.DRE_PEDIU_ESCOLA_REVISAR,
        )

    @property
    def alteracoes_cardapio_reprovadas(self):
        return AlteracaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapio.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
        )

    def alteracoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapio)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
        )

    def alteracoes_cardapio_cei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEI)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapioCEI.workflow_class.DRE_A_VALIDAR,
        )

    def alteracoes_cardapio_cemei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEMEI)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=AlteracaoCardapioCEMEI.workflow_class.DRE_A_VALIDAR,
        )

    #
    # Inversões de cardápio
    #

    def inversoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InversaoCardapio)
        return queryset.filter(
            escola__in=self.escolas.all(),
            status=InversaoCardapio.workflow_class.DRE_A_VALIDAR,
        )

    @property
    def inversoes_cardapio_autorizadas(self):
        return InversaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[
                InversaoCardapio.workflow_class.DRE_VALIDADO,
                InversaoCardapio.workflow_class.CODAE_AUTORIZADO,
                InversaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inversoes_cardapio_reprovados(self):
        return InversaoCardapio.objects.filter(
            escola__in=self.escolas.all(),
            status__in=[InversaoCardapio.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA],
        )

    @property
    def possui_escolas_com_acesso_ao_medicao_inicial(self):
        return (
            self.acesso_modulo_medicao_inicial
            or self.escolas.filter(acesso_modulo_medicao_inicial=True).exists()
        )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Diretoria regional"
        verbose_name_plural = "Diretorias regionais"
        ordering = ("nome",)


class FaixaIdadeEscolar(
    ExportModelOperationsMixin("faixa_idade"), Nomeavel, Ativavel, TemChaveExterna
):
    """de 1 a 2 anos, de 2 a 5 anos, de 7 a 18 anos, etc."""

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Idade escolar"
        verbose_name_plural = "Idades escolares"
        ordering = ("nome",)


class TipoUnidadeEscolar(
    ExportModelOperationsMixin("tipo_ue"), Iniciais, Ativavel, TemChaveExterna
):
    """EMEF, CIEJA, EMEI, EMEBS, CEI, CEMEI..."""

    cardapios = models.ManyToManyField(
        "cardapio.Cardapio", blank=True, related_name="tipos_unidade_escolar"
    )
    periodos_escolares = models.ManyToManyField(
        "escola.PeriodoEscolar", blank=True, related_name="tipos_unidade_escolar"
    )
    tem_somente_integral_e_parcial = models.BooleanField(
        help_text="Variável de controle para setar os períodos escolares na mão, válido para CEI CEU, CEI e CCI",
        default=False,
    )
    pertence_relatorio_solicitacoes_alimentacao = models.BooleanField(
        help_text="Variável de controle para determinar quais tipos de unidade escolar são exibidos no relatório de "
        "solicitações de alimentação",
        default=True,
    )

    @property
    def eh_cei(self):
        lista_tipos_unidades = [
            "CEI DIRET",
            "CEU CEI",
            "CEI",
            "CCI",
            "CCI/CIPS",
            "CEI CEU",
        ]
        return self.iniciais in lista_tipos_unidades

    def get_cardapio(self, data):
        # TODO: ter certeza que tem so um cardapio por dia por tipo de u.e.
        try:
            return self.cardapios.get(data=data)
        except ObjectDoesNotExist:
            return None

    def __str__(self):
        return self.iniciais

    class Meta:
        verbose_name = "Tipo de unidade escolar"
        verbose_name_plural = "Tipos de unidade escolar"
        ordering = ("iniciais",)


class TipoGestao(
    ExportModelOperationsMixin("tipo_gestao"), Nomeavel, Ativavel, TemChaveExterna
):
    """Terceirizada completa, tec mista."""

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de gestão"
        verbose_name_plural = "Tipos de gestão"


class PeriodoEscolar(
    ExportModelOperationsMixin("periodo_escolar"), Nomeavel, TemChaveExterna, Posicao
):
    """manhã, intermediário, tarde, vespertino, noturno, integral."""

    tipos_alimentacao = models.ManyToManyField(
        "cardapio.TipoAlimentacao", related_name="periodos_escolares"
    )
    tipo_turno = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], blank=True, null=True
    )

    @staticmethod
    def dict_periodos():
        return {
            "MANHA": PeriodoEscolar.objects.get_or_create(nome="MANHA")[0],
            "TARDE": PeriodoEscolar.objects.get_or_create(nome="TARDE")[0],
            "INTEGRAL": PeriodoEscolar.objects.get_or_create(nome="INTEGRAL")[0],
            "NOITE": PeriodoEscolar.objects.get_or_create(nome="NOITE")[0],
            "INTERMEDIARIO": PeriodoEscolar.objects.get_or_create(nome="INTERMEDIARIO")[
                0
            ],
            "VESPERTINO": PeriodoEscolar.objects.get_or_create(nome="VESPERTINO")[0],
            "PARCIAL": PeriodoEscolar.objects.get_or_create(nome="PARCIAL")[0],
            None: None,
        }

    class Meta:
        ordering = ("posicao",)
        verbose_name = "Período escolar"
        verbose_name_plural = "Períodos escolares"

    def __str__(self):
        return self.nome


class Escola(
    ExportModelOperationsMixin("escola"),
    Ativavel,
    TemChaveExterna,
    TemCodigoEOL,
    TemVinculos,
    AcessoModuloMedicaoInicial,
):
    acesso_desde = models.DateField(
        "Acesso módulo medição desde", null=True, blank=True
    )
    nome = models.CharField("Nome", max_length=160, blank=True)
    codigo_eol = models.CharField(
        "Código EOL", max_length=6, unique=True, validators=[MinLengthValidator(6)]
    )
    codigo_codae = models.CharField(  # noqa: DJ01
        "Código CODAE",
        max_length=10,
        blank=True,
        null=True,
        default=None,
    )
    diretoria_regional = models.ForeignKey(
        DiretoriaRegional, related_name="escolas", on_delete=models.DO_NOTHING
    )
    tipo_unidade = models.ForeignKey(TipoUnidadeEscolar, on_delete=models.DO_NOTHING)
    tipo_gestao = models.ForeignKey(
        TipoGestao, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    lote = models.ForeignKey(
        "Lote", related_name="escolas", blank=True, null=True, on_delete=models.PROTECT
    )
    subprefeitura = models.ForeignKey(
        "Subprefeitura",
        related_name="escolas",
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT,
    )
    contato = models.ForeignKey(
        "dados_comuns.Contato",
        on_delete=models.SET_DEFAULT,
        blank=True,
        null=True,
        default=None,
    )
    idades = models.ManyToManyField(FaixaIdadeEscolar, blank=True)
    tipos_contagem = models.ManyToManyField("dieta_especial.TipoContagem", blank=True)
    endereco = models.ForeignKey(
        "dados_comuns.Endereco", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    enviar_email_por_produto = models.BooleanField(
        default=False,
        help_text="Envia e-mail quando houver um produto com status de homologado, não homologado, ativar ou suspender.",  # noqa
    )

    @property
    def tipos_alimentacao(self):
        return TipoAlimentacao.objects.filter(
            uuid__in=self.tipo_unidade.vinculotipoalimentacaocomperiodoescolaretipounidadeescolar_set.values_list(
                "tipos_alimentacao__uuid", flat=True
            )
            .exclude(tipos_alimentacao__nome__isnull=True)
            .distinct()
        )

    @property
    def eh_parceira(self):
        return self.tipo_gestao and self.tipo_gestao.nome == "PARCEIRA"

    @property
    def quantidade_alunos(self):
        quantidade = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola=self, tipo_turma="REGULAR"
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade.get("quantidade_alunos__sum") or 0

    @property
    def quantidade_alunos_cei_da_cemei(self):
        if not self.eh_cemei:
            return None
        return self.aluno_set.filter(ciclo=Aluno.CICLO_ALUNO_CEI).count()

    def quantidade_alunos_cei_por_periodo(self, periodo):
        if not self.eh_cemei:
            return None
        return self.aluno_set.filter(
            periodo_escolar__nome=periodo, ciclo=Aluno.CICLO_ALUNO_CEI
        ).count()

    def quantidade_alunos_cei_por_periodo_por_faixa(self, periodo, faixa):
        if not self.eh_cemei:
            return None
        data_inicio = datetime.date.today() - relativedelta(months=faixa.inicio)
        data_fim = datetime.date.today() - relativedelta(months=faixa.fim)
        return self.aluno_set.filter(
            periodo_escolar__nome=periodo,
            data_nascimento__lte=data_inicio,
            data_nascimento__gte=data_fim,
            ciclo=Aluno.CICLO_ALUNO_CEI,
        ).count()

    @property
    def quantidade_alunos_emebs_infantil(self):
        if not self.eh_emebs:
            return None
        return self.aluno_set.filter(etapa=Aluno.ETAPA_INFANTIL).count()

    def quantidade_alunos_emebs_por_periodo_infantil(self, nome_periodo_escolar):
        if not self.eh_emebs:
            return None
        return self.aluno_set.filter(
            periodo_escolar__nome=nome_periodo_escolar, etapa=Aluno.ETAPA_INFANTIL
        ).count()

    def quantidade_alunos_emebs_por_periodo_fundamental(self, nome_periodo_escolar):
        if not self.eh_emebs:
            return None
        return (
            self.aluno_set.filter(
                periodo_escolar__nome=nome_periodo_escolar,
            )
            .exclude(etapa=Aluno.ETAPA_INFANTIL)
            .count()
        )

    def quantidade_alunos_emei_por_periodo(self, periodo):
        if not self.eh_cemei:
            return None
        return self.aluno_set.filter(
            periodo_escolar__nome=periodo, ciclo=Aluno.CICLO_ALUNO_EMEI
        ).count()

    def quantidade_alunos_matriculados_por_data(
        self, data, cei_ou_emei="N/A", infantil_ou_fundamental="N/A"
    ):
        today = datetime.date.today()
        if data.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d"):
            data = today - datetime.timedelta(days=1)

        logs = self.logs_alunos_matriculados_por_periodo.filter(
            criado_em=data,
            cei_ou_emei=cei_ou_emei,
            infantil_ou_fundamental=infantil_ou_fundamental,
        ).aggregate(soma=Sum("quantidade_alunos"))

        soma_quantidade_alunos = logs["soma"] or 0
        return soma_quantidade_alunos

    @property
    def quantidade_alunos_emei_da_cemei(self):
        if not self.eh_cemei:
            return None
        return self.aluno_set.filter(ciclo=Aluno.CICLO_ALUNO_EMEI).count()

    @property
    def alunos_por_periodo_escolar(self):
        return self.escolas_periodos.filter(quantidade_alunos__gte=1)

    @property
    def editais(self):
        if self.lote:
            return list(
                set(
                    [
                        str(edital)
                        for edital in self.lote.contratos_do_lote.filter(
                            edital__isnull=False, encerrado=False
                        ).values_list("edital__uuid", flat=True)
                    ]
                )
            )
        return []

    @property
    def edital(self):
        if self.lote:
            for edital in self.lote.contratos_do_lote.filter(edital__isnull=False):
                return edital
        return None

    @property
    def possui_alunos_regulares(self):
        return AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__uuid=self.uuid, tipo_turma="REGULAR", quantidade_alunos__gte=1
        ).exists()

    def periodos_escolares(self, ano=datetime.date.today().year):
        """Recupera periodos escolares da escola, desde que haja pelomenos um aluno para este período."""

        if self.tipo_unidade.tem_somente_integral_e_parcial:
            periodos = PeriodoEscolar.objects.filter(
                nome__in=PERIODOS_ESPECIAIS_CEI_CEU_CCI
            )
        elif not self.possui_alunos_regulares:
            periodos = PeriodoEscolar.objects.filter(
                vinculotipoalimentacaocomperiodoescolaretipounidadeescolar__tipo_unidade_escolar=self.tipo_unidade,
                vinculotipoalimentacaocomperiodoescolaretipounidadeescolar__ativo=True,
            )
        else:
            periodos = PeriodoEscolar.objects.filter(
                id__in=self.logs_alunos_matriculados_por_periodo.filter(
                    tipo_turma="REGULAR",
                    quantidade_alunos__gte=1,
                    criado_em__year=ano,
                )
                .values_list("periodo_escolar", flat=True)
                .distinct()
            )
        return periodos

    @property
    def vinculos_que_podem_ser_finalizados(self):
        return self.vinculos.filter(
            Q(data_inicial=None, data_final=None, ativo=False)
            | Q(  # noqa W504 esperando ativacao
                data_inicial__isnull=False, data_final=None, ativo=True
            )  # noqa W504 ativo
        ).exclude(perfil__nome=DIRETOR_UE)

    @property
    def eh_cei(self):
        lista_tipos_unidades = [
            "CEI DIRET",
            "CEU CEI",
            "CEI",
            "CCI",
            "CCI/CIPS",
            "CEI CEU",
        ]
        return self.tipo_unidade and self.tipo_unidade.iniciais in lista_tipos_unidades

    @property
    def eh_cemei(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            "CEU CEMEI",
            "CEMEI",
        ]

    @property
    def eh_emei(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in ["CEU EMEI", "EMEI"]

    @property
    def eh_emebs(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in ["EMEBS"]

    @property
    def eh_ceu_gestao(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in ["CEU GESTAO"]

    @property
    def eh_emef_emei_cieja(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            "EMEI",
            "EMEF",
            "EMEFM",
            "CEU EMEF",
            "CEU EMEI",
            "CIEJA",
        ]

    @property
    def eh_emef(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            "EMEF",
            "CEU EMEF",
            "EMEFM",
        ]

    @property
    def eh_cieja(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in ["CIEJA"]

    @property
    def eh_cmct(self):
        return self.tipo_unidade and self.tipo_unidade.iniciais in ["CMCT"]

    @property
    def modulo_gestao(self):
        if self.tipo_gestao and self.tipo_gestao.nome == "TERC TOTAL":
            return "TERCEIRIZADA"
        return "ABASTECIMENTO"

    @property
    def periodos_escolares_com_alunos(self):
        return list(
            self.aluno_set.filter(periodo_escolar__isnull=False)
            .values_list("periodo_escolar__nome", flat=True)
            .distinct()
        )

    def quantidade_alunos_por_cei_emei(self, manha_e_tarde_sempre=False):  # noqa C901
        if not self.eh_cemei:
            return None
        return_dict = {}
        alunos_por_periodo_e_faixa_etaria = (
            self.alunos_por_periodo_e_faixa_etaria_objetos_alunos()
        )
        dict_normalizado = {
            unidecode.unidecode(faixa): dict(quantidade_alunos.items())
            for faixa, quantidade_alunos in alunos_por_periodo_e_faixa_etaria.items()
        }

        lista_faixas = {}
        for periodo, dict_faixas in dict_normalizado.items():
            lista_faixas[periodo] = []
            for uuid_, quantidade_alunos in dict_faixas.items():
                lista_faixas[periodo].append(
                    {
                        "uuid": uuid_,
                        "faixa": FaixaEtaria.objects.get(uuid=uuid_).__str__(),
                        "quantidade_alunos": quantidade_alunos,
                        "inicio": FaixaEtaria.objects.get(uuid=uuid_).inicio,
                    }
                )
            lista_faixas[periodo] = sorted(
                lista_faixas[periodo], key=lambda x: x["inicio"]
            )
        periodos = self.periodos_escolares_com_alunos
        if manha_e_tarde_sempre:
            periodos = list(
                PeriodoEscolar.objects.filter(
                    nome__in=PERIODOS_ESPECIAIS_CEMEI
                ).values_list("nome", flat=True)
            )
        for periodo in periodos:
            return_dict[periodo] = {}
            try:
                return_dict[periodo]["CEI"] = lista_faixas[periodo]
            except KeyError:
                return_dict[periodo]["CEI"] = lista_faixas["INTEGRAL"]
            return_dict[periodo]["EMEI"] = self.quantidade_alunos_emei_por_periodo(
                periodo
            )

        return_array = []
        indice = 0
        for periodo, cei_emei in return_dict.items():
            return_array.append({"nome": periodo})
            for key, value in cei_emei.items():
                return_array[indice][key] = value
            indice += 1

        return return_array

    @property
    def quantidade_alunos_por_periodo_cei_emei(self):
        if not self.eh_cemei:
            return None
        return_dict = {}

        for periodo in self.periodos_escolares_com_alunos:
            return_dict[periodo] = {}
            return_dict[periodo]["CEI"] = self.quantidade_alunos_cei_por_periodo(
                periodo
            )
            return_dict[periodo]["EMEI"] = self.quantidade_alunos_emei_por_periodo(
                periodo
            )

        return_array = []
        indice = 0
        for periodo, cei_emei in return_dict.items():
            return_array.append({"nome": periodo})
            for key, value in cei_emei.items():
                return_array[indice][key] = value
            indice += 1

        return return_array

    @property
    def grupos_inclusoes(self):
        return self.grupos_inclusoes_normais

    def get_cardapio(self, data):
        return self.tipo_unidade.get_cardapio(data)

    @property
    def inclusoes_continuas(self):
        return self.inclusoes_alimentacao_continua

    def __str__(self):
        return f"{self.codigo_eol}: {self.nome}"

    def matriculados_por_periodo_e_faixa_etaria(self):
        periodos = self.periodos_escolares().values_list("nome", flat=True)
        matriculados_por_faixa = {}
        if self.eh_cei or self.eh_cemei:
            for periodo in periodos:
                faixas = redis_conn.hgetall(f"{REDIS_PREFIX}-{self.uuid}-{periodo}")
                faixas = Counter({f"{key}": int(faixas[key]) for key in faixas})
                matriculados_por_faixa[periodo] = faixas
        return matriculados_por_faixa

    def obter_data_referencia(self, data_referencia=None):
        return data_referencia if data_referencia else date.today()

    def obter_faixas_etarias(self, faixas_etarias=None):
        if not faixas_etarias:
            faixas_etarias = FaixaEtaria.objects.filter(ativo=True)
        if faixas_etarias.count() == 0:
            raise ObjectDoesNotExist()
        return faixas_etarias

    def contar_alunos_por_faixa(
        self, aluno_data_nascimento, data_referencia, faixas_etarias, seis_anos_atras
    ):
        count = Counter()
        for faixa_etaria in faixas_etarias:
            if faixa_etaria.data_pertence_a_faixa(
                aluno_data_nascimento, data_referencia
            ):
                count[str(faixa_etaria.uuid)] += 1
            elif aluno_data_nascimento < seis_anos_atras and faixa_etaria.fim == 73:
                count[str(faixa_etaria.uuid)] += 1
        return count

    def alunos_por_periodo_e_faixa_etaria(
        self, data_referencia=None, faixas_etarias=None
    ):
        data_referencia = self.obter_data_referencia(data_referencia)
        faixas_etarias = self.obter_faixas_etarias(faixas_etarias)

        lista_alunos = (
            EOLServicoSGP.get_lista_alunos_por_escola_ano_corrente_ou_seguinte(
                self.codigo_eol
            )
        )

        seis_anos_atras = datetime.date.today() - relativedelta(years=6)
        dict_periodos = dict(PeriodoEscolar.objects.values_list("tipo_turno", "nome"))

        resultados = {}
        for aluno in lista_alunos:
            tipo_turno = aluno.get("tipoTurno")
            nome_periodo = dict_periodos[tipo_turno]
            data_nascimento = dt_nascimento_from_api(aluno["dataNascimento"])
            if nome_periodo not in resultados:
                resultados[nome_periodo] = Counter()
            resultados[nome_periodo] += self.contar_alunos_por_faixa(
                data_nascimento, data_referencia, faixas_etarias, seis_anos_atras
            )
        return resultados

    def alunos_periodo_parcial_e_faixa_etaria(
        self, data_referencia=None, faixas_etarias=None
    ):
        if not self.eh_cei and not self.eh_cemei:
            return {}

        data_referencia = self.obter_data_referencia(data_referencia)
        faixas_etarias = self.obter_faixas_etarias(faixas_etarias)
        deletar_alunos_periodo_parcial_outras_escolas(self, data_referencia)
        alunos_periodo_parcial = AlunoPeriodoParcial.objects.filter(
            aluno__escola__codigo_eol=self.codigo_eol,
            solicitacao_medicao_inicial__mes=str(data_referencia.month).zfill(2),
            solicitacao_medicao_inicial__ano=str(data_referencia.year),
        ).values_list("aluno__codigo_eol", flat=True)

        lista_alunos = (
            EOLServicoSGP.get_lista_alunos_por_escola_ano_corrente_ou_seguinte(
                self.codigo_eol
            )
        )

        alunos_periodo_parcial_set = set(alunos_periodo_parcial)
        seis_anos_atras = datetime.date.today() - relativedelta(years=6)

        resultados = {}
        for aluno in lista_alunos:
            if str(aluno["codigoAluno"]) not in alunos_periodo_parcial_set:
                continue
            periodo = "PARCIAL"
            data_nascimento = dt_nascimento_from_api(aluno["dataNascimento"])
            if periodo not in resultados:
                resultados[periodo] = Counter()
            resultados[periodo] += self.contar_alunos_por_faixa(
                data_nascimento, data_referencia, faixas_etarias, seis_anos_atras
            )
        return resultados

    def alunos_por_periodo_e_faixa_etaria_objetos_alunos(
        self, data_referencia=None, faixas_etarias=None
    ):
        data_referencia = self.obter_data_referencia(data_referencia)
        faixas_etarias = self.obter_faixas_etarias(faixas_etarias)

        lista_alunos = Aluno.objects.filter(
            escola__codigo_eol=self.codigo_eol, ciclo=Aluno.CICLO_ALUNO_CEI
        )
        seis_anos_atras = datetime.date.today() - relativedelta(years=6)
        resultados = {}
        for aluno in lista_alunos:
            periodo = aluno.periodo_escolar.nome
            data_nascimento = aluno.data_nascimento
            if periodo not in resultados:
                resultados[periodo] = Counter()
            resultados[periodo] += self.contar_alunos_por_faixa(
                data_nascimento, data_referencia, faixas_etarias, seis_anos_atras
            )
        return resultados

    def alunos_por_faixa_etaria(self, data_referencia=None, faixas_etarias=None):
        data_referencia = self.obter_data_referencia(data_referencia)
        faixas_etarias = self.obter_faixas_etarias(faixas_etarias)

        lista_alunos = (
            EOLServicoSGP.get_lista_alunos_por_escola_ano_corrente_ou_seguinte(
                self.codigo_eol
            )
        )

        seis_anos_atras = datetime.date.today() - relativedelta(years=6)

        resultados = Counter()
        for aluno in lista_alunos:
            data_nascimento = dt_nascimento_from_api(aluno["dataNascimento"])
            resultados += self.contar_alunos_por_faixa(
                data_nascimento, data_referencia, faixas_etarias, seis_anos_atras
            )
        return resultados

    def get_lista_medicoes_kit_lanche_avulso_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if (
            "Solicitações de Alimentação" in lista_medicoes
            or self.eh_cei
            or self.eh_cemei
        ):
            return lista_medicoes
        if self.solicitacoes_kit_lanche_avulsa.filter(
            status="CODAE_AUTORIZADO",
            solicitacao_kit_lanche__data__month=mes,
            solicitacao_kit_lanche__data__year=ano,
        ).exists():
            lista_medicoes.append("Solicitações de Alimentação")
        return lista_medicoes

    def get_lista_medicoes_kit_lanche_unificado_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if "Solicitações de Alimentação" in lista_medicoes:
            return lista_medicoes
        if self.escolaquantidade_set.filter(
            solicitacao_unificada__status="CODAE_AUTORIZADO",
            cancelado=False,
            solicitacao_unificada__solicitacao_kit_lanche__data__month=mes,
            solicitacao_unificada__solicitacao_kit_lanche__data__year=ano,
        ).exists():
            lista_medicoes.append("Solicitações de Alimentação")
        return lista_medicoes

    def get_lista_medicoes_kit_lanche_cei_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes
    ) -> list:
        if "Solicitações de Alimentação" in lista_medicoes or not self.eh_cei:
            return lista_medicoes
        if self.solicitacoes_kit_lanche_cei_avulsa.filter(
            status="CODAE_AUTORIZADO",
            solicitacao_kit_lanche__data__month=mes,
            solicitacao_kit_lanche__data__year=ano,
        ).exists():
            lista_medicoes.append("Solicitações de Alimentação")
        return lista_medicoes

    def get_lista_medicoes_kit_lanche_cemei_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if "Solicitações de Alimentação" in lista_medicoes or not self.eh_cemei:
            return lista_medicoes
        if self.solicitacoes_kit_lanche_cemei.filter(
            status="CODAE_AUTORIZADO", data__month=mes, data__year=ano
        ).exists():
            lista_medicoes.append("Solicitações de Alimentação")
        return lista_medicoes

    def get_lista_medicoes_qualquer_kit_lanche_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        lista_medicoes = self.get_lista_medicoes_kit_lanche_avulso_autorizado_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = self.get_lista_medicoes_kit_lanche_unificado_autorizado_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = self.get_lista_medicoes_kit_lanche_cei_autorizado_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = self.get_lista_medicoes_kit_lanche_cemei_autorizado_no_mes(
            mes, ano, lista_medicoes
        )
        return lista_medicoes

    def get_lista_medicoes_alteracao_generica_lanche_emergencial_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if (
            "Solicitações de Alimentação" in lista_medicoes
            or self.eh_cei
            or self.eh_cemei
        ):
            return lista_medicoes
        if self.alteracaocardapio_set.filter(
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=mes,
            datas_intervalo__data__year=ano,
            datas_intervalo__cancelado=False,
            motivo__nome="Lanche Emergencial",
        ).exists():
            lista_medicoes.append("Solicitações de Alimentação")
        return lista_medicoes

    def get_lista_medicoes_alteracao_generica_rpl_lpr_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if self.eh_cei or self.eh_cemei:
            return lista_medicoes
        queryset = self.alteracaocardapio_set.filter(
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=mes,
            datas_intervalo__data__year=ano,
            datas_intervalo__cancelado=False,
        ).exclude(motivo__nome="Lanche Emergencial")
        if queryset.exists():
            periodos_escolares_nomes = list(
                queryset.values_list(
                    "substituicoes_periodo_escolar__periodo_escolar__nome",
                    flat=True,
                ).distinct()
            )
            lista_medicoes = list(set(periodos_escolares_nomes + lista_medicoes))
        return lista_medicoes

    def get_lista_medicoes_alteracao_cei_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if not self.eh_cei:
            return lista_medicoes
        queryset = self.alteracaocardapiocei_set.filter(
            status="CODAE_AUTORIZADO", data__month=mes, data__year=ano
        )
        if queryset.exists():
            periodos_escolares_nomes = list(
                queryset.values_list(
                    "substituicoes_cei_periodo_escolar__periodo_escolar__nome",
                    flat=True,
                ).distinct()
            )
            lista_medicoes = list(set(periodos_escolares_nomes + lista_medicoes))
        return lista_medicoes

    def get_lista_medicoes_alteracao_cemei_lanche_emergencial_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if "Solicitações de Alimentação" in lista_medicoes or not self.eh_cemei:
            return lista_medicoes
        queryset = self.alteracaocardapiocemei_set.filter(
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=mes,
            datas_intervalo__data__year=ano,
            datas_intervalo__cancelado=False,
            motivo__nome="Lanche Emergencial",
        )
        if queryset.exists():
            lista_medicoes.append("Solicitações de Alimentação")
        return lista_medicoes

    def get_lista_medicoes_alteracao_cemei_rpl_lpr_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if not self.eh_cemei:
            return lista_medicoes
        queryset = self.alteracaocardapiocemei_set.filter(
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=mes,
            datas_intervalo__data__year=ano,
            datas_intervalo__cancelado=False,
        ).exclude(motivo__nome="Lanche Emergencial")
        if queryset.exists():
            periodos_escolares_nomes = list(
                queryset.values_list(
                    "substituicoes_cemei_emei_periodo_escolar__periodo_escolar__nome",
                    "substituicoes_cemei_cei_periodo_escolar__periodo_escolar__nome",
                ).distinct()
            )
            periodos_unicos = list(
                {nome for tupla in periodos_escolares_nomes for nome in tupla if nome}
            )
            lista_medicoes = list(set(periodos_unicos + lista_medicoes))
        return lista_medicoes

    def get_lista_medicoes_qualquer_alteracao_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        lista_medicoes = (
            self.get_lista_medicoes_alteracao_generica_rpl_lpr_autorizada_no_mes(
                mes, ano, lista_medicoes
            )
        )
        lista_medicoes = self.get_lista_medicoes_alteracao_generica_lanche_emergencial_autorizada_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = self.get_lista_medicoes_alteracao_cei_autorizada_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = (
            self.get_lista_medicoes_alteracao_cemei_rpl_lpr_autorizada_no_mes(
                mes, ano, lista_medicoes
            )
        )
        lista_medicoes = self.get_lista_medicoes_alteracao_cemei_lanche_emergencial_autorizada_no_mes(
            mes, ano, lista_medicoes
        )
        return lista_medicoes

    def get_lista_medicoes_inclusao_normal_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if self.eh_cei or self.eh_cemei:
            return lista_medicoes
        queryset = self.grupos_inclusoes.filter(
            status="CODAE_AUTORIZADO",
            quantidades_por_periodo__cancelado=False,
            inclusoes_normais__data__month=mes,
            inclusoes_normais__data__year=ano,
        )
        if queryset.exists():
            periodos_escolares_nomes = list(
                queryset.values_list(
                    "quantidades_por_periodo__periodo_escolar__nome", flat=True
                ).distinct()
            )
            lista_medicoes = list(set(periodos_escolares_nomes + lista_medicoes))
        return lista_medicoes

    def get_lista_medicoes_inclusao_continua_programas_projetos_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if "Programas e Projetos" in lista_medicoes or self.eh_cei:
            return lista_medicoes
        primeiro_dia_mes = datetime.date(ano, mes, 1)
        ultimo_dia_mes = get_ultimo_dia_mes(primeiro_dia_mes)
        queryset = self.inclusoes_alimentacao_continua.filter(
            status="CODAE_AUTORIZADO",
            data_inicial__lte=ultimo_dia_mes,
            data_final__gte=primeiro_dia_mes,
        ).exclude(motivo__nome="ETEC")
        if queryset.exists():
            lista_medicoes.append("Programas e Projetos")
        return lista_medicoes

    def get_lista_medicoes_inclusao_continua_etec_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if "ETEC" in lista_medicoes or self.eh_cei:
            return lista_medicoes
        primeiro_dia_mes = datetime.date(ano, mes, 1)
        ultimo_dia_mes = get_ultimo_dia_mes(primeiro_dia_mes)
        queryset = self.inclusoes_alimentacao_continua.filter(
            status="CODAE_AUTORIZADO",
            data_inicial__lte=ultimo_dia_mes,
            data_final__gte=primeiro_dia_mes,
            motivo__nome="ETEC",
        )
        if queryset.exists():
            lista_medicoes.append("ETEC")
        return lista_medicoes

    def get_lista_medicoes_inclusao_cei_parcial_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        """
        Verifica se há alguma inclusão CEI com período externo diferente do interno,
        autorizada pela CODAE no mês e ano informados.

        Args:
            mes (int): Mês da solicitação.
            ano (int): Ano da solicitação.
            lista_medicoes (list): Lista de medições iniciais com solicitações identificadas anteriormente.

        Returns:
            list: A lista de erros atualizada, incluindo "PARCIAL" se for identificado periodos diferentes.
        """

        if "PARCIAL" in lista_medicoes or not self.eh_cei:
            return lista_medicoes
        if (
            self.grupos_inclusoes_por_cei.filter(
                status="CODAE_AUTORIZADO",
                dias_motivos_da_inclusao_cei__data__month=mes,
                dias_motivos_da_inclusao_cei__data__year=ano,
                dias_motivos_da_inclusao_cei__cancelado=False,
            )
            .filter(
                ~Q(
                    quantidade_alunos_da_inclusao__periodo=F(
                        "quantidade_alunos_da_inclusao__periodo_externo"
                    )
                )
            )
            .exists()
        ):
            lista_medicoes.append("PARCIAL")
        return lista_medicoes

    def get_lista_medicoes_inclusao_cei_periodos_escolares_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        """
        Verifica se há alguma inclusão CEI com período externo igual do interno,
        autorizada pela CODAE no mês e ano informados.

        Args:
            mes (int): Mês da solicitação.
            ano (int): Ano da solicitação.
            lista_medicoes (list): Lista de medições iniciais com solicitações identificadas anteriormente.

        Returns:
            list: A lista de erros atualizada, incluindo "INTEGRAL", "MANHA", "TARDE", etc. se for identificado periodos iguais.
        """

        if not self.eh_cei:
            return lista_medicoes
        queryset = self.grupos_inclusoes_por_cei.filter(
            status="CODAE_AUTORIZADO",
            dias_motivos_da_inclusao_cei__data__month=mes,
            dias_motivos_da_inclusao_cei__data__year=ano,
            dias_motivos_da_inclusao_cei__cancelado=False,
        ).filter(
            Q(
                quantidade_alunos_da_inclusao__periodo=F(
                    "quantidade_alunos_da_inclusao__periodo_externo"
                )
            )
        )
        if queryset.exists():
            periodos_escolares_nomes = list(
                queryset.values_list(
                    "quantidade_alunos_da_inclusao__periodo__nome", flat=True
                ).distinct()
            )
            lista_medicoes = list(set(periodos_escolares_nomes + lista_medicoes))
        return lista_medicoes

    def get_lista_medicoes_inclusao_cemei_cei_parcial_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        """
        Verifica se há alguma inclusão CEI da CEMEI com período escolar diferente de INTEGRAL
        autorizada pela CODAE no mês e ano informados.

        Args:
            mes (int): Mês da solicitação.
            ano (int): Ano da solicitação.
            lista_medicoes (list): Lista de medições iniciais com solicitações identificadas anteriormente.

        Returns:
            list: A lista de erros atualizada, incluindo "PARCIAL" se for identificado um período diferente de INTEGRAL
        """
        if "PARCIAL" in lista_medicoes or not self.eh_cemei:
            return lista_medicoes
        queryset = self.inclusoes_de_alimentacao_cemei.filter(
            status="CODAE_AUTORIZADO",
            dias_motivos_da_inclusao_cemei__data__month=mes,
            dias_motivos_da_inclusao_cemei__data__year=ano,
            dias_motivos_da_inclusao_cemei__cancelado=False,
            quantidade_alunos_cei_da_inclusao_cemei__isnull=False,
        ).filter(
            ~Q(
                quantidade_alunos_cei_da_inclusao_cemei__periodo_escolar__nome="INTEGRAL"
            )
        )
        if queryset.exists():
            lista_medicoes.append("PARCIAL")
        return lista_medicoes

    def get_lista_medicoes_inclusao_cemei_cei_integral_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if "INTEGRAL" in lista_medicoes or not self.eh_cemei:
            return lista_medicoes
        queryset = self.inclusoes_de_alimentacao_cemei.filter(
            status="CODAE_AUTORIZADO",
            dias_motivos_da_inclusao_cemei__data__month=mes,
            dias_motivos_da_inclusao_cemei__data__year=ano,
            dias_motivos_da_inclusao_cemei__cancelado=False,
            quantidade_alunos_cei_da_inclusao_cemei__periodo_escolar__nome="INTEGRAL",
        )
        if queryset.exists():
            lista_medicoes.append("INTEGRAL")
        return lista_medicoes

    def get_lista_medicoes_inclusao_cemei_emei_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if not self.eh_cemei:
            return lista_medicoes
        queryset = self.inclusoes_de_alimentacao_cemei.filter(
            status="CODAE_AUTORIZADO",
            dias_motivos_da_inclusao_cemei__data__month=mes,
            dias_motivos_da_inclusao_cemei__data__year=ano,
            dias_motivos_da_inclusao_cemei__cancelado=False,
            quantidade_alunos_emei_da_inclusao_cemei__isnull=False,
        )
        if queryset.exists():
            periodos_escolares_nomes = list(
                queryset.values_list(
                    "quantidade_alunos_emei_da_inclusao_cemei__periodo_escolar__nome",
                    flat=True,
                ).distinct()
            )
            nomes_normalizados = [
                "Infantil " + nome for nome in periodos_escolares_nomes
            ]
            lista_medicoes = list(set(lista_medicoes + nomes_normalizados))
        return lista_medicoes

    def get_lista_medicoes_qualquer_inclusao_autorizada_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        lista_medicoes = self.get_lista_medicoes_inclusao_normal_autorizada_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = self.get_lista_medicoes_inclusao_continua_programas_projetos_autorizada_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = (
            self.get_lista_medicoes_inclusao_continua_etec_autorizada_no_mes(
                mes, ano, lista_medicoes
            )
        )

        lista_medicoes = (
            self.get_lista_medicoes_inclusao_cei_periodos_escolares_autorizada_no_mes(
                mes, ano, lista_medicoes
            )
        )
        lista_medicoes = self.get_lista_medicoes_inclusao_cei_parcial_autorizada_no_mes(
            mes, ano, lista_medicoes
        )

        lista_medicoes = (
            self.get_lista_medicoes_inclusao_cemei_cei_integral_autorizada_no_mes(
                mes, ano, lista_medicoes
            )
        )
        lista_medicoes = (
            self.get_lista_medicoes_inclusao_cemei_cei_parcial_autorizada_no_mes(
                mes, ano, lista_medicoes
            )
        )
        lista_medicoes = self.get_lista_medicoes_inclusao_cemei_emei_autorizada_no_mes(
            mes, ano, lista_medicoes
        )

        return lista_medicoes

    def get_lista_medicoes_solicitacoes_autorizadas_no_mes(
        self, mes: int, ano: int
    ) -> list:
        """
        Verifica se há alguma solicitação autorizada para o mês e ano passados como parâmetro.

        Args:
            mes (int): Mês da solicitação.
            ano (int): Ano da solicitação.

        Returns:
            list[str]: A lista de strings com os tipos de medição inicial possíveis
        """
        lista_medicoes = []
        lista_medicoes = self.get_lista_medicoes_qualquer_kit_lanche_autorizado_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = self.get_lista_medicoes_qualquer_alteracao_autorizada_no_mes(
            mes, ano, lista_medicoes
        )
        lista_medicoes = self.get_lista_medicoes_qualquer_inclusao_autorizada_no_mes(
            mes, ano, lista_medicoes
        )
        return lista_medicoes

    class Meta:
        verbose_name = "Escola"
        verbose_name_plural = "Escolas"
        ordering = ("codigo_eol",)


class EscolaPeriodoEscolar(
    ExportModelOperationsMixin("escola_periodo"), Ativavel, TemChaveExterna
):
    """Serve para guardar a quantidade de alunos da escola em um dado periodo escolar.

    Ex: EMEI BLABLA pela manhã tem 55 alunos
    """

    escola = models.ForeignKey(
        Escola, related_name="escolas_periodos", on_delete=models.DO_NOTHING
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar, related_name="escolas_periodos", on_delete=models.DO_NOTHING
    )
    quantidade_alunos = models.PositiveSmallIntegerField(
        "Quantidade de alunos", default=0
    )
    horas_atendimento = models.IntegerField(null=True)

    def __str__(self):
        periodo_nome = self.periodo_escolar.nome

        return f"Escola {self.escola.nome} no periodo da {periodo_nome} tem {self.quantidade_alunos} alunos"

    def alunos_por_faixa_etaria(self, data_referencia):  # noqa C901
        """
        Calcula quantos alunos existem em cada faixa etaria nesse período.

        Retorna um collections.Counter, onde as chaves são o uuid das faixas etárias
        e os valores os totais de alunos. Exemplo:
        {
            'asdf-1234': 25,
            'qwer-5678': 42,
            'zxcv-4567': 16
        }
        """
        faixas_etarias = FaixaEtaria.objects.filter(ativo=True)
        if faixas_etarias.count() == 0:
            raise ObjectDoesNotExist()
        lista_alunos = (
            EOLServicoSGP.get_lista_alunos_por_escola_ano_corrente_ou_seguinte(
                self.escola.codigo_eol
            )
        )

        faixa_alunos = Counter()
        for aluno in lista_alunos:
            if aluno["tipoTurno"] == self.periodo_escolar.tipo_turno:
                data_nascimento = dt_nascimento_from_api(aluno["dataNascimento"])
                meses = (data_nascimento.year - data_referencia.year) * 12
                meses = meses + (data_nascimento.month - data_referencia.month)
                meses = meses * (-1)
                if meses >= 73:
                    faixa_etaria = FaixaEtaria.objects.filter(
                        inicio=48, fim=73, ativo=True
                    ).first()
                else:
                    faixa_etaria = FaixaEtaria.objects.filter(
                        inicio__lte=int(meses), fim__gt=int(meses), ativo=True
                    ).first()
                if faixa_etaria:
                    faixa_alunos[faixa_etaria.uuid] += 1
        return faixa_alunos

    class Meta:
        verbose_name = "Escola com período escolar"
        verbose_name_plural = "Escola com períodos escolares"
        unique_together = [["periodo_escolar", "escola"]]


class LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar(
    TemChaveExterna, CriadoEm, Justificativa, CriadoPor
):
    escola = models.ForeignKey(
        Escola,
        related_name="log_alteracao_quantidade_alunos",
        on_delete=models.DO_NOTHING,
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar,
        related_name="log_alteracao_quantidade_alunos",
        on_delete=models.DO_NOTHING,
    )
    quantidade_alunos_de = models.PositiveSmallIntegerField(
        "Quantidade de alunos anterior", default=0
    )
    quantidade_alunos_para = models.PositiveSmallIntegerField(
        "Quantidade de alunos alterada", default=0
    )

    def __str__(self):
        quantidade_anterior = self.quantidade_alunos_de
        quantidade_atual = self.quantidade_alunos_para
        escola = self.escola.nome
        return f"Alteração de: {quantidade_anterior} alunos, para: {quantidade_atual} alunos na escola: {escola}"

    class Meta:
        verbose_name = "Log Alteração quantidade de alunos"
        verbose_name_plural = "Logs de Alteração quantidade de alunos"
        ordering = ("criado_em",)


class LogRotinaDiariaAlunos(TemChaveExterna, CriadoEm):
    quantidade_alunos_antes = models.PositiveIntegerField(
        "Quantidade de alunos antes", default=0
    )
    quantidade_alunos_atual = models.PositiveIntegerField(
        "Quantidade de alunos atual", default=0
    )

    def __str__(self):
        criado_em = self.criado_em.strftime("%Y-%m-%d %H:%M:%S")
        quant_antes = self.quantidade_alunos_antes
        quant_atual = self.quantidade_alunos_atual
        return f"Criado em {criado_em} - Quant. de alunos antes: {quant_antes}. Quant. de alunos atual: {quant_atual}"

    class Meta:
        verbose_name = "Log Rotina Diária quantidade de alunos"
        verbose_name_plural = "Logs Rotina Diária quantidade de alunos"
        ordering = ("-criado_em",)


class Lote(ExportModelOperationsMixin("lote"), TemChaveExterna, Nomeavel, Iniciais):
    """Lote de escolas."""

    tipo_gestao = models.ForeignKey(
        TipoGestao,
        on_delete=models.DO_NOTHING,
        related_name="lotes",
        null=True,
        blank=True,
    )
    diretoria_regional = models.ForeignKey(
        "escola.DiretoriaRegional",
        on_delete=models.DO_NOTHING,
        related_name="lotes",
        null=True,
        blank=True,
    )
    terceirizada = models.ForeignKey(
        "terceirizada.Terceirizada",
        on_delete=models.DO_NOTHING,
        related_name="lotes",
        null=True,
        blank=True,
    )

    @property
    def escolas(self):
        return self.escolas

    @property
    def quantidade_alunos(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=self.escolas.all(), tipo_turma="REGULAR"
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    def _transferir_solicitacoes_gestao_alimentacao(
        self, terceirizada, data_da_virada: datetime.date
    ) -> None:
        """
        Transfere Solicitações de Gestão de Alimentação pendentes de autorização ou autorizadas à serem atendidadas,
        ou seja, com datas futuras à transferência do lote para a empresa nova.
        """
        canceladas_ou_negadas = Q(
            status__in=[
                FluxoAprovacaoPartindoDaEscola.workflow_class.CODAE_NEGOU_PEDIDO,
                FluxoAprovacaoPartindoDaEscola.workflow_class.CANCELADO_AUTOMATICAMENTE,
                FluxoAprovacaoPartindoDaEscola.workflow_class.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
                FluxoAprovacaoPartindoDaEscola.workflow_class.ESCOLA_CANCELOU,
            ]
        )
        canceladas_suspensao = Q(
            status__in=[FluxoInformativoPartindoDaEscola.workflow_class.ESCOLA_CANCELOU]
        )
        self.inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data_inicial__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.inclusao_alimentacao_grupoinclusaoalimentacaonormal_rastro_lote.exclude(
            canceladas_ou_negadas | Q(inclusoes_normais__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(dias_motivos_da_inclusao_cei__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(dias_motivos_da_inclusao_cemei__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_alteracaocardapio_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data_inicial__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_alteracaocardapiocei_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_alteracaocardapiocemei_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(alterar_dia__lt=data_da_virada)
            | Q(data_inicial__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.kit_lanche_solicitacaokitlancheavulsa_rastro_lote.exclude(
            canceladas_ou_negadas | Q(solicitacao_kit_lanche__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.kit_lanche_solicitacaokitlancheceiavulsa_rastro_lote.exclude(
            canceladas_ou_negadas | Q(solicitacao_kit_lanche__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.kit_lanche_solicitacaokitlanchecemei_rastro_lote.exclude(
            canceladas_ou_negadas | Q(data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_inversaocardapio_rastro_lote.exclude(
            canceladas_ou_negadas
            | Q(data_de_inversao__lt=data_da_virada)
            | Q(data_para_inversao__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_gruposuspensaoalimentacao_rastro_lote.exclude(
            canceladas_suspensao | Q(suspensoes_alimentacao__data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)
        self.cardapio_suspensaoalimentacaodacei_rastro_lote.exclude(
            canceladas_suspensao | Q(data__lt=data_da_virada)
        ).update(rastro_terceirizada=terceirizada, terceirizada_conferiu_gestao=False)

    def _transferir_solicitacoes_gestao_alimentacao_com_datas_no_passado_e_no_presente(
        self, terceirizada_nova, data_virada: datetime.date
    ) -> None:
        """
        Realiza a transferência de todas as solicitações de Gestão de Alimentação autorizadas
        com datas no passado/presente e futuro.
        """
        terceirizada_pre_transferencia = self.terceirizada

        for tipo, cfg in self.TRANSFERENCIAS_CONFIG.items():
            self._transferir_lote_generico_config(
                tipo, data_virada, terceirizada_pre_transferencia, terceirizada_nova
            )

    TRANSFERENCIAS_CONFIG = {
        # ---------------- Inclusões ----------------
        "inclusoes_continuas": {
            "query_attr": "inclusao_alimentacao_inclusaoalimentacaocontinua_rastro_lote",
            "model": "InclusaoAlimentacaoContinua",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {"data_final__gte": "data_virada"},
            "cria_fk_func": "_cria_objetos_fk_inclusao_continua_copia",
            "atualiza_original": "_atualiza_inclusao_continua_original",
            "atualiza_copia": "_atualiza_inclusao_continua_copia_para_nova_terceirizada",
        },
        "inclusoes_normais": {
            "query_attr": "inclusao_alimentacao_grupoinclusaoalimentacaonormal_rastro_lote",
            "model": "GrupoInclusaoAlimentacaoNormal",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "inclusoes_normais__data__gte": "data_virada",
                "inclusoes_normais__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_inclusao_normal_copia",
            "atualiza_original": "_atualiza_inclusao_normal_original",
            "atualiza_copia": "_atualiza_inclusao_normal_copia_para_nova_terceirizada",
        },
        "inclusoes_cei": {
            "query_attr": "inclusao_alimentacao_inclusaoalimentacaodacei_rastro_lote",
            "model": "InclusaoAlimentacaoDaCEI",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "dias_motivos_da_inclusao_cei__data__gte": "data_virada",
                "dias_motivos_da_inclusao_cei__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_inclusao_cei_copia",
            "atualiza_original": "_atualiza_inclusao_cei_original",
            "atualiza_copia": "_atualiza_inclusao_cei_copia_para_nova_terceirizada",
        },
        "inclusoes_cemei": {
            "query_attr": "inclusao_alimentacao_inclusaodealimentacaocemei_rastro_lote",
            "model": "InclusaoDeAlimentacaoCEMEI",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "dias_motivos_da_inclusao_cemei__data__gte": "data_virada",
                "dias_motivos_da_inclusao_cemei__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_inclusao_cemei_copia",
            "atualiza_original": "_atualiza_inclusao_cemei_original",
            "atualiza_copia": "_atualiza_inclusao_cemei_copia_para_nova_terceirizada",
        },
        # ---------------- Alterações ----------------
        "alteracoes": {
            "query_attr": "cardapio_alteracaocardapio_rastro_lote",
            "model": "AlteracaoCardapio",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "datas_intervalo__data__gte": "data_virada",
                "datas_intervalo__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_alteracao_copia",
            "atualiza_original": "_atualiza_alteracao_original",
            "atualiza_copia": "_atualiza_alteracao_copia_para_nova_terceirizada",
        },
        "alteracoes_cemei": {
            "query_attr": "cardapio_alteracaocardapiocemei_rastro_lote",
            "model": "AlteracaoCardapioCEMEI",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": {
                "datas_intervalo__data__gte": "data_virada",
                "datas_intervalo__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_alteracao_cemei_copia",
            "atualiza_original": "_atualiza_alteracao_original",
            "atualiza_copia": "_atualiza_alteracao_copia_para_nova_terceirizada",
        },
        # ---------------- Suspensões ----------------
        "suspensoes": {
            "query_attr": "cardapio_gruposuspensaoalimentacao_rastro_lote",
            "model": "GrupoSuspensaoAlimentacao",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.INFORMADO,
            "filtros_extra": {
                "suspensoes_alimentacao__data__gte": "data_virada",
                "suspensoes_alimentacao__cancelado": False,
            },
            "cria_fk_func": "_cria_objetos_fk_suspensao_copia",
            "atualiza_original": "_atualiza_suspensao_original",
            "atualiza_copia": "_atualiza_suspensao_copia_para_nova_terceirizada",
        },
        # ---------------- Inversões ----------------
        "inversoes": {
            "query_attr": "cardapio_inversaocardapio_rastro_lote",
            "model": "InversaoCardapio",
            "status_field": "status",
            "status_value": lambda cls: cls.workflow_class.CODAE_AUTORIZADO,
            "filtros_extra": [
                {"data_de_inversao__gte": "data_virada"},
                {"data_para_inversao__gte": "data_virada"},
                {"data_de_inversao_2__gte": "data_virada"},
                {"data_para_inversao_2__gte": "data_virada"},
            ],
            "cria_fk_func": "_cria_objetos_fk_inversao_copia",
            "atualiza_original": "_atualiza_inversao_original",
            "atualiza_copia": "_atualiza_inversao_copia_para_nova_terceirizada",
        },
    }

    def _transferir_lote_generico_config(
        self, tipo, data_virada, terceirizada_pre_transferencia, terceirizada_nova
    ):
        cfg = self.TRANSFERENCIAS_CONFIG[tipo]
        model_class = globals()[cfg["model"]]
        status_value = cfg["status_value"](model_class)

        filtros_extra = cfg.get("filtros_extra", {})

        queryset_base = getattr(self, cfg["query_attr"]).filter(
            **{
                cfg["status_field"]: status_value,
                "rastro_terceirizada": terceirizada_pre_transferencia,
            }
        )

        # Se for lista, combina com OR
        if isinstance(filtros_extra, list):
            q_obj = Q()
            for f in filtros_extra:
                resolved = {
                    campo: (data_virada if valor == "data_virada" else valor)
                    for campo, valor in f.items()
                }
                q_obj |= Q(**resolved)
            queryset = queryset_base.filter(q_obj)
        else:
            # Caso normal: dict (AND)
            resolved = {
                campo: (data_virada if valor == "data_virada" else valor)
                for campo, valor in filtros_extra.items()
            }
            queryset = queryset_base.filter(**resolved)

        queryset = queryset.distinct()

        if not queryset.exists():
            return

        cria_fk_func = getattr(self, cfg["cria_fk_func"])
        atualiza_original_func = getattr(self, cfg["atualiza_original"])
        atualiza_copia_func = getattr(self, cfg["atualiza_copia"])

        for original in queryset:
            uuid_original = original.uuid
            copia = clonar_objeto(original)
            original = model_class.objects.get(uuid=uuid_original)

            cria_fk_func(copia, original)
            atualiza_original_func(original, data_virada)
            atualiza_copia_func(copia, data_virada, terceirizada_nova)

    def _criar_copias_fk(self, original, copia, campos_fk, relacao):
        for campo_fk in campos_fk:
            cria_copias_fk(original, campo_fk, relacao, copia)

    # Inclusão Contínua
    def _cria_objetos_fk_inclusao_continua_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["quantidades_por_periodo"],
            "inclusao_alimentacao_continua",
        )
        copiar_logs(original, copia)

    def _atualiza_inclusao_continua_original(self, original, data_virada):
        original.data_final = data_virada - datetime.timedelta(days=1)
        original.save()

    def _atualiza_inclusao_continua_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.data_inicial = data_virada
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inclusão Normal
    def _cria_objetos_fk_inclusao_normal_copia(self, copia, original):
        self._criar_copias_fk(
            original, copia, ["quantidades_por_periodo"], "grupo_inclusao_normal"
        )
        self._criar_copias_fk(original, copia, ["inclusoes_normais"], "grupo_inclusao")
        copiar_logs(original, copia)

    def _atualiza_inclusao_normal_original(self, original, data_virada):
        original.inclusoes_normais.filter(data__gte=data_virada).delete()

    def _atualiza_inclusao_normal_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.inclusoes_normais.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inclusão CEI
    def _cria_objetos_fk_inclusao_cei_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["quantidade_alunos_da_inclusao"],
            "inclusao_alimentacao_da_cei",
        )
        self._criar_copias_fk(
            original, copia, ["dias_motivos_da_inclusao_cei"], "inclusao_cei"
        )
        copiar_logs(original, copia)

    def _atualiza_inclusao_cei_original(self, original, data_virada):
        original.dias_motivos_da_inclusao_cei.filter(data__gte=data_virada).delete()

    def _atualiza_inclusao_cei_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.dias_motivos_da_inclusao_cei.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inclusão CEMEI
    def _cria_objetos_fk_inclusao_cemei_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            [
                "dias_motivos_da_inclusao_cemei",
                "quantidade_alunos_cei_da_inclusao_cemei",
                "quantidade_alunos_emei_da_inclusao_cemei",
            ],
            "inclusao_alimentacao_cemei",
        )
        copiar_logs(original, copia)

    def _atualiza_inclusao_cemei_original(self, original, data_virada):
        original.dias_motivos_da_inclusao_cemei.filter(data__gte=data_virada).delete()

    def _atualiza_inclusao_cemei_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.dias_motivos_da_inclusao_cemei.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Alterações
    def _cria_objetos_fk_alteracao_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["datas_intervalo", "substituicoes_periodo_escolar"],
            "alteracao_cardapio",
        )
        copiar_logs(original, copia)

    def _cria_objetos_fk_alteracao_cemei_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            [
                "substituicoes_cemei_cei_periodo_escolar",
                "substituicoes_cemei_emei_periodo_escolar",
            ],
            "alteracao_cardapio",
        )
        self._criar_copias_fk(
            original, copia, ["datas_intervalo"], "alteracao_cardapio_cemei"
        )
        for index, substituicao_cemei_cei in enumerate(
            original.substituicoes_cemei_cei_periodo_escolar.all().order_by("id")
        ):
            for faixa_etaria in substituicao_cemei_cei.faixas_etarias.all():
                faixa_etaria_copia = deepcopy(faixa_etaria)
                faixa_etaria_copia.id = None
                faixa_etaria_copia.uuid = uuid.uuid4()
                faixa_etaria_copia.substituicao_alimentacao = (
                    copia.substituicoes_cemei_cei_periodo_escolar.all().order_by("id")[
                        index
                    ]
                )
                faixa_etaria_copia.save()
        copiar_logs(original, copia)

    def _atualiza_alteracao_original(self, original, data_virada):
        original.datas_intervalo.filter(data__gte=data_virada).delete()
        data_pre_virada = data_virada - datetime.timedelta(days=1)
        original.data_final = data_pre_virada
        original.save()

    def _atualiza_alteracao_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.datas_intervalo.filter(data__lt=data_virada).delete()
        copia.data_inicial = data_virada
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Suspensões
    def _cria_objetos_fk_suspensao_copia(self, copia, original):
        self._criar_copias_fk(
            original,
            copia,
            ["quantidades_por_periodo", "suspensoes_alimentacao"],
            "grupo_suspensao",
        )
        copiar_logs(original, copia)

    def _atualiza_suspensao_original(self, original, data_virada):
        original.suspensoes_alimentacao.filter(data__gte=data_virada).delete()

    def _atualiza_suspensao_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.suspensoes_alimentacao.filter(data__lt=data_virada).delete()
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    # Inversões
    def _cria_objetos_fk_inversao_copia(self, copia, original):
        campos_m2m = ["tipos_alimentacao"]
        for campo_m2m in campos_m2m:
            cria_copias_m2m(original, campo_m2m, copia)
        copiar_logs(original, copia)

    def _atualiza_inversao_original(self, original, data_virada):
        return

    def _atualiza_inversao_copia_para_nova_terceirizada(
        self, copia, data_virada, terceirizada_nova
    ):
        copia.rastro_terceirizada = terceirizada_nova
        copia.terceirizada_conferiu_gestao = False
        copia.save()

    def _transferir_dietas_especiais(self, terceirizada_nova) -> None:
        """
        Transfere dietas especiais ativas e autorizadas para a nova empresa do lote
        """
        canceladas_ou_negadas_ou_inativas = Q(
            status__in=[
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CANCELADO_ALUNO_MUDOU_ESCOLA,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CODAE_NEGOU_PEDIDO,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.ESCOLA_CANCELOU,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.TERMINADA_AUTOMATICAMENTE_SISTEMA,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.CODAE_AUTORIZOU_INATIVACAO,
                FluxoDietaEspecialPartindoDaEscola.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
            ],
        )
        self.dieta_especial_solicitacaodietaespecial_rastro_lote.exclude(
            canceladas_ou_negadas_ou_inativas
        ).exclude(
            status=FluxoDietaEspecialPartindoDaEscola.workflow_class.CODAE_AUTORIZADO,
            ativo=False,
        ).update(
            rastro_terceirizada=terceirizada_nova, conferido=False
        )

    @transaction.atomic
    def transferir_lote(
        self, terceirizada_nova, data_da_virada=datetime.date.today()
    ) -> None:
        """
        Realiza a transferência das solicitações de Gestão de Alimentação e Dieta Especial para a nova
        empresa a assumir o fornecimento do lote.
        """
        self._transferir_solicitacoes_gestao_alimentacao(
            terceirizada_nova, data_da_virada
        )
        self._transferir_solicitacoes_gestao_alimentacao_com_datas_no_passado_e_no_presente(
            terceirizada_nova, data_da_virada
        )
        self._transferir_dietas_especiais(terceirizada_nova)

    def __str__(self):
        nome_dre = (
            self.diretoria_regional.nome
            if self.diretoria_regional
            else "sem DRE definida"
        )
        return f"{self.nome} - {nome_dre}"

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ("nome",)


class Subprefeitura(
    ExportModelOperationsMixin("subprefeitura"), Nomeavel, TemChaveExterna
):
    AGRUPAMENTO = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
    )

    codigo_eol = models.CharField(  # noqa DJ01
        "Código EOL", max_length=6, unique=True, null=True, blank=True
    )
    diretoria_regional = models.ManyToManyField(
        DiretoriaRegional, related_name="subprefeituras", blank=True
    )
    lote = models.ForeignKey(
        "Lote",
        related_name="subprefeituras",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    agrupamento = models.PositiveSmallIntegerField(choices=AGRUPAMENTO, default=1)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Subprefeitura"
        verbose_name_plural = "Subprefeituras"
        ordering = ("nome",)


class Codae(
    ExportModelOperationsMixin("codae"),
    Nomeavel,
    TemChaveExterna,
    TemVinculos,
    AcessoModuloMedicaoInicial,
):
    @property
    def vinculos_que_podem_ser_finalizados(self):
        return self.vinculos.filter(
            Q(data_inicial=None, data_final=None, ativo=False)
            | Q(  # noqa W504 esperando ativacao
                data_inicial__isnull=False, data_final=None, ativo=True
            )  # noqa W504 ativo
        ).exclude(
            perfil__nome__in=[
                COORDENADOR_DIETA_ESPECIAL,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
            ]
        )

    @property
    def quantidade_alunos(self):
        quantidade_result = AlunosMatriculadosPeriodoEscola.objects.filter(
            escola__in=Escola.objects.all(), tipo_turma="REGULAR"
        ).aggregate(Sum("quantidade_alunos"))
        return quantidade_result.get("quantidade_alunos__sum") or 0

    def inversoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InversaoCardapio)
        return queryset.filter(
            status__in=[
                InversaoCardapio.workflow_class.DRE_VALIDADO,
                InversaoCardapio.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def grupos_inclusoes_alimentacao_normal_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, GrupoInclusaoAlimentacaoNormal)
        return queryset.filter(
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_VALIDADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def filtra_solicitacoes_minhas_escolas_a_validar_por_data(
        self, filtro_aplicado, model
    ):
        queryset = queryset_por_data(filtro_aplicado, model)
        return queryset.filter(
            escola__in=Escola.objects.all(),
            status=SolicitacaoKitLancheAvulsa.workflow_class.DRE_A_VALIDAR,
        )

    def inclusoes_alimentacao_de_cei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InclusaoAlimentacaoDaCEI)
        return queryset.filter(
            status__in=[
                InclusaoAlimentacaoDaCEI.workflow_class.DRE_VALIDADO,
                InclusaoAlimentacaoDaCEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def inversoes_cardapio_autorizadas(self):
        return InversaoCardapio.objects.filter(
            status__in=[
                InversaoCardapio.workflow_class.CODAE_AUTORIZADO,
                InversaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inversoes_cardapio_reprovados(self):
        return InversaoCardapio.objects.filter(
            status__in=[InversaoCardapio.workflow_class.CODAE_NEGOU_PEDIDO]
        )

    def inclusoes_alimentacao_continua_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InclusaoAlimentacaoContinua)
        return queryset.filter(
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_VALIDADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def inclusoes_alimentacao_cemei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InclusaoDeAlimentacaoCEMEI)
        return queryset.filter(
            status__in=[
                InclusaoDeAlimentacaoCEMEI.workflow_class.DRE_VALIDADO,
                InclusaoDeAlimentacaoCEMEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def alteracoes_cardapio_das_minhas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapio)
        return queryset.filter(
            status__in=[
                AlteracaoCardapio.workflow_class.DRE_VALIDADO,
                AlteracaoCardapio.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def alteracoes_cardapio_cei_das_minhas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEI)
        return queryset.filter(
            status__in=[
                AlteracaoCardapioCEI.workflow_class.DRE_VALIDADO,
                AlteracaoCardapioCEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def alteracoes_cardapio_cemei_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEMEI)
        return queryset.filter(
            status__in=[
                AlteracaoCardapioCEMEI.workflow_class.DRE_VALIDADO,
                AlteracaoCardapioCEMEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def suspensoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        return GrupoSuspensaoAlimentacao.objects.filter(
            ~Q(status__in=[GrupoSuspensaoAlimentacao.workflow_class.RASCUNHO])
        )

        #
        # Inversões de cardápio
        #

    def solicitacoes_unificadas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheUnificada)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheUnificada.workflow_class.CODAE_A_AUTORIZAR,
                SolicitacaoKitLancheUnificada.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def solicitacoes_unificadas_autorizadas(self):
        return SolicitacaoKitLancheUnificada.objects.filter(
            status__in=[
                SolicitacaoKitLancheUnificada.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheUnificada.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inclusoes_continuas_autorizadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            status__in=[
                InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheUnificada.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inclusoes_normais_autorizadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def inclusoes_continuas_reprovadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_NEGOU_PEDIDO
        )

    @property
    def inclusoes_normais_reprovadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_NEGOU_PEDIDO
        )

    @property
    def solicitacao_kit_lanche_avulsa_autorizadas(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheAvulsa.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    def solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
        self, filtro_aplicado
    ):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheCEMEI)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheCEMEI.workflow_class.DRE_VALIDADO,
                SolicitacaoKitLancheCEMEI.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def solicitacao_kit_lanche_avulsa_reprovadas(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            status=SolicitacaoKitLancheAvulsa.workflow_class.CODAE_NEGOU_PEDIDO
        )

    def solicitacoes_kit_lanche_das_minhas_escolas_a_validar(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheAvulsa)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.DRE_VALIDADO,
                SolicitacaoKitLancheAvulsa.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    def solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, SolicitacaoKitLancheCEIAvulsa)
        return queryset.filter(
            status__in=[
                SolicitacaoKitLancheCEIAvulsa.workflow_class.DRE_VALIDADO,
                SolicitacaoKitLancheCEIAvulsa.workflow_class.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ]
        )

    @property
    def alteracoes_cardapio_autorizadas(self):
        return AlteracaoCardapio.objects.filter(
            status__in=[
                AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
                AlteracaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ]
        )

    @property
    def alteracoes_cardapio_reprovadas(self):
        return AlteracaoCardapio.objects.filter(
            status=AlteracaoCardapio.workflow_class.CODAE_NEGOU_PEDIDO
        )

    def delete(self, *args, **kwargs):
        pass

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "CODAE"
        verbose_name_plural = "CODAE"


class Responsavel(Nomeavel, TemChaveExterna, CriadoEm):
    cpf = models.CharField(  # noqa DJ01
        max_length=11,
        blank=True,
        null=True,
        unique=True,
        validators=[MinLengthValidator(11)],
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Responsável"
        verbose_name_plural = "Reponsáveis"


class FaixaEtaria(Ativavel, TemChaveExterna):
    inicio = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    fim = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])

    def data_pertence_a_faixa(self, data_pesquisada, data_referencia_arg=None):
        data_referencia = (
            date.today() if data_referencia_arg is None else data_referencia_arg
        )
        data_inicio = subtrai_meses_de_data(self.fim, data_referencia)
        data_fim = subtrai_meses_de_data(self.inicio, data_referencia)
        return data_inicio <= data_pesquisada < data_fim

    def __str__(self):
        return faixa_to_string(self.inicio, self.fim)


class Aluno(TemChaveExterna):
    ETAPA_INFANTIL = 10

    CICLO_ALUNO_CEI = 1
    CICLO_ALUNO_EMEI = 2

    nome = models.CharField("Nome Completo do Aluno", max_length=100)
    codigo_eol = models.CharField(  # noqa DJ01
        "Código EOL",
        max_length=7,
        unique=True,
        validators=[MinLengthValidator(7)],
        null=True,
        blank=True,
    )
    data_nascimento = models.DateField()
    escola = models.ForeignKey(Escola, blank=True, null=True, on_delete=models.SET_NULL)
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar, blank=True, null=True, on_delete=models.SET_NULL
    )
    cpf = models.CharField(  # noqa DJ01
        max_length=11,
        blank=True,
        null=True,
        unique=True,
        validators=[MinLengthValidator(11)],
    )
    nao_matriculado = models.BooleanField(default=False)
    serie = models.CharField(max_length=10, blank=True, null=True)  # noqa DJ01

    responsaveis = models.ManyToManyField(
        Responsavel, blank=True, related_name="alunos"
    )

    etapa = models.PositiveSmallIntegerField(blank=True, null=True)
    ciclo = models.PositiveSmallIntegerField(blank=True, null=True)
    desc_etapa = models.CharField("Descrição etapa", max_length=50, blank=True)
    desc_ciclo = models.CharField("Descrição ciclo", max_length=50, blank=True)

    def __str__(self):
        if self.nao_matriculado:
            return f"{self.nome} - Não Matriculado"
        return f"{self.nome} - {self.codigo_eol}"

    def faixa_etaria(self, data_comparacao=date.today()) -> FaixaEtaria:
        meses = quantidade_meses(data_comparacao, self.data_nascimento)
        ultima_faixa = FaixaEtaria.objects.filter(ativo=True).order_by("fim").last()
        if meses >= ultima_faixa.fim:
            faixa = ultima_faixa
        else:
            faixa = FaixaEtaria.objects.get(
                ativo=True, inicio__lte=meses, fim__gt=meses
            )
        return faixa

    @property
    def possui_dieta_especial_ativa(self):
        return self.dietas_especiais.filter(ativo=True).exists()

    @property
    def foto_aluno_base64(self):
        try:
            novosgpservicologado = NovoSGPServicoLogado()
            response = novosgpservicologado.pegar_foto_aluno(self.codigo_eol)
            if response.status_code == status.HTTP_200_OK:
                download = response.json()["download"]
                return f'data:{download["item2"]};base64,{download["item1"]}'
            return None
        except Exception:
            return None

    def inativar_dieta_especial(self):
        try:
            dieta_especial = self.dietas_especiais.get(ativo=True)
            dieta_especial.ativo = False
            dieta_especial.save()
        except MultipleObjectsReturned:
            logger.critical("Aluno não deve possuir mais de uma Dieta Especial ativa")

    def cria_historico(self, codigo_situacao, situacao, escola=None):
        historico = HistoricoMatriculaAluno(
            aluno=self,
            escola=escola or self.escola,
            data_inicio=datetime.date.today(),
            codigo_situacao=codigo_situacao,
            situacao=situacao,
            data_fim=(
                datetime.date.today() if codigo_situacao not in [1, 6, 10, 13] else None
            ),
        )
        historico.save()
        return historico

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"


class MudancaFaixasEtarias(Justificativa, TemChaveExterna):
    faixas_etarias_ativadas = models.ManyToManyField(FaixaEtaria)


class PlanilhaEscolaDeParaCodigoEolCodigoCoade(CriadoEm, TemAlteradoEm):
    planilha = models.FileField(
        help_text="Deve ser inserido um arquivo excel em formato xlsx<br> "
        "O arquivo deve conter as colunas código eol e código codae.<br>"
        "O nome de cada coluna deve ser exatamente como a seguir:<br> "
        "<b>codigo_eol</b> e <b>codigo_unidade</b>"
    )
    codigos_codae_vinculados = models.BooleanField(
        "Códigos Codae Vinculados?", default=False, editable=False
    )

    class Meta:
        verbose_name = "Planilha De-Para: Código EOL x Código Codae"
        verbose_name_plural = "Planilhas De-Para: Código EOL x Código Codae"

    def __str__(self):
        return str(self.planilha)


class PlanilhaAtualizacaoTipoGestaoEscola(ArquivoCargaBase):
    class Meta:
        verbose_name = "Planilha Atualização Tipo Gestão Escola"
        verbose_name_plural = "Planilha Atualização Tipo Gestão Escola"

    def __str__(self):
        return str(self.conteudo)


class TipoTurma(Enum):
    REGULAR = 1
    PROGRAMAS = 3

    @classmethod
    def choices(cls):
        return tuple((t.name, t.value) for t in cls)


class AlunosMatriculadosPeriodoEscola(CriadoEm, TemAlteradoEm, TemChaveExterna):
    """Serve para guardar a quantidade de alunos matriculados da escola em um dado periodo escolar.

    Ex: EMEI BLABLA pela manhã tem 20 alunos
    """

    escola = models.ForeignKey(
        Escola,
        related_name="alunos_matriculados_por_periodo",
        on_delete=models.DO_NOTHING,
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar, related_name="alunos_matriculados", on_delete=models.DO_NOTHING
    )
    quantidade_alunos = models.PositiveSmallIntegerField(
        "Quantidade de alunos", default=0
    )

    tipo_turma = models.CharField(
        max_length=255,
        choices=TipoTurma.choices(),
        blank=True,
        default=TipoTurma.REGULAR.name,
    )

    @classmethod
    def criar(cls, escola, periodo_escolar, quantidade_alunos, tipo_turma):
        alunos_matriculados = cls.objects.filter(
            escola=escola, periodo_escolar=periodo_escolar, tipo_turma=tipo_turma
        ).first()
        if not alunos_matriculados:
            alunos_matriculados = cls.objects.create(
                escola=escola,
                periodo_escolar=periodo_escolar,
                quantidade_alunos=quantidade_alunos,
                tipo_turma=tipo_turma,
            )
        else:
            alunos_matriculados.quantidade_alunos = quantidade_alunos
            alunos_matriculados.save()

    def __str__(self):
        periodo_nome = self.periodo_escolar.nome

        return f"""Escola {self.escola.nome} do tipo {self.tipo_turma} no periodo da {periodo_nome}
        tem {self.quantidade_alunos} alunos"""

    def formata_para_relatorio(self):
        return {
            "dre": self.escola.diretoria_regional.nome,
            "lote": self.escola.lote.nome if self.escola.lote else " - ",
            "tipo_unidade": self.escola.tipo_unidade.iniciais,
            "escola": self.escola.nome,
            "periodo_escolar": self.periodo_escolar.nome,
            "tipo_turma": self.tipo_turma,
            "eh_cei": self.escola.eh_cei,
            "eh_cemei": self.escola.eh_cemei,
            "matriculados": self.quantidade_alunos,
            "alunos_por_faixa_etaria": self.escola.matriculados_por_periodo_e_faixa_etaria(),
        }

    class Meta:
        verbose_name = "Alunos Matriculados por Período e Escola"
        verbose_name_plural = "Alunos Matriculados por Períodos e Escolas"


class LogAlunosMatriculadosPeriodoEscola(TemChaveExterna, CriadoEm, TemObservacao):
    """Histórico da quantidade de Alunos por período."""

    INFANTIL_OU_FUNDAMENTAL = (
        ("N/A", "N/A"),
        ("INFANTIL", "INFANTIL"),
        ("FUNDAMENTAL", "FUNDAMENTAL"),
    )

    escola = models.ForeignKey(
        Escola,
        related_name="logs_alunos_matriculados_por_periodo",
        on_delete=models.DO_NOTHING,
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar,
        related_name="logs_alunos_matriculados",
        on_delete=models.DO_NOTHING,
    )
    quantidade_alunos = models.PositiveSmallIntegerField(
        "Quantidade de alunos", default=0
    )

    tipo_turma = models.CharField(
        max_length=255,
        choices=TipoTurma.choices(),
        blank=True,
        default=TipoTurma.REGULAR.name,
    )
    cei_ou_emei = models.CharField(max_length=4, choices=CEI_OU_EMEI, default="N/A")
    infantil_ou_fundamental = models.CharField(
        max_length=11, choices=INFANTIL_OU_FUNDAMENTAL, default="N/A"
    )

    def cria_logs_emei_em_cemei(self):
        if (
            not self.escola.eh_cemei
            or self.tipo_turma != "REGULAR"
            or (self.periodo_escolar and self.periodo_escolar.nome != "INTEGRAL")
            or self.escola.quantidade_alunos_emei_por_periodo("INTEGRAL") == 0
        ):
            return
        if not LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=self.escola,
            periodo_escolar=self.periodo_escolar,
            criado_em__year=self.criado_em.year,
            criado_em__month=self.criado_em.month,
            criado_em__day=self.criado_em.day,
            tipo_turma=self.tipo_turma,
            cei_ou_emei="EMEI",
        ).exists():
            log = LogAlunosMatriculadosPeriodoEscola.objects.create(
                escola=self.escola,
                periodo_escolar=self.periodo_escolar,
                quantidade_alunos=self.escola.quantidade_alunos_emei_por_periodo(
                    "INTEGRAL"
                ),
                tipo_turma=self.tipo_turma,
                cei_ou_emei="EMEI",
            )
            log.criado_em = self.criado_em
            log.save()

    def cria_logs_cei_em_cemei(self):
        if (
            not self.escola.eh_cemei
            or self.tipo_turma != "REGULAR"
            or self.periodo_escolar
            and self.periodo_escolar.nome != "INTEGRAL"
        ):
            return
        if not LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=self.escola,
            periodo_escolar=self.periodo_escolar,
            criado_em__year=self.criado_em.year,
            criado_em__month=self.criado_em.month,
            criado_em__day=self.criado_em.day,
            tipo_turma=self.tipo_turma,
            cei_ou_emei="CEI",
        ).exists():
            log = LogAlunosMatriculadosPeriodoEscola.objects.create(
                escola=self.escola,
                periodo_escolar=self.periodo_escolar,
                quantidade_alunos=self.escola.quantidade_alunos_cei_por_periodo(
                    "INTEGRAL"
                ),
                tipo_turma=self.tipo_turma,
                cei_ou_emei="CEI",
            )
            log.criado_em = self.criado_em
            log.save()

    def cria_logs_emebs(self, infantil_ou_fundamental):
        if not self.escola.eh_emebs or self.tipo_turma != "REGULAR":
            return
        metodo_qtd_alunos = (
            f"quantidade_alunos_emebs_por_periodo_{infantil_ou_fundamental.lower()}"
        )
        if not LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=self.escola,
            periodo_escolar=self.periodo_escolar,
            criado_em__year=self.criado_em.year,
            criado_em__month=self.criado_em.month,
            criado_em__day=self.criado_em.day,
            tipo_turma=self.tipo_turma,
            infantil_ou_fundamental=infantil_ou_fundamental,
        ).exists():
            log = LogAlunosMatriculadosPeriodoEscola.objects.create(
                escola=self.escola,
                periodo_escolar=self.periodo_escolar,
                quantidade_alunos=getattr(self.escola, metodo_qtd_alunos)(
                    self.periodo_escolar.nome
                ),
                tipo_turma=self.tipo_turma,
                infantil_ou_fundamental=infantil_ou_fundamental,
            )
            log.criado_em = self.criado_em
            log.save()

    @classmethod
    def criar(cls, escola, periodo_escolar, quantidade_alunos, data, tipo_turma):
        try:
            log = cls.objects.get(
                escola=escola,
                periodo_escolar=periodo_escolar,
                criado_em__year=data.year,
                criado_em__month=data.month,
                criado_em__day=data.day,
                tipo_turma=tipo_turma,
                cei_ou_emei="N/A",
                infantil_ou_fundamental="N/A",
            )
        except cls.DoesNotExist:
            log = cls.objects.create(
                escola=escola,
                periodo_escolar=periodo_escolar,
                quantidade_alunos=quantidade_alunos,
                tipo_turma=tipo_turma,
                cei_ou_emei="N/A",
                infantil_ou_fundamental="N/A",
            )
            log.criado_em = data
            log.save()
        log.cria_logs_emei_em_cemei()
        log.cria_logs_cei_em_cemei()
        log.cria_logs_emebs("INFANTIL")
        log.cria_logs_emebs("FUNDAMENTAL")

    def __str__(self):
        periodo_nome = self.periodo_escolar.nome

        return f"""Escola {self.escola.nome} do tipo {self.tipo_turma} no periodo da {periodo_nome}
        tem {self.quantidade_alunos} alunos no dia {self.criado_em}"""

    class Meta:
        verbose_name = "Log Alteração quantidade de alunos regular e programa"
        verbose_name_plural = (
            "Logs de Alteração quantidade de alunos regulares e de programas"
        )
        ordering = ("-criado_em",)


class DiaCalendario(CriadoEm, TemAlteradoEm, TemData, TemChaveExterna):
    SABADO = 5
    DOMINGO = 6

    escola = models.ForeignKey(
        Escola, related_name="calendario", on_delete=models.DO_NOTHING, null=True
    )
    dia_letivo = models.BooleanField("É dia Letivo?", default=True)

    @classmethod
    def existe_inclusao_continua(
        self, escola, datas_nao_letivas, periodos_escolares_alteracao
    ):
        dias_fim_de_semana = [
            data for data in datas_nao_letivas if eh_fim_de_semana(data)
        ]
        for data in dias_fim_de_semana:
            if (
                escola.inclusoes_continuas.filter(
                    status="CODAE_AUTORIZADO",
                    data_inicial__lte=data,
                    data_final__gte=data,
                    quantidades_por_periodo__periodo_escolar__in=periodos_escolares_alteracao,
                    quantidades_por_periodo__cancelado=False,
                )
                .filter(
                    Q(quantidades_por_periodo__dias_semana__icontains=self.SABADO)
                    | Q(quantidades_por_periodo__dias_semana__icontains=self.DOMINGO)
                )
                .exists()
            ):
                return True
        return False

    @classmethod
    def pelo_menos_um_dia_letivo(
        cls, escola: Escola, datas: list, alteracao: AlteracaoCardapio
    ):
        if escola.calendario.filter(data__in=datas, dia_letivo=True).exists():
            return True
        try:
            datas_nao_letivas = [
                data
                for data in datas
                if not escola.calendario.get(data=data).dia_letivo
            ]
        except DiaCalendario.DoesNotExist:
            datas_nao_letivas = datas
        periodos_escolares_alteracao = alteracao.substituicoes.values_list(
            "periodo_escolar"
        )
        if escola.grupos_inclusoes.filter(
            inclusoes_normais__cancelado=False,
            inclusoes_normais__data__in=datas_nao_letivas,
            quantidades_por_periodo__periodo_escolar__in=periodos_escolares_alteracao,
            status="CODAE_AUTORIZADO",
        ).exists():
            return True
        return cls.existe_inclusao_continua(
            escola, datas_nao_letivas, periodos_escolares_alteracao
        )

    def __str__(self) -> str:
        return f"""Dia {self.data.strftime("%d/%m/%Y")}
        {"é dia letivo" if self.dia_letivo else "não é dia letivo"} para escola {self.escola}"""

    class Meta:
        verbose_name = "Dia"
        verbose_name_plural = "Dias"
        ordering = ("data",)


class LogAtualizaDadosAluno(models.Model):
    criado_em = models.DateTimeField("Criado em", editable=False, auto_now_add=True)
    codigo_eol = models.CharField("Codigo EOL da escola", max_length=50)
    status = models.PositiveSmallIntegerField("Status da requisição", default=0)
    msg_erro = models.TextField("Mensagem erro", blank=True)

    def __str__(self):
        retorno = f'Requisicao para Escola: "#{str(self.codigo_eol)}"'
        retorno += f' na data de: "{self.criado_em}"'
        return retorno


class LogAlunosMatriculadosFaixaEtariaDia(
    TemChaveExterna, CriadoEm, TemData, TemFaixaEtariaEQuantidade
):
    """Histórico da quantidade de Alunos por faixa etária, dia, período, escola."""

    escola = models.ForeignKey(
        Escola,
        related_name="logs_alunos_matriculados_por_faixa_etaria",
        on_delete=models.DO_NOTHING,
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar,
        related_name="logs_alunos_matriculados_por_faixa_etaria",
        on_delete=models.DO_NOTHING,
    )

    def __str__(self):
        periodo_nome = self.periodo_escolar.nome

        return f"""Escola {self.escola.nome} no periodo da {periodo_nome}
        tem {self.quantidade} aluno(s) no dia {self.data} faixa etária {self.faixa_etaria}"""

    class Meta:
        verbose_name = "Log quantidade de alunos por faixa etária, dia e período"
        verbose_name_plural = (
            "Logs quantidades de alunos por faixas etárias, dias e períodos"
        )
        ordering = ("criado_em",)


class LogAlunoPorDia(TemChaveExterna, CriadoEm):
    """Relaciona log LogAlunosMatriculadosFaixaEtariaDia e Aluno."""

    log_alunos_matriculados_faixa_dia = models.ForeignKey(
        LogAlunosMatriculadosFaixaEtariaDia,
        related_name="logs_alunos_por_dia",
        on_delete=models.PROTECT,
    )
    aluno = models.ForeignKey(
        Aluno, related_name="logs_alunos_por_dia", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Log aluno por dia"
        verbose_name_plural = "Logs alunos por dia"
        ordering = ("criado_em",)


class AlunoPeriodoParcial(TemChaveExterna, CriadoEm):
    """Relaciona alunos em período parcial com a unidade educacional e a solicitação de medição inicial."""

    escola = models.ForeignKey(
        Escola, related_name="alunos_periodo_parcial", on_delete=models.PROTECT
    )
    aluno = models.ForeignKey(
        Aluno, related_name="alunos_periodo_parcial", on_delete=models.PROTECT
    )
    solicitacao_medicao_inicial = models.ForeignKey(
        "medicao_inicial.SolicitacaoMedicaoInicial",
        related_name="alunos_periodo_parcial",
        on_delete=models.CASCADE,
    )
    data = models.DateField("Aluno no período parcial a partir de", null=True)
    data_removido = models.DateField("Aluno no período parcial a partir de", null=True)

    def __str__(self):
        retorno = f"{self.aluno.nome} para SMI {self.solicitacao_medicao_inicial.mes}/"
        retorno += f"{self.solicitacao_medicao_inicial.ano} da UE {self.escola.nome}"
        retorno += f" a partir de {self.data}" if self.data else ""
        retorno += f" até {self.data_removido}" if self.data_removido else ""
        return retorno

    class Meta:
        verbose_name = "Aluno no período parcial"
        verbose_name_plural = "Alunos no período parcial"
        ordering = ("criado_em",)


class DiaSuspensaoAtividades(TemData, TemChaveExterna, CriadoEm, CriadoPor):
    tipo_unidade = models.ForeignKey(TipoUnidadeEscolar, on_delete=models.CASCADE)
    edital = models.ForeignKey(
        "terceirizada.Edital", on_delete=models.CASCADE, blank=True, null=True
    )

    @property
    def tipo_unidades(self):
        return None

    @staticmethod
    def get_dias_com_suspensao_escola(escola: Escola, quantidade_dias: int):
        hoje = datetime.date.today()
        proximos_dias_uteis = obter_dias_uteis_apos_hoje(quantidade_dias)
        dias = datetime_range(hoje, proximos_dias_uteis)
        dias_com_suspensao = DiaSuspensaoAtividades.objects.filter(
            data__in=dias,
            tipo_unidade=escola.tipo_unidade,
            edital__uuid__in=escola.editais,
        ).count()
        return dias_com_suspensao

    @staticmethod
    def get_dias_com_suspensao_solicitacao_unificada(
        dre: DiretoriaRegional, quantidade_dias: int
    ):
        hoje = datetime.date.today()
        proximos_dias_uteis = obter_dias_uteis_apos_hoje(quantidade_dias)
        dias = datetime_range(hoje, proximos_dias_uteis)
        dias_com_suspensao = 0
        for dia in dias:
            if (
                DiaSuspensaoAtividades.objects.filter(
                    data=dia, edital__uuid__in=dre.editais
                ).count()
                == TipoUnidadeEscolar.objects.count()
            ):
                dias_com_suspensao += 1
        return dias_com_suspensao

    @staticmethod
    def eh_dia_de_suspensao(escola: Escola, data: date):
        return DiaSuspensaoAtividades.objects.filter(
            data=data, tipo_unidade=escola.tipo_unidade, edital__uuid__in=escola.editais
        ).exists()

    def __str__(self):
        return f'{self.data.strftime("%d/%m/%Y")} - {self.tipo_unidade.iniciais} - Edital {self.edital}'

    class Meta:
        verbose_name = "Dia de suspensão de atividades"
        verbose_name_plural = "Dias de suspensão de atividades"
        unique_together = ("tipo_unidade", "data", "edital")
        ordering = ("data",)


class GrupoUnidadeEscolar(TemChaveExterna, Nomeavel):
    tipos_unidades = models.ManyToManyField(TipoUnidadeEscolar, blank=True)

    def todas_solicitacoes_medicao_do_grupo_aprovadas_codae(self, data, lote_uuid):
        from ..medicao_inicial.models import SolicitacaoMedicaoInicial

        escolas = Escola.objects.filter(
            tipo_unidade__in=self.tipos_unidades.all(),
            lote__uuid=lote_uuid,
            acesso_modulo_medicao_inicial=True,
            acesso_desde__lte=data,
        )
        solicitacoes_medicao_inicial = SolicitacaoMedicaoInicial.objects.filter(
            escola__tipo_unidade__in=self.tipos_unidades.all(),
            escola__lote__uuid=lote_uuid,
            escola__acesso_modulo_medicao_inicial=True,
            escola__acesso_desde__lte=data,
            mes=f"{data.month:02d}",
            ano=data.year,
            status=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        )
        todas_solicitacoes_aprovadas_codae = (
            solicitacoes_medicao_inicial.exists()
            and escolas.count() == solicitacoes_medicao_inicial.count()
        )
        return todas_solicitacoes_aprovadas_codae, solicitacoes_medicao_inicial

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Grupo de unidade escolar"
        verbose_name_plural = "Grupos de unidade escolar"
        ordering = ("nome",)


class HistoricoMatriculaAluno(TemChaveExterna):
    aluno = models.ForeignKey(
        "Aluno", on_delete=models.PROTECT, related_name="historico"
    )
    escola = models.ForeignKey(
        "Escola", on_delete=models.PROTECT, related_name="historico"
    )
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True)
    codigo_situacao = models.IntegerField()
    situacao = models.CharField(blank=True)

    class Meta:
        verbose_name = "Histórico de Matrícula do Aluno"
        verbose_name_plural = "Históricos de Matrículas dos Alunos"

    def __str__(self) -> str:
        return f"{self.aluno} - {self.escola} | De: {self.data_inicio} Ate: {self.data_fim}"
