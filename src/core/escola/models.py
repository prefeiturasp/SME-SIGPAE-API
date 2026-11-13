from __future__ import annotations

import datetime
from collections import Counter
from datetime import date

import environ
import redis
import unidecode
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q, Sum

from src.dados_comuns.constants import StringsCaminhoModelos, StringsVerboseNameModels

from ...cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ...cardapio.base.models import TipoAlimentacao
from ...dados_comuns.behaviors import (
    AcessoModuloMedicaoInicial,
    Ativavel,
    CriadoEm,
    CriadoPor,
    Iniciais,
    Nomeavel,
    Posicao,
    TemAlteradoEm,
    TemChaveExterna,
    TemCodigoEOL,
    TemData,
    TemVinculos,
)
from ...dados_comuns.constants import (
    DIRETOR_UE,
    FORMATO_DATA_BRASILEIRO,
    SOLICITACOES_DE_ALIMENTACAO,
    TIPO_UNIDADE_CEI_DIRET,
    TIPOS_ALIMENTACAO,
    TIPOS_UNIDADE_ESCOLAR,
    obter_dias_uteis_apos_hoje,
)
from ...dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from ...dados_comuns.utils import datetime_range, eh_fim_de_semana, get_ultimo_dia_mes
from ...eol_servico.utils import EOLServicoSGP, dt_nascimento_from_api
from ..aluno.models import Aluno, AlunoPeriodoParcial, FaixaEtaria, TipoTurma
from ..constants import (
    CEU_EMEF,
    CEU_EMEI,
    CIEJA,
    EMEF,
    EMEF_P_FOM,
    EMEFM,
    EMEI,
    EMEI_P_FOM,
    ESCOLA_TIPO_GESTAO_NOME,
    LISTA_TIPOS_UNIDADES,
    PERIODOS_ESPECIAIS_CEI_CEU_CCI,
    PERIODOS_ESPECIAIS_CEMEI,
)
from ..diretoria_regional.models import DiretoriaRegional
from ..utils import deletar_alunos_periodo_parcial_outras_escolas

env = environ.Env()
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")
REDIS_DB = env("REDIS_DB")
REDIS_PREFIX = env("REDIS_PREFIX")

redis_conn = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    encoding="utf-8",
    decode_responses=True,
)


class TipoUnidadeEscolar(Iniciais, Ativavel, TemChaveExterna):
    """EMEF, CIEJA, EMEI, EMEBS, CEI, CEMEI..."""

    periodos_escolares = models.ManyToManyField(
        StringsCaminhoModelos.MODEL_PERIODOESCOLAR.value,
        blank=True,
        related_name="tipos_unidade_escolar",
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
        return self.iniciais in LISTA_TIPOS_UNIDADES

    def __str__(self):
        return self.iniciais

    class Meta:
        verbose_name = "Tipo de unidade escolar"
        verbose_name_plural = "Tipos de unidade escolar"
        ordering = ("iniciais",)


class TipoGestao(Nomeavel, Ativavel, TemChaveExterna):
    """Terceirizada completa, tec mista."""

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Tipo de gestão"
        verbose_name_plural = "Tipos de gestão"


class PeriodoEscolar(Nomeavel, TemChaveExterna, Posicao):
    """manhã, intermediário, tarde, vespertino, noturno, integral."""

    tipos_alimentacao = models.ManyToManyField(
        StringsCaminhoModelos.MODEL_TIPOALIMENTACAO.value,
        related_name="periodos_escolares",
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
    Ativavel,
    TemChaveExterna,
    TemCodigoEOL,
    TemVinculos,
    AcessoModuloMedicaoInicial,
):
    acesso_desde = models.DateField(
        StringsVerboseNameModels.ACESSO_MODULO_MEDICAO_DESDE.value,
        null=True,
        blank=True,
        help_text="Define o mês a partir do qual a escola poderá realizar o lançamento da medição inicial.",
    )
    nome = models.CharField(
        StringsVerboseNameModels.NOME.value, max_length=160, blank=True
    )
    codigo_eol = models.CharField(
        StringsVerboseNameModels.CODIGO_EOL.value,
        max_length=6,
        unique=True,
        validators=[MinLengthValidator(6)],
    )
    codigo_codae = models.CharField(  # noqa: DJ01
        StringsVerboseNameModels.CODIGO_CODAE.value,
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
    endereco = models.ForeignKey(
        "dados_comuns.Endereco", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    enviar_email_por_produto = models.BooleanField(
        default=False,
        help_text="Envia e-mail quando houver um produto com status de homologado, não homologado, ativar ou suspender.",  # noqa
    )

    def historico_escola_por_data(self, data: datetime.date):
        if not data:
            return None

        return (
            self.historicos_escola.filter(
                models.Q(data_inicial__lte=data) | models.Q(data_inicial__isnull=True)
            )
            .filter(data_final__gte=data)
            .order_by("-data_inicial")
            .first()
        )

    def nome_historico(self, data: datetime.date) -> str:
        if not data:
            return self.nome

        historico = self.historico_escola_por_data(data)

        return historico.nome_escola_normalizado if historico else self.nome

    def tipo_unidade_historico(self, data: datetime.date) -> TipoUnidadeEscolar:
        if not data:
            return self.tipo_unidade

        historico = self.historico_escola_por_data(data)

        return historico.tipo_unidade if historico else self.tipo_unidade

    def esta_em_dia_letivo_sigpae(self, data: datetime.date) -> bool:
        """Indica se a escola está contemplada em um DiaLetivoSIGPAE da data.

        A escola é contemplada quando está entre as unidades do dia letivo ou,
        não havendo unidades cadastradas, quando seu tipo de unidade e lote
        estão entre os do dia letivo.
        """
        from ..dias_letivos.models import DiaLetivoSIGPAE

        if DiaLetivoSIGPAE.objects.filter(data=data, escolas=self).exists():
            return True

        return (
            DiaLetivoSIGPAE.objects.filter(data=data, escolas__isnull=True)
            .filter(
                tipos_unidade_escolar=self.tipo_unidade,
                lotes=self.lote,
            )
            .exists()
        )

    @property
    def ultimo_dia_letivo(self):
        DEZEMBRO = 12

        hoje = datetime.date.today()
        if hoje.month != DEZEMBRO:
            return None

        ultimo_dia = (
            self.calendario.filter(
                data__month=DEZEMBRO,
                data__year=hoje.year,
                dia_letivo=True,
            )
            .order_by("data")
            .last()
        )

        return ultimo_dia.data if ultimo_dia else None

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

    def periodos_escolares(
        self, ano=datetime.date.today().year, mes=None, pega_atualmente=False
    ):
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
            if pega_atualmente:
                periodos = PeriodoEscolar.objects.filter(
                    escolas_periodos__escola=self,
                    escolas_periodos__quantidade_alunos__gt=0,
                ).distinct()
            else:
                filtro_logs = self.logs_alunos_matriculados_por_periodo.filter(
                    tipo_turma="REGULAR",
                    quantidade_alunos__gte=1,
                    criado_em__year=ano,
                )
                if mes is not None:
                    filtro_logs = filtro_logs.filter(criado_em__month=mes)
                periodos = PeriodoEscolar.objects.filter(
                    id__in=filtro_logs.values_list(
                        "periodo_escolar", flat=True
                    ).distinct()
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
    def eh_cei(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in LISTA_TIPOS_UNIDADES

    @property
    def eh_cemei(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            TIPOS_UNIDADE_ESCOLAR.CEU_CEMEI.value,
            TIPOS_UNIDADE_ESCOLAR.CEMEI.value,
        ]

    @property
    def eh_emei(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            CEU_EMEI,
            EMEI,
            EMEI_P_FOM,
        ]

    @property
    def eh_emebs(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            TIPOS_UNIDADE_ESCOLAR.EMEBS.value
        ]

    @property
    def eh_ceu_gestao(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            TIPOS_UNIDADE_ESCOLAR.CEU_GESTAO.value
        ]

    @property
    def eh_emef_emei_cieja(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            EMEI,
            EMEF,
            EMEFM,
            CEU_EMEF,
            CEU_EMEI,
            CIEJA,
            EMEF_P_FOM,
            EMEI_P_FOM,
        ]

    @property
    def eh_emef(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            EMEF,
            CEU_EMEF,
            EMEFM,
            EMEF_P_FOM,
        ]

    @property
    def eh_cieja(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [CIEJA]

    @property
    def eh_cmct(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            TIPOS_UNIDADE_ESCOLAR.CMCT.value
        ]

    @property
    def eh_p_fom(self) -> bool:
        return self.tipo_unidade and self.tipo_unidade.iniciais in [
            EMEI_P_FOM,
            EMEF_P_FOM,
        ]

    def _eh_tipo_unidade_data(
        self, data: datetime.date, iniciais_validas: set[str], fallback: bool
    ) -> bool:
        """Verifica se a escola é do tipo de unidade especificado na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        if not data:
            return fallback

        historico = self.historico_escola_por_data(data)

        if historico and historico.tipo_unidade:
            return historico.tipo_unidade.iniciais in iniciais_validas

        return fallback

    def eh_cemei_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é CEMEI na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={
                TIPOS_UNIDADE_ESCOLAR.CEU_CEMEI.value,
                TIPOS_UNIDADE_ESCOLAR.CEMEI.value,
            },
            fallback=self.eh_cemei,
        )

    def eh_emei_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é EMEI na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={CEU_EMEI, EMEI, EMEI_P_FOM},
            fallback=self.eh_emei,
        )

    def eh_cei_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é CEI na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={
                TIPO_UNIDADE_CEI_DIRET,
                TIPOS_UNIDADE_ESCOLAR.CEU_CEI.value,
                TIPOS_UNIDADE_ESCOLAR.CEI.value,
                TIPOS_UNIDADE_ESCOLAR.CCI.value,
                TIPOS_UNIDADE_ESCOLAR.CCI_CIPS.value,
                TIPOS_UNIDADE_ESCOLAR.CEI_CEU.value,
            },
            fallback=self.eh_cei,
        )

    def eh_emebs_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é EMEBS na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={TIPOS_UNIDADE_ESCOLAR.EMEBS.value},
            fallback=self.eh_emebs,
        )

    def eh_ceu_gestao_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é CEU GESTAO na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={TIPOS_UNIDADE_ESCOLAR.CEU_GESTAO.value},
            fallback=self.eh_ceu_gestao,
        )

    def eh_emef_emei_cieja_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é EMEI, EMEF ou CIEJA na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={
                EMEI,
                EMEF,
                EMEFM,
                CEU_EMEF,
                CEU_EMEI,
                CIEJA,
                EMEF_P_FOM,
                EMEI_P_FOM,
            },
            fallback=self.eh_emef_emei_cieja,
        )

    def eh_emef_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é EMEF na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={EMEF, CEU_EMEF, EMEFM, EMEF_P_FOM},
            fallback=self.eh_emef,
        )

    def eh_cieja_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é CIEJA na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={CIEJA},
            fallback=self.eh_cieja,
        )

    def eh_cmct_data(self, data: datetime.date) -> bool:
        """Verifica se a escola é CMCT na data passada, considerando o histórico da escola. Se não houver histórico para a data, considera o tipo atual da escola."""
        return self._eh_tipo_unidade_data(
            data,
            iniciais_validas={TIPOS_UNIDADE_ESCOLAR.CMCT.value},
            fallback=self.eh_cmct,
        )

    @property
    def modulo_gestao(self):
        if self.tipo_gestao and self.tipo_gestao.nome == ESCOLA_TIPO_GESTAO_NOME:
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
                periodo_cei = lista_faixas.get(periodo, [])
                return_dict[periodo][TIPOS_UNIDADE_ESCOLAR.CEI.value] = periodo_cei
            except KeyError:
                return_dict[periodo][TIPOS_UNIDADE_ESCOLAR.CEI.value] = (
                    lista_faixas.get("INTEGRAL")
                )
            return_dict[periodo][EMEI] = self.quantidade_alunos_emei_por_periodo(
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
            return_dict[periodo][TIPOS_UNIDADE_ESCOLAR.CEI.value] = (
                self.quantidade_alunos_cei_por_periodo(periodo)
            )
            return_dict[periodo][EMEI] = self.quantidade_alunos_emei_por_periodo(
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

    @property
    def inclusoes_continuas(self):
        return self.inclusoes_alimentacao_continua

    def __str__(self):
        return f"{self.codigo_eol}: {self.nome}"

    def matriculados_por_periodo_e_faixa_etaria(self, data=datetime.date.today()):
        periodos = self.periodos_escolares(data.year).values_list("nome", flat=True)
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
        alunos_periodo_parcial = (
            AlunoPeriodoParcial.objects.filter(
                aluno__escola__codigo_eol=self.codigo_eol,
                solicitacao_medicao_inicial__mes=str(data_referencia.month).zfill(2),
                solicitacao_medicao_inicial__ano=str(data_referencia.year),
            )
            .filter(Q(data__isnull=True) | Q(data__lte=data_referencia))
            .filter(
                Q(data_removido__isnull=True) | Q(data_removido__gte=data_referencia)
            )
            .values_list("aluno__codigo_eol", flat=True)
        )
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

    def alunos_por_faixa_etaria(
        self, data_referencia=None, faixas_etarias=None, lista_alunos=None
    ):
        data_referencia = self.obter_data_referencia(data_referencia)
        faixas_etarias = self.obter_faixas_etarias(faixas_etarias)

        if lista_alunos is None:
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
            SOLICITACOES_DE_ALIMENTACAO in lista_medicoes
            or self.eh_cei
            or self.eh_cemei
        ):
            return lista_medicoes
        if self.solicitacoes_kit_lanche_avulsa.filter(
            status="CODAE_AUTORIZADO",
            solicitacao_kit_lanche__data__month=mes,
            solicitacao_kit_lanche__data__year=ano,
        ).exists():
            lista_medicoes.append(SOLICITACOES_DE_ALIMENTACAO)
        return lista_medicoes

    def get_lista_medicoes_kit_lanche_unificado_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if SOLICITACOES_DE_ALIMENTACAO in lista_medicoes:
            return lista_medicoes
        if self.escolaquantidade_set.filter(
            solicitacao_unificada__status="CODAE_AUTORIZADO",
            cancelado=False,
            solicitacao_unificada__solicitacao_kit_lanche__data__month=mes,
            solicitacao_unificada__solicitacao_kit_lanche__data__year=ano,
        ).exists():
            lista_medicoes.append(SOLICITACOES_DE_ALIMENTACAO)
        return lista_medicoes

    def get_lista_medicoes_kit_lanche_cei_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes
    ) -> list:
        if SOLICITACOES_DE_ALIMENTACAO in lista_medicoes or not self.eh_cei:
            return lista_medicoes
        if self.solicitacoes_kit_lanche_cei_avulsa.filter(
            status="CODAE_AUTORIZADO",
            solicitacao_kit_lanche__data__month=mes,
            solicitacao_kit_lanche__data__year=ano,
        ).exists():
            lista_medicoes.append(SOLICITACOES_DE_ALIMENTACAO)
        return lista_medicoes

    def get_lista_medicoes_kit_lanche_cemei_autorizado_no_mes(
        self, mes: int, ano: int, lista_medicoes: list
    ) -> list:
        if SOLICITACOES_DE_ALIMENTACAO in lista_medicoes or not self.eh_cemei:
            return lista_medicoes
        if self.solicitacoes_kit_lanche_cemei.filter(
            status="CODAE_AUTORIZADO", data__month=mes, data__year=ano
        ).exists():
            lista_medicoes.append(SOLICITACOES_DE_ALIMENTACAO)
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
            SOLICITACOES_DE_ALIMENTACAO in lista_medicoes
            or self.eh_cei
            or self.eh_cemei
        ):
            return lista_medicoes
        if self.alteracaocardapio_set.filter(
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=mes,
            datas_intervalo__data__year=ano,
            datas_intervalo__cancelado=False,
            motivo__nome=TIPOS_ALIMENTACAO.LANCHE_EMERGENCIAL.value,
        ).exists():
            lista_medicoes.append(SOLICITACOES_DE_ALIMENTACAO)
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
        ).exclude(motivo__nome=TIPOS_ALIMENTACAO.LANCHE_EMERGENCIAL.value)
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
        if SOLICITACOES_DE_ALIMENTACAO in lista_medicoes or not self.eh_cemei:
            return lista_medicoes
        queryset = self.alteracaocardapiocemei_set.filter(
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=mes,
            datas_intervalo__data__year=ano,
            datas_intervalo__cancelado=False,
            motivo__nome=TIPOS_ALIMENTACAO.LANCHE_EMERGENCIAL.value,
        )
        if queryset.exists():
            lista_medicoes.append(SOLICITACOES_DE_ALIMENTACAO)
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
        ).exclude(motivo__nome=TIPOS_ALIMENTACAO.LANCHE_EMERGENCIAL.value)
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


class EscolaPeriodoEscolar(Ativavel, TemChaveExterna):
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
        StringsVerboseNameModels.QUANTIDADE_DE_ALUNOS.value, default=0
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
        StringsVerboseNameModels.QUANTIDADE_DE_ALUNOS.value, default=0
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
        periodo_escolar = self.periodo_escolar.nome
        if self.escola.eh_cei:
            periodos_cei = {"MANHA": "Infantil Manhã", "TARDE": "Infantil Tarde"}
            periodo_escolar = periodos_cei.get(periodo_escolar, periodo_escolar)

        return {
            "dre": self.escola.diretoria_regional.nome,
            "lote": self.escola.lote.nome if self.escola.lote else " - ",
            "tipo_unidade": self.escola.tipo_unidade.iniciais,
            "escola": self.escola.nome,
            "periodo_escolar": periodo_escolar,
            "tipo_turma": self.tipo_turma,
            "eh_cei": self.escola.eh_cei,
            "eh_cemei": self.escola.eh_cemei,
            "matriculados": self.quantidade_alunos,
            "alunos_por_faixa_etaria": self.escola.matriculados_por_periodo_e_faixa_etaria(),
        }

    class Meta:
        verbose_name = "Alunos Matriculados por Período e Escola"
        verbose_name_plural = "Alunos Matriculados por Períodos e Escolas"


class DiaCalendario(CriadoEm, TemAlteradoEm, TemData, TemChaveExterna):
    SABADO = 5
    DOMINGO = 6

    escola = models.ForeignKey(
        Escola, related_name="calendario", on_delete=models.DO_NOTHING, null=True
    )
    periodo_escolar = models.ForeignKey(
        PeriodoEscolar,
        related_name="dias_calendario",
        on_delete=models.SET_NULL,  # mantém o DiaCalendario mesmo se o período for apagado
        null=True,
        blank=True,
    )
    dia_letivo = models.BooleanField(
        StringsVerboseNameModels.E_DIA_LETIVO.value, default=True
    )

    @classmethod
    def existe_inclusao_continua(
        cls, escola, datas_nao_letivas, periodos_escolares_alteracao
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
                    Q(quantidades_por_periodo__dias_semana__icontains=cls.SABADO)
                    | Q(quantidades_por_periodo__dias_semana__icontains=cls.DOMINGO)
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
                if not escola.calendario.get(
                    data=data, periodo_escolar__isnull=True
                ).dia_letivo
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
        return f"""Dia {self.data.strftime(FORMATO_DATA_BRASILEIRO)}
        {"é dia letivo" if self.dia_letivo else "não é dia letivo"} para escola {self.escola}"""

    class Meta:
        verbose_name = "Dia"
        verbose_name_plural = "Dias"
        ordering = ("data",)


class DiaSuspensaoAtividades(TemData, TemChaveExterna, CriadoEm, CriadoPor):
    tipo_unidade = models.ForeignKey(TipoUnidadeEscolar, on_delete=models.CASCADE)
    edital = models.ForeignKey(
        StringsCaminhoModelos.MODEL_EDITAL.value,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
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
        return f"{self.data.strftime(FORMATO_DATA_BRASILEIRO)} - {self.tipo_unidade.iniciais} - Edital {self.edital}"

    class Meta:
        verbose_name = "Dia de suspensão de atividades"
        verbose_name_plural = "Dias de suspensão de atividades"
        unique_together = ("tipo_unidade", "data", "edital")
        ordering = ("data",)


class GrupoUnidadeEscolar(TemChaveExterna, Nomeavel):
    GRUPO_1 = "Grupo 1"
    GRUPO_2 = "Grupo 2"
    GRUPO_3 = "Grupo 3"
    GRUPO_4 = "Grupo 4"
    GRUPO_5 = "Grupo 5"
    GRUPO_6 = "Grupo 6"

    tipos_unidades = models.ManyToManyField(TipoUnidadeEscolar, blank=True)

    def todas_solicitacoes_medicao_do_grupo_aprovadas_codae(self, data, lote_uuid):
        from ...medicao_inicial.models import SolicitacaoMedicaoInicial

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


class HistoricoEscola(Nomeavel, TemChaveExterna, CriadoEm, TemAlteradoEm):
    escola = models.ForeignKey(
        "Escola", on_delete=models.PROTECT, related_name="historicos_escola"
    )
    tipo_unidade = models.ForeignKey(TipoUnidadeEscolar, on_delete=models.CASCADE)
    data_inicial = models.DateField(blank=True, null=True)
    data_final = models.DateField(null=True)

    def __str__(self) -> str:
        return f"{self.escola.codigo_eol} - {self.escola.nome} -> era {self.nome} - até {self.data_final.strftime(FORMATO_DATA_BRASILEIRO)}"

    @property
    def nome_escola_normalizado(self):
        return f"{self.nome} (ATUAL {self.escola.nome})"

    class Meta:
        verbose_name = "Histórico da Escola"
        verbose_name_plural = "Históricos da escola"
