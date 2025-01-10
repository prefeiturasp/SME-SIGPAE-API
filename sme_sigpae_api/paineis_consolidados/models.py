import ast
import datetime
import operator

from django.db import models
from django.db.models import Q

from ..cardapio.api.serializers.serializers import (
    AlteracaoCardapioCEISerializer,
    AlteracaoCardapioCEMEISerializer,
    AlteracaoCardapioSerializer,
    GrupoSuspensaoAlimentacaoSerializer,
    InversaoCardapioSerializer,
    SuspensaoAlimentacaoDaCEISerializer,
)
from ..cardapio.models import (
    AlteracaoCardapio,
    AlteracaoCardapioCEI,
    AlteracaoCardapioCEMEI,
    GrupoSuspensaoAlimentacao,
    InversaoCardapio,
    SuspensaoAlimentacaoDaCEI,
)
from ..dados_comuns.behaviors import TemIdentificadorExternoAmigavel, TemPrioridade
from ..dados_comuns.constants import DAQUI_A_SETE_DIAS, DAQUI_A_TRINTA_DIAS
from ..dados_comuns.fluxo_status import (
    DietaEspecialWorkflow,
    InformativoPartindoDaEscolaWorkflow,
    PedidoAPartirDaDiretoriaRegionalWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)
from ..dados_comuns.models import LogSolicitacoesUsuario
from ..dieta_especial.models import SolicitacaoDietaEspecial
from ..escola.models import Codae, DiretoriaRegional, Escola
from ..inclusao_alimentacao.api.serializers.serializers import (
    GrupoInclusaoAlimentacaoNormalSerializer,
    InclusaoAlimentacaoContinuaSerializer,
    InclusaoAlimentacaoDaCEISerializer,
    InclusaoDeAlimentacaoCEMEISerializer,
)
from ..inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from ..kit_lanche.api.serializers.serializers import (
    SolicitacaoKitLancheAvulsaSerializer,
    SolicitacaoKitLancheCEIAvulsaSerializer,
    SolicitacaoKitLancheCEMEIRetrieveSerializer,
    SolicitacaoKitLancheUnificadaRelatorioSolicitacoesAlimentacaoSerializer,
)
from ..kit_lanche.models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEMEI,
    SolicitacaoKitLancheUnificada,
)
from ..terceirizada.models import Terceirizada


class SolicitacoesDestaSemanaManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(7)
        return (
            super(SolicitacoesDestaSemanaManager, self)
            .get_queryset()
            .filter(data_evento__range=(data_limite_inicial, data_limite_final))
        )


class SolicitacoesDesteMesManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(31)
        return (
            super(SolicitacoesDesteMesManager, self)
            .get_queryset()
            .filter(data_evento__range=(data_limite_inicial, data_limite_final))
        )


class MoldeConsolidado(models.Model, TemPrioridade, TemIdentificadorExternoAmigavel):
    """Mapeia uma sql view para um modelo django.

    Mapeia a view gerada pelos sqls (solicitacoes_consolidadas) para objetos que
    são utilizados nos paineis consolidados, principalmente no painel de Gestão de Alimentação.
    """

    PENDENTES_STATUS = []
    PENDENTES_EVENTO = []

    AUTORIZADOS_STATUS = []
    AUTORIZADOS_EVENTO = []

    CANCELADOS_STATUS = []
    CANCELADOS_EVENTO = []

    NEGADOS_STATUS = []
    NEGADOS_EVENTO = []

    PENDENTES_STATUS_DIETA_ESPECIAL = [
        DietaEspecialWorkflow.CODAE_A_AUTORIZAR,
        DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO,
    ]
    PENDENTES_EVENTO_DIETA_ESPECIAL = [
        LogSolicitacoesUsuario.INICIO_FLUXO,
        LogSolicitacoesUsuario.INICIO_FLUXO_INATIVACAO,
    ]

    AUTORIZADO_STATUS_DIETA_ESPECIAL = [
        DietaEspecialWorkflow.CODAE_AUTORIZADO,
        DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO,
        DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
        InformativoPartindoDaEscolaWorkflow.INFORMADO,
    ]
    AUTORIZADO_EVENTO_DIETA_ESPECIAL = [
        LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO,
        LogSolicitacoesUsuario.INICIO_FLUXO,
    ]

    NEGADOS_STATUS_DIETA_ESPECIAL = [
        DietaEspecialWorkflow.CODAE_NEGOU_PEDIDO,
        DietaEspecialWorkflow.CODAE_NEGOU_INATIVACAO,
        DietaEspecialWorkflow.CODAE_NEGOU_CANCELAMENTO,
    ]
    NEGADOS_EVENTO_DIETA_ESPECIAL = [
        LogSolicitacoesUsuario.CODAE_NEGOU,
        LogSolicitacoesUsuario.CODAE_NEGOU_INATIVACAO,
        LogSolicitacoesUsuario.CODAE_NEGOU_CANCELAMENTO,
    ]

    CANCELADOS_STATUS_DIETA_ESPECIAL = [
        DietaEspecialWorkflow.ESCOLA_CANCELOU,
        DietaEspecialWorkflow.CANCELADO_ALUNO_MUDOU_ESCOLA,
        DietaEspecialWorkflow.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
        DietaEspecialWorkflow.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    ]
    CANCELADOS_EVENTO_DIETA_ESPECIAL = [
        LogSolicitacoesUsuario.ESCOLA_CANCELOU,
        LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA,
        LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
        LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
    ]

    INATIVOS_STATUS_DIETA_ESPECIAL = [
        DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO,
        PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        DietaEspecialWorkflow.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
    ]
    INATIVOS_EVENTO_DIETA_ESPECIAL = [
        LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
        LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE,
    ]

    CANCELADOS_STATUS_DIETA_ESPECIAL_TEMP = [
        DietaEspecialWorkflow.CODAE_AUTORIZOU_INATIVACAO,
        DietaEspecialWorkflow.TERMINADA_AUTOMATICAMENTE_SISTEMA,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        DietaEspecialWorkflow.ESCOLA_CANCELOU,
    ]
    CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP = [
        LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
        LogSolicitacoesUsuario.TERMINADA_AUTOMATICAMENTE_SISTEMA,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    ]

    TP_SOL_TODOS = "TODOS"
    # Solicitações de Inclusão
    TP_SOL_INC_ALIMENTA = "INC_ALIMENTA"
    TP_SOL_INC_ALIMENTA_CONTINUA = "INC_ALIMENTA_CONTINUA"
    TP_SOL_INC_ALIMENTA_CEI = "INC_ALIMENTA_CEI"
    TP_SOL_INC_ALIMENTA_CEMEI = "INC_ALIMENTA_CEMEI"
    # Solcitações de Alteração
    TP_SOL_ALT_CARDAPIO = "ALT_CARDAPIO"
    TP_SOL_ALT_CARDAPIO_CEI = "ALT_CARDAPIO_CEI"
    TP_SOL_ALT_CARDAPIO_CEMEI = "ALT_CARDAPIO_CEMEI"
    # Solicitações de Kit Lanche
    TP_SOL_KIT_LANCHE_AVULSA = "KIT_LANCHE_AVULSA"
    TP_SOL_KIT_LANCHE_UNIFICADA = "KIT_LANCHE_UNIFICADA"
    TP_SOL_KIT_LANCHE_AVULSA_CEI = "KIT_LANCHE_AVULSA_CEI"
    TP_SOL_KIT_LANCHE_CEMEI = "KIT_LANCHE_CEMEI"
    # Solicitações de Suspensão
    TP_SOL_SUSP_ALIMENTACAO = "SUSP_ALIMENTACAO"
    TP_SOL_SUSP_ALIMENTACAO_CEI = "SUSP_ALIMENTACAO_CEI"
    # Solicitações de Inversão
    TP_SOL_INV_CARDAPIO = "INV_CARDAPIO"
    # Solicitações de Dieta Especial
    TP_SOL_DIETA_ESPECIAL = "DIETA_ESPECIAL"

    STATUS_TODOS = "TODOS"
    STATUS_AUTORIZADOS = "AUTORIZADOS"
    STATUS_NEGADOS = "NEGADOS"
    STATUS_CANCELADOS = "CANCELADOS"
    STATUS_PENDENTES = "RECEBIDAS"

    uuid = models.UUIDField(editable=False)
    data_evento = models.DateField()
    data_evento_2 = models.DateField()
    data_evento_fim = models.DateField()
    criado_em = models.DateTimeField()
    lote_nome = models.CharField(max_length=50)
    dre_nome = models.CharField(max_length=200)
    dre_iniciais = models.CharField(max_length=10)
    escola_nome = models.CharField(max_length=200)
    tipo_solicitacao_dieta = models.CharField(max_length=30)
    terceirizada_nome = models.CharField(max_length=200)
    nome_aluno = models.CharField(max_length=200)
    serie = models.CharField(max_length=10)
    codigo_eol_aluno = models.CharField(max_length=7)
    aluno_nao_matriculado = models.BooleanField(default=False, null=True)
    dieta_alterada_id = models.IntegerField()
    classificacao_id = models.IntegerField()
    ativo = models.BooleanField()
    em_vigencia = models.BooleanField()

    lote_uuid = models.UUIDField(editable=False)
    escola_uuid = models.UUIDField(editable=False)
    escola_tipo_unidade_uuid = models.UUIDField(editable=False)
    escola_tipo_gestao_uuid = models.UUIDField(editable=False)
    escola_destino_uuid = models.UUIDField(editable=False)
    escola_destino_id = models.IntegerField()
    escola_destino_tipo_unidade_uuid = models.UUIDField(editable=False)
    lote_escola_destino_uuid = models.UUIDField(editable=False)
    dre_uuid = models.UUIDField(editable=False)
    dre_escola_destino_uuid = models.UUIDField(editable=False)
    terceirizada_uuid = models.UUIDField(editable=False)

    tipo_doc = models.CharField(max_length=30)
    desc_doc = models.CharField(max_length=50)
    data_log = models.DateTimeField()
    status_evento = models.PositiveSmallIntegerField()
    motivo = models.CharField(max_length=100)
    numero_alunos = models.BigIntegerField()
    status_atual = models.CharField(max_length=32)

    objects = models.Manager()
    filtro_7_dias = SolicitacoesDestaSemanaManager()
    filtro_30_dias = SolicitacoesDesteMesManager()
    conferido = models.BooleanField()
    terceirizada_conferiu_gestao = models.BooleanField()

    @property
    def get_raw_model(self):
        models_de_para = {
            "DIETA_ESPECIAL": SolicitacaoDietaEspecial,
            "ALT_CARDAPIO": AlteracaoCardapio,
            "INV_CARDAPIO": InversaoCardapio,
            "INC_ALIMENTA": GrupoInclusaoAlimentacaoNormal,
            "INC_ALIMENTA_CONTINUA": InclusaoAlimentacaoContinua,
            "KIT_LANCHE_AVULSA": SolicitacaoKitLancheAvulsa,
            "SUSP_ALIMENTACAO": GrupoSuspensaoAlimentacao,
            "KIT_LANCHE_UNIFICADA": SolicitacaoKitLancheUnificada,
            "INC_ALIMENTA_CEI": InclusaoAlimentacaoDaCEI,
            "ALT_CARDAPIO_CEI": AlteracaoCardapioCEI,
            "KIT_LANCHE_AVULSA_CEI": SolicitacaoKitLancheCEIAvulsa,
            "SUSP_ALIMENTACAO_CEI": SuspensaoAlimentacaoDaCEI,
            "KIT_LANCHE_CEMEI": SolicitacaoKitLancheCEMEI,
            "INC_ALIMENTA_CEMEI": InclusaoDeAlimentacaoCEMEI,
            "ALT_CARDAPIO_CEMEI": AlteracaoCardapioCEMEI,
        }
        return models_de_para[self.tipo_doc]

    @classmethod
    def busca_por_tipo_solicitacao(cls, queryset, query_params, **kwargs):
        tipo_solicitacao = query_params.get("tipo_solicitacao")
        if not tipo_solicitacao:
            return queryset
        if tipo_solicitacao == "KIT_LANCHE":
            queryset = queryset.filter(desc_doc__icontains="Kit Lanche").exclude(
                desc_doc__icontains="Unificado"
            )
        else:
            queryset = queryset.filter(desc_doc__icontains=tipo_solicitacao)
        return queryset

    @classmethod
    def filtrar_tipo_doc(cls, queryset, query_params, **kwargs):
        if query_params.get("tipo_doc"):
            queryset = queryset.filter(tipo_doc=query_params.get("tipo_doc"))
        return queryset

    @classmethod
    def excluir_inclusoes_continuas(cls, queryset, query_params, **kwargs):
        if query_params.get("excluir_inclusoes_continuas"):
            queryset = queryset.exclude(tipo_doc="INC_ALIMENTA_CONTINUA")
        return queryset

    @classmethod
    def busca_data_evento(cls, queryset, query_params, **kwargs):
        data_evento = query_params.get("data_evento")
        if not data_evento:
            return queryset
        queryset = queryset.filter(
            Q(data_evento=data_evento)
            | Q(data_evento_2=data_evento)
            | (
                Q(data_evento_fim__isnull=False)
                & ~Q(desc_doc__icontains="Alteração")
                & Q(data_evento__lte=data_evento)
                & Q(data_evento_fim__gte=data_evento)
            )
        )
        return queryset

    @classmethod
    def busca_periodo_de_datas(cls, queryset, data_evento, data_evento_fim, **kwargs):
        filtros_inicio = Q()
        filtros_fim = Q()
        if data_evento:
            data_evento = "-".join(data_evento.split("/")[::-1])
            filtros_inicio = (
                Q(data_evento__gte=data_evento)
                | Q(data_evento_2__gte=data_evento)
                | (
                    Q(data_evento_fim__isnull=False)
                    & ~Q(desc_doc__icontains="Alteração")
                    & Q(data_evento__gte=data_evento)
                )
            )
        if data_evento_fim:
            data_evento_fim = "-".join(data_evento_fim.split("/")[::-1])
            filtros_fim = (
                Q(data_evento__lte=data_evento_fim)
                | Q(data_evento_2__lte=data_evento_fim)
                | (
                    Q(data_evento_fim__isnull=False)
                    & ~Q(desc_doc__icontains="Alteração")
                    & Q(data_evento_fim__lte=data_evento_fim)
                )
            )

        filtros = filtros_inicio & filtros_fim
        queryset = queryset.filter(filtros)
        return queryset

    @classmethod
    def map_queryset_por_tipo_doc(cls, tipo_doc, **kwargs):
        if not tipo_doc:
            return None
        mapeador = {
            "INC_ALIMENTA": [
                cls.TP_SOL_INC_ALIMENTA,
                cls.TP_SOL_INC_ALIMENTA_CONTINUA,
                cls.TP_SOL_INC_ALIMENTA_CEI,
                cls.TP_SOL_INC_ALIMENTA_CEMEI,
            ],
            "ALT_CARDAPIO": [
                cls.TP_SOL_ALT_CARDAPIO,
                cls.TP_SOL_ALT_CARDAPIO_CEI,
                cls.TP_SOL_ALT_CARDAPIO_CEMEI,
            ],
            "KIT_LANCHE_AVULSA": [
                cls.TP_SOL_KIT_LANCHE_AVULSA,
                cls.TP_SOL_KIT_LANCHE_AVULSA_CEI,
                cls.TP_SOL_KIT_LANCHE_CEMEI,
            ],
            "KIT_LANCHE_UNIFICADO": [cls.TP_SOL_KIT_LANCHE_UNIFICADA],
            "SUSP_ALIMENTACAO": [
                cls.TP_SOL_SUSP_ALIMENTACAO,
                cls.TP_SOL_SUSP_ALIMENTACAO_CEI,
            ],
            "INV_CARDAPIO": [cls.TP_SOL_INV_CARDAPIO],
        }
        lista_tipo_doc = []
        for td in tipo_doc:
            lista_tipo_doc = lista_tipo_doc + mapeador[td]
        return lista_tipo_doc

    @classmethod
    def get_class_name(cls, tipo_doc, **kwargs):
        mapeador = {
            f"{cls.TP_SOL_INC_ALIMENTA}": GrupoInclusaoAlimentacaoNormal,
            f"{cls.TP_SOL_INC_ALIMENTA_CONTINUA}": InclusaoAlimentacaoContinua,
            f"{cls.TP_SOL_INC_ALIMENTA_CEI}": InclusaoAlimentacaoDaCEI,
            f"{cls.TP_SOL_INC_ALIMENTA_CEMEI}": InclusaoDeAlimentacaoCEMEI,
            f"{cls.TP_SOL_ALT_CARDAPIO}": AlteracaoCardapio,
            f"{cls.TP_SOL_ALT_CARDAPIO_CEI}": AlteracaoCardapioCEI,
            f"{cls.TP_SOL_ALT_CARDAPIO_CEMEI}": AlteracaoCardapioCEMEI,
            f"{cls.TP_SOL_KIT_LANCHE_AVULSA}": SolicitacaoKitLancheAvulsa,
            f"{cls.TP_SOL_KIT_LANCHE_UNIFICADA}": SolicitacaoKitLancheUnificada,
            f"{cls.TP_SOL_KIT_LANCHE_AVULSA_CEI}": SolicitacaoKitLancheCEIAvulsa,
            f"{cls.TP_SOL_KIT_LANCHE_CEMEI}": SolicitacaoKitLancheCEMEI,
            f"{cls.TP_SOL_SUSP_ALIMENTACAO}": GrupoSuspensaoAlimentacao,
            f"{cls.TP_SOL_SUSP_ALIMENTACAO_CEI}": SuspensaoAlimentacaoDaCEI,
            f"{cls.TP_SOL_INV_CARDAPIO}": InversaoCardapio,
        }
        return mapeador[tipo_doc]

    @classmethod
    def get_serializer_name(cls, tipo_doc, **kwargs):
        mapeador = {
            f"{cls.TP_SOL_INC_ALIMENTA}": GrupoInclusaoAlimentacaoNormalSerializer,
            f"{cls.TP_SOL_INC_ALIMENTA_CONTINUA}": InclusaoAlimentacaoContinuaSerializer,
            f"{cls.TP_SOL_INC_ALIMENTA_CEI}": InclusaoAlimentacaoDaCEISerializer,
            f"{cls.TP_SOL_INC_ALIMENTA_CEMEI}": InclusaoDeAlimentacaoCEMEISerializer,
            f"{cls.TP_SOL_ALT_CARDAPIO}": AlteracaoCardapioSerializer,
            f"{cls.TP_SOL_ALT_CARDAPIO_CEI}": AlteracaoCardapioCEISerializer,
            f"{cls.TP_SOL_ALT_CARDAPIO_CEMEI}": AlteracaoCardapioCEMEISerializer,
            f"{cls.TP_SOL_KIT_LANCHE_AVULSA}": SolicitacaoKitLancheAvulsaSerializer,
            f"{cls.TP_SOL_KIT_LANCHE_UNIFICADA}": SolicitacaoKitLancheUnificadaRelatorioSolicitacoesAlimentacaoSerializer,
            f"{cls.TP_SOL_KIT_LANCHE_AVULSA_CEI}": SolicitacaoKitLancheCEIAvulsaSerializer,
            f"{cls.TP_SOL_KIT_LANCHE_CEMEI}": SolicitacaoKitLancheCEMEIRetrieveSerializer,
            f"{cls.TP_SOL_SUSP_ALIMENTACAO}": GrupoSuspensaoAlimentacaoSerializer,
            f"{cls.TP_SOL_SUSP_ALIMENTACAO_CEI}": SuspensaoAlimentacaoDaCEISerializer,
            f"{cls.TP_SOL_INV_CARDAPIO}": InversaoCardapioSerializer,
        }
        return mapeador[tipo_doc]

    @classmethod
    def solicitacoes_detalhadas(cls, solicitacoes, request, **kwargs):
        resultado = []
        if not solicitacoes:
            return resultado
        for str_dict in solicitacoes:
            solicitacao = ast.literal_eval(str_dict)
            class_name = cls.get_class_name(solicitacao["tipo_doc"])
            serializer_name = cls.get_serializer_name(solicitacao["tipo_doc"])
            solicitacao = class_name.objects.get(uuid=solicitacao["uuid"])
            resultado.append(
                serializer_name(
                    solicitacao, context={"request": request}, many=False
                ).data
            )
        return resultado

    @classmethod
    def busca_filtro(cls, queryset, query_params, **kwargs):
        if query_params.get("periodo"):
            data_limite = datetime.date.today() - datetime.timedelta(
                days=int(query_params.get("periodo"))
            )
            queryset = queryset.filter(data_evento__gte=data_limite)
        if query_params.get("busca"):
            queryset = queryset.filter(
                Q(uuid__icontains=query_params.get("busca"))
                | Q(desc_doc__icontains=query_params.get("busca"))
                | Q(escola_nome__icontains=query_params.get("busca"))
                | Q(escola_uuid__icontains=query_params.get("busca"))
                | Q(lote_nome__icontains=query_params.get("busca"))
                | Q(motivo__icontains=query_params.get("busca"))
            )
        if query_params.get("lote"):
            queryset = queryset.filter(lote_uuid__icontains=query_params.get("lote"))
        if query_params.get("status"):
            queryset = queryset.filter(
                terceirizada_conferiu_gestao=query_params.get("status") == "1"
            )
        if query_params.get("diretoria_regional"):
            queryset = queryset.filter(dre_uuid=query_params.get("diretoria_regional"))
        queryset = cls.excluir_inclusoes_continuas(queryset, query_params)
        queryset = cls.filtrar_tipo_doc(queryset, query_params)
        queryset = cls.busca_por_tipo_solicitacao(queryset, query_params)
        queryset = cls.busca_data_evento(queryset, query_params)
        return queryset

    @classmethod
    def busca_filtro_dietas_especiais(cls, queryset, query_params, **kwargs):
        if query_params.get("titulo"):
            queryset = queryset.filter(
                Q(uuid__icontains=query_params.get("titulo"))
                | Q(escola_nome__icontains=query_params.get("titulo"))
                | Q(lote_nome__icontains=query_params.get("titulo"))
                | Q(nome_aluno__icontains=query_params.get("titulo"))
                | Q(codigo_eol_aluno__icontains=query_params.get("titulo"))
            )
        if query_params.get("lote"):
            queryset = queryset.filter(lote_uuid__icontains=query_params.get("lote"))
        if query_params.get("status"):
            queryset = queryset.filter(conferido=query_params.get("status") == "1")
        return queryset

    @classmethod
    def get_pendentes_autorizacao(cls, **kwargs):
        raise NotImplementedError("Precisa implementar")

    @classmethod
    def get_autorizados(cls, **kwargs):
        raise NotImplementedError("Precisa implementar")

    @classmethod
    def get_negados(cls, **kwargs):
        raise NotImplementedError("Precisa implementar")

    @classmethod
    def get_cancelados(cls, **kwargs):
        raise NotImplementedError("Precisa implementar")

    @property
    def data(self):
        return self.criado_em

    @classmethod
    def _get_manager(cls, kwargs):
        filtro = kwargs.get("filtro")
        manager = cls.objects
        if filtro == DAQUI_A_SETE_DIAS:
            manager = cls.filtro_7_dias
        elif filtro == DAQUI_A_TRINTA_DIAS:
            manager = cls.filtro_30_dias
        return manager

    @classmethod
    def _filtro_data_status_tipo(  # noqa: C901
        cls,
        data_final,
        data_inicial,
        query_set,
        status_solicitacao,
        tipo_solicitacao,
    ):
        if data_inicial and data_final:
            query_set = query_set.filter(
                criado_em__date__range=(data_inicial, data_final)
            )
        if tipo_solicitacao != cls.TP_SOL_TODOS:
            query_set = query_set.filter(tipo_doc=tipo_solicitacao)
        if status_solicitacao != cls.STATUS_TODOS:
            # AUTORIZADOS|NEGADOS|CANCELADOS|RECEBIDAS|TODOS
            if status_solicitacao == cls.STATUS_AUTORIZADOS:
                query_set = query_set.filter(
                    status_atual__in=cls.AUTORIZADOS_STATUS,
                    status_evento__in=cls.AUTORIZADOS_EVENTO,
                )
            elif status_solicitacao == cls.STATUS_NEGADOS:
                query_set = query_set.filter(
                    status_evento__in=cls.NEGADOS_EVENTO,
                    status_atual__in=cls.NEGADOS_STATUS,
                )
            elif status_solicitacao == cls.STATUS_CANCELADOS:
                query_set = query_set.filter(
                    status_evento__in=cls.CANCELADOS_EVENTO,
                    status_atual__in=cls.CANCELADOS_STATUS,
                )
            elif status_solicitacao == cls.STATUS_PENDENTES:
                query_set = query_set.filter(
                    status_atual__in=cls.PENDENTES_STATUS,
                    status_evento__in=cls.PENDENTES_EVENTO,
                )
        # TODO: verificar distinct uuid junto com criado_em
        return query_set.order_by("-criado_em")

    @classmethod
    def _conta_autorizados(cls, query_set):
        return (
            query_set.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
            )
            .distinct("uuid")
            .count()
        )

    @classmethod
    def _conta_negados(cls, query_set):
        return (
            query_set.filter(
                status_evento__in=cls.NEGADOS_EVENTO,
                status_atual__in=cls.NEGADOS_STATUS,
            )
            .distinct("uuid")
            .count()
        )

    @classmethod
    def _conta_cancelados(cls, query_set):
        return (
            query_set.filter(
                status_evento__in=cls.CANCELADOS_EVENTO,
                status_atual__in=cls.CANCELADOS_STATUS,
            )
            .distinct("uuid")
            .count()
        )

    @classmethod
    def _conta_pendentes(cls, query_set):
        return (
            query_set.filter(
                status_evento__in=cls.PENDENTES_EVENTO,
                status_atual__in=cls.PENDENTES_STATUS,
            )
            .distinct("uuid")
            .count()
        )

    @classmethod
    def _conta_totais(cls, query_set, query_set_mes_passado):
        tot_autorizados = cls._conta_autorizados(query_set)
        tot_negados = cls._conta_negados(query_set)
        tot_cancelados = cls._conta_cancelados(query_set)
        tot_pendentes = cls._conta_pendentes(query_set)
        total = tot_autorizados + tot_negados + tot_cancelados + tot_pendentes
        tot_autorizados_mp = cls._conta_autorizados(query_set_mes_passado)
        tot_negados_mp = cls._conta_negados(query_set_mes_passado)
        tot_cancelados_mp = cls._conta_cancelados(query_set_mes_passado)
        tot_pendentes_mp = cls._conta_pendentes(query_set_mes_passado)
        total_mp = (
            tot_autorizados_mp + tot_negados_mp + tot_cancelados_mp + tot_pendentes_mp
        )
        return dict(
            total_autorizados=tot_autorizados,
            total_negados=tot_negados,
            total_cancelados=tot_cancelados,
            total_pendentes=tot_pendentes,
            total_mes_atual=total,
            total_autorizados_mes_passado=tot_autorizados_mp,
            total_negados_mes_passado=tot_negados_mp,
            total_cancelados_mes_passado=tot_cancelados_mp,
            total_pendentes_mes_passado=tot_pendentes_mp,
            total_mes_passado=total_mp,
        )

    @staticmethod
    def classe_por_tipo_usuario(tipo_obj_instituicao):
        map_ = {
            Escola: SolicitacoesEscola,
            DiretoriaRegional: SolicitacoesDRE,
            Codae: SolicitacoesCODAE,
            Terceirizada: SolicitacoesTerceirizada,
        }
        return map_[tipo_obj_instituicao]

    class Meta:
        managed = False
        db_table = "solicitacoes_consolidadas"
        abstract = True


class SolicitacoesNutrisupervisao(MoldeConsolidado):
    #
    # Filtros padrão
    #

    PENDENTES_STATUS = [
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
    ]
    PENDENTES_EVENTO = [
        LogSolicitacoesUsuario.DRE_VALIDOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
    ]

    AUTORIZADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        InformativoPartindoDaEscolaWorkflow.INFORMADO,
    ]
    AUTORIZADOS_EVENTO = [
        LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.INICIO_FLUXO,
    ]

    CANCELADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU,
        PedidoAPartirDaDiretoriaRegionalWorkflow.DRE_CANCELOU,
    ]
    CANCELADOS_EVENTO = [
        LogSolicitacoesUsuario.DRE_CANCELOU,
        LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    ]

    NEGADOS_STATUS = [PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO]
    NEGADOS_EVENTO = [LogSolicitacoesUsuario.CODAE_NEGOU]

    @classmethod
    def get_pendentes_autorizacao(cls, **kwargs):
        manager = cls._get_manager(kwargs)
        return (
            manager.filter(
                (
                    Q(status_evento__in=cls.PENDENTES_EVENTO)
                    & Q(status_atual__in=cls.PENDENTES_STATUS)
                )
                | (
                    Q(desc_doc="Kit Lanche Unificado")
                    & Q(status_atual="CODAE_A_AUTORIZAR")
                )
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct("data_log")
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.NEGADOS_EVENTO,
                status_atual__in=cls.NEGADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.CANCELADOS_EVENTO,
                status_atual__in=cls.CANCELADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )


class SolicitacoesNutrimanifestacao(MoldeConsolidado):
    #
    # Filtros padrão
    #

    AUTORIZADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        InformativoPartindoDaEscolaWorkflow.INFORMADO,
    ]
    AUTORIZADOS_EVENTO = [
        LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.INICIO_FLUXO,
    ]

    CANCELADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU,
        PedidoAPartirDaDiretoriaRegionalWorkflow.DRE_CANCELOU,
    ]
    CANCELADOS_EVENTO = [
        LogSolicitacoesUsuario.DRE_CANCELOU,
        LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    ]

    NEGADOS_STATUS = [PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO]
    NEGADOS_EVENTO = [LogSolicitacoesUsuario.CODAE_NEGOU]

    @classmethod
    def get_autorizados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.NEGADOS_EVENTO,
                status_atual__in=cls.NEGADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.CANCELADOS_EVENTO,
                status_atual__in=cls.CANCELADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )


class SolicitacoesCODAE(MoldeConsolidado):
    #
    # Filtros padrão
    #

    PENDENTES_STATUS = [
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
    ]
    PENDENTES_EVENTO = [
        LogSolicitacoesUsuario.DRE_VALIDOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
    ]

    AUTORIZADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        InformativoPartindoDaEscolaWorkflow.INFORMADO,
    ]
    AUTORIZADOS_EVENTO = [
        LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.INICIO_FLUXO,
    ]

    CANCELADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU,
        PedidoAPartirDaDiretoriaRegionalWorkflow.DRE_CANCELOU,
    ]
    CANCELADOS_EVENTO = [
        LogSolicitacoesUsuario.DRE_CANCELOU,
        LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    ]

    NEGADOS_STATUS = [PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO]
    NEGADOS_EVENTO = [LogSolicitacoesUsuario.CODAE_NEGOU]

    @classmethod
    def get_pendentes_dieta_especial(cls, **kwargs):
        return (
            cls.objects.filter(
                status_atual__in=cls.PENDENTES_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.PENDENTES_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados_dieta_especial(cls, **kwargs):
        return (
            cls.objects.filter(
                Q(em_vigencia=True) | Q(em_vigencia__isnull=True),
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                ativo=True,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados_dieta_especial(cls, **kwargs):
        return (
            cls.objects.filter(
                status_atual__in=cls.NEGADOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.NEGADOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados_dieta_especial(cls, **kwargs):
        return (
            cls.objects.filter(
                Q(
                    tipo_solicitacao_dieta="ALTERACAO_UE",
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL_TEMP,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP,
                )
                | Q(
                    tipo_solicitacao_dieta="COMUM",
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL,
                ),
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizadas_temporariamente_dieta_especial(cls, **kwargs):
        return (
            cls.objects.filter(
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=False,
                em_vigencia=False,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_temporariamente_dieta_especial(cls, **kwargs):
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                dieta_alterada__isnull=False, tipo_solicitacao="ALTERACAO_UE"
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        return (
            cls.objects.filter(
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                tipo_solicitacao_dieta="COMUM",
                ativo=False,
                id__in=ids_alterados,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_dieta_especial(cls, **kwargs):
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                dieta_alterada__isnull=False, tipo_solicitacao="ALTERACAO_UE"
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        return (
            cls.objects.filter(
                ~Q(id__in=ids_alterados),
                status_atual__in=cls.INATIVOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.INATIVOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                tipo_solicitacao_dieta="COMUM",
                ativo=False,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_pendentes_autorizacao(cls, **kwargs):
        manager = cls._get_manager(kwargs)
        return (
            manager.filter(
                (
                    Q(status_evento__in=cls.PENDENTES_EVENTO)
                    & Q(status_atual__in=cls.PENDENTES_STATUS)
                )
                | (
                    Q(desc_doc="Kit Lanche Unificado")
                    & Q(status_atual="CODAE_A_AUTORIZAR")
                )
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct("data_log")
            .order_by("-data_log")
        )

    @classmethod
    def get_recebidas(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
                data_evento__lte=datetime.date.today(),
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.NEGADOS_EVENTO,
                status_atual__in=cls.NEGADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados(cls, **kwargs):
        return (
            cls.objects.filter(
                status_evento__in=cls.CANCELADOS_EVENTO,
                status_atual__in=cls.CANCELADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_questionamentos(cls, **kwargs):
        return (
            cls.objects.filter(
                status_atual=PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
                status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU,
            )
            .distinct()
            .order_by("-data_log")
        )

    #
    # Filtros consolidados
    #

    @classmethod  # noqa C901
    def filtros_codae(cls, **kwargs):
        # TODO: melhorar esse código, está complexo.
        escola_uuid = kwargs.get("escola_uuid")
        dre_uuid = kwargs.get("dre_uuid")
        data_inicial = kwargs.get("data_inicial", None)
        data_final = kwargs.get("data_final", None)
        tipo_solicitacao = kwargs.get("tipo_solicitacao", cls.TP_SOL_TODOS)
        status_solicitacao = kwargs.get("status_solicitacao", cls.STATUS_TODOS)
        queryset = cls.objects.all()
        if escola_uuid != "TODOS":
            queryset = queryset.filter(escola_uuid=escola_uuid)
        if dre_uuid != "TODOS":
            queryset = queryset.filter(dre_uuid=dre_uuid)
        return cls._filtro_data_status_tipo(
            data_final, data_inicial, queryset, status_solicitacao, tipo_solicitacao
        )

    @classmethod
    def get_solicitacoes_ano_corrente(cls, **kwargs):
        """Usado para geração do gráfico."""
        return (
            cls.objects.filter(criado_em__year=datetime.date.today().year)
            .distinct("uuid")
            .values("criado_em__month", "desc_doc")
        )

    @classmethod
    def resumo_totais_mes(cls, **kwargs):
        hoje = datetime.date.today()
        mes_passado = datetime.date(
            year=hoje.year, month=hoje.month, day=1
        ) - datetime.timedelta(days=1)
        query_set = cls.objects.filter(
            criado_em__date__year=hoje.year,
            criado_em__date__month=hoje.month,
        )
        query_set_mes_passado = cls.objects.filter(
            criado_em__date__year=mes_passado.year,
            criado_em__date__month=mes_passado.month,
        )

        return cls._conta_totais(query_set, query_set_mes_passado)

    @classmethod
    def map_queryset_por_status(cls, status, **kwargs):
        if not status:
            return cls.objects.all()
        mapeador = {
            "AUTORIZADOS": "cls.get_autorizados()",
            "CANCELADOS": "cls.get_cancelados()",
            "NEGADOS": "cls.get_negados()",
            "RECEBIDAS": "cls.get_recebidas()",
            "DIETAS_AUTORIZADAS": "cls.get_autorizados_dieta_especial()",
        }
        return eval(mapeador[status])  # nosec


class SolicitacoesEscola(MoldeConsolidado):
    #
    # Filtros padrão
    #

    PENDENTES_STATUS = [
        PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
        PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        # TODO: Bruno. remover essa parte de dieta especial depois da entrega da sprint
        DietaEspecialWorkflow.CODAE_A_AUTORIZAR,
    ]
    PENDENTES_EVENTO = [
        LogSolicitacoesUsuario.INICIO_FLUXO,
        LogSolicitacoesUsuario.DRE_VALIDOU,
        LogSolicitacoesUsuario.CODAE_QUESTIONOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        # TODO: Bruno. remover essa parte de dieta especial depois da entrega da sprint
        LogSolicitacoesUsuario.DIETA_ESPECIAL,
    ]

    AUTORIZADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        InformativoPartindoDaEscolaWorkflow.INFORMADO,
    ]
    AUTORIZADOS_EVENTO = [
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        LogSolicitacoesUsuario.INICIO_FLUXO,
    ]

    CANCELADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU,
        PedidoAPartirDaDiretoriaRegionalWorkflow.DRE_CANCELOU,
    ]
    CANCELADOS_EVENTO = [
        LogSolicitacoesUsuario.DRE_CANCELOU,
        LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    ]

    NEGADOS_STATUS = [
        PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO,
        PedidoAPartirDaEscolaWorkflow.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
    ]
    NEGADOS_EVENTO = [
        LogSolicitacoesUsuario.CODAE_NEGOU,
        LogSolicitacoesUsuario.DRE_NAO_VALIDOU,
    ]

    @classmethod
    def get_pendentes_dieta_especial(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(
                escola_uuid=escola_uuid,
                status_atual__in=cls.PENDENTES_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.PENDENTES_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados_dieta_especial(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        escola_destino = Escola.objects.get(uuid=escola_uuid)

        # Mantive o comportamento normal para as solicitações
        # que não são de alteração de UE.
        solicitacoes_em_vigencia_e_ativas = cls.objects.filter(
            Q(em_vigencia=True) | Q(em_vigencia__isnull=True),
            escola_destino_id=escola_destino.id,
            escola_uuid=escola_uuid,
            status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
            status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
            tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            ativo=True,
        )

        solicitacoes_de_alteracao_para_escola_de_origem = cls.objects.filter(
            Q(em_vigencia=False) | Q(em_vigencia=True, ativo=True),
            escola_uuid=escola_uuid,
            status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
            status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
            tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            dieta_alterada_id__isnull=False,
        )

        solicitacoes = (
            solicitacoes_em_vigencia_e_ativas
            | solicitacoes_de_alteracao_para_escola_de_origem
        )
        return solicitacoes.distinct().order_by("-data_log")

    @classmethod
    def get_negados_dieta_especial(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(
                escola_uuid=escola_uuid,
                status_atual__in=cls.NEGADOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.NEGADOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados_dieta_especial(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        escola_destino = Escola.objects.get(uuid=escola_uuid)
        return (
            cls.objects.filter(
                Q(
                    Q(escola_uuid=escola_uuid) | Q(escola_destino_id=escola_destino.id),
                    tipo_solicitacao_dieta="ALTERACAO_UE",
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL_TEMP,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP,
                )
                | Q(
                    tipo_solicitacao_dieta__in=["COMUM", "ALUNO_NAO_MATRICULADO"],
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL,
                    escola_uuid=escola_uuid,
                )
                | Q(
                    tipo_solicitacao_dieta="CANCELAMENTO_DIETA",
                    status_atual=DietaEspecialWorkflow.ESCOLA_CANCELOU,
                    status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
                    escola_uuid=escola_uuid,
                ),
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizadas_temporariamente_dieta_especial(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        escola_destino = Escola.objects.get(uuid=escola_uuid)
        return (
            cls.objects.filter(
                escola_destino_id=escola_destino.id,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=False,
                em_vigencia=True,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_aguardando_vigencia_dieta_especial(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        escola_destino = Escola.objects.get(uuid=escola_uuid)
        return (
            cls.objects.filter(
                escola_destino_id=escola_destino.id,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=False,
                em_vigencia=False,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_temporariamente_dieta_especial(cls, **kwargs):
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                dieta_alterada__isnull=False, tipo_solicitacao="ALTERACAO_UE"
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(
                escola_uuid=escola_uuid,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                tipo_solicitacao_dieta="COMUM",
                ativo=False,
                id__in=ids_alterados,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_dieta_especial(cls, **kwargs):
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                dieta_alterada__isnull=False, tipo_solicitacao="ALTERACAO_UE"
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(
                escola_uuid=escola_uuid,
                status_atual__in=cls.INATIVOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.INATIVOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=True,
                ativo=False,
            )
            .exclude(id__in=ids_alterados)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_pendentes_autorizacao(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(escola_uuid=escola_uuid)
            .filter(
                status_atual__in=cls.PENDENTES_STATUS,
                status_evento__in=cls.PENDENTES_EVENTO,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_recebidas(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
                escola_uuid=escola_uuid,
                data_evento__lte=datetime.date.today(),
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados(cls, **kwargs):
        from django.db.models import Q

        from sme_sigpae_api.kit_lanche.models import SolicitacaoKitLancheUnificada

        escola_uuid = kwargs.get("escola_uuid")
        uuids_solicitacao_unificadas = SolicitacaoKitLancheUnificada.objects.filter(
            escolas_quantidades__escola__uuid=escola_uuid,
            escolas_quantidades__cancelado=False,
        ).values_list("uuid", flat=True)
        return (
            cls.objects.filter(
                Q(escola_uuid=escola_uuid) | Q(uuid__in=uuids_solicitacao_unificadas),
                status_atual__in=cls.AUTORIZADOS_STATUS,
                status_evento__in=cls.AUTORIZADOS_EVENTO,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.NEGADOS_EVENTO,
                status_atual__in=cls.NEGADOS_STATUS,
                escola_uuid=escola_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados(cls, **kwargs):
        from django.db.models import Q

        from sme_sigpae_api.kit_lanche.models import SolicitacaoKitLancheUnificada

        escola_uuid = kwargs.get("escola_uuid")
        uuids_solicitacao_unificadas = SolicitacaoKitLancheUnificada.objects.filter(
            escolas_quantidades__escola__uuid=escola_uuid
        ).values_list("uuid", flat=True)
        cancelados = (
            cls.objects.filter(
                Q(escola_uuid=escola_uuid) | Q(uuid__in=uuids_solicitacao_unificadas),
                status_evento__in=cls.CANCELADOS_EVENTO,
                status_atual__in=cls.CANCELADOS_STATUS,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )
        uuids_solicitacao_unificadas_canceladas_parcialmente = (
            SolicitacaoKitLancheUnificada.objects.filter(
                escolas_quantidades__escola__uuid=escola_uuid,
                escolas_quantidades__cancelado=True,
            ).values_list("uuid", flat=True)
        )
        kit_lanche_unificados_parcialmente_cancelados = (
            cls.objects.filter(
                uuid__in=uuids_solicitacao_unificadas_canceladas_parcialmente,
                status_atual__in=cls.AUTORIZADOS_STATUS,
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                tipo_doc=cls.TP_SOL_KIT_LANCHE_UNIFICADA,
            )
            .distinct()
            .order_by("-data_log")
        )
        return cancelados | kit_lanche_unificados_parcialmente_cancelados

    #
    # Filtros consolidados
    #

    @classmethod
    def get_solicitacoes_ano_corrente(cls, **kwargs):
        """Usado para geração do gráfico."""
        escola_uuid = kwargs.get("escola_uuid")
        return (
            cls.objects.filter(
                escola_uuid=escola_uuid, criado_em__year=datetime.date.today().year
            )
            .distinct("uuid")
            .values("criado_em__month", "desc_doc")
        )

    @classmethod  # noqa C901
    def filtros_escola(cls, **kwargs):
        # TODO: melhorar esse código, está complexo.
        escola_uuid = kwargs.get("escola_uuid")
        data_inicial = kwargs.get("data_inicial", None)
        data_final = kwargs.get("data_final", None)
        tipo_solicitacao = kwargs.get("tipo_solicitacao", cls.TP_SOL_TODOS)
        status_solicitacao = kwargs.get("status_solicitacao", cls.STATUS_TODOS)

        query_set = cls.objects.filter(escola_uuid=escola_uuid)

        return cls._filtro_data_status_tipo(
            data_final, data_inicial, query_set, status_solicitacao, tipo_solicitacao
        )

    @classmethod
    def resumo_totais_mes(cls, **kwargs):
        escola_uuid = kwargs.get("escola_uuid")
        hoje = datetime.date.today()
        mes_passado = datetime.date(
            year=hoje.year, month=hoje.month, day=1
        ) - datetime.timedelta(days=1)
        query_set = cls.objects.filter(
            escola_uuid=escola_uuid,
            criado_em__date__year=hoje.year,
            criado_em__date__month=hoje.month,
        )
        query_set_mes_passado = cls.objects.filter(
            escola_uuid=escola_uuid,
            criado_em__date__year=mes_passado.year,
            criado_em__date__month=mes_passado.month,
        )

        return cls._conta_totais(query_set, query_set_mes_passado)

    @classmethod
    def map_queryset_por_status(cls, status, **kwargs):
        escola_uuid = kwargs.get("instituicao_uuid")
        if not status:
            return cls.objects.all()
        mapeador = {
            "AUTORIZADOS": f'cls.get_autorizados(escola_uuid="{escola_uuid}")',
            "CANCELADOS": f'cls.get_cancelados(escola_uuid="{escola_uuid}")',
            "NEGADOS": f'cls.get_negados(escola_uuid="{escola_uuid}")',
            "RECEBIDAS": f'cls.get_recebidas(escola_uuid="{escola_uuid}")',
            "DIETAS_AUTORIZADAS": f'cls.get_autorizados_dieta_especial(escola_uuid="{escola_uuid}")',
        }
        return eval(mapeador[status])  # nosec


class SolicitacoesDRE(MoldeConsolidado):
    #
    # Filtros padrão
    #

    PENDENTES_STATUS = [
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
        PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
    ]
    PENDENTES_EVENTO = [
        LogSolicitacoesUsuario.DRE_VALIDOU,
        LogSolicitacoesUsuario.INICIO_FLUXO,
        LogSolicitacoesUsuario.CODAE_QUESTIONOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
    ]

    AUTORIZADOS_STATUS = [
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_AUTORIZADO,
        PedidoAPartirDaDiretoriaRegionalWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
        InformativoPartindoDaEscolaWorkflow.INFORMADO,
    ]
    AUTORIZADOS_EVENTO = [
        LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
        LogSolicitacoesUsuario.INICIO_FLUXO,
    ]

    CANCELADOS_STATUS = [
        PedidoAPartirDaDiretoriaRegionalWorkflow.DRE_CANCELOU,
        PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU,
    ]
    CANCELADOS_EVENTO = [
        LogSolicitacoesUsuario.DRE_CANCELOU,
        LogSolicitacoesUsuario.ESCOLA_CANCELOU,
    ]

    NEGADOS_STATUS = [
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_NEGOU_PEDIDO,
        PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO,
        PedidoAPartirDaEscolaWorkflow.DRE_NAO_VALIDOU_PEDIDO_ESCOLA,
    ]
    NEGADOS_EVENTO = [
        LogSolicitacoesUsuario.CODAE_NEGOU,
        LogSolicitacoesUsuario.DRE_NAO_VALIDOU,
    ]

    AGUARDANDO_CODAE_STATUS = [
        PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
        PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
        PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
    ]
    AGUARDANDO_CODAE_EVENTO = [
        LogSolicitacoesUsuario.DRE_VALIDOU,
        LogSolicitacoesUsuario.CODAE_QUESTIONOU,
        LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
        LogSolicitacoesUsuario.INICIO_FLUXO,
    ]

    @classmethod
    def get_pendentes_dieta_especial(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                dre_uuid=dre_uuid,
                status_atual__in=cls.PENDENTES_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.PENDENTES_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados_dieta_especial(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        eh_relatorio_dietas_autorizadas = kwargs.get("eh_relatorio_dietas_autorizadas")
        objects_filtrados = cls.objects.filter(
            Q(em_vigencia=True) | Q(em_vigencia__isnull=True),
            status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
            status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
            tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            ativo=True,
        )
        if eh_relatorio_dietas_autorizadas:
            objects_filtrados = objects_filtrados.filter(
                dre_escola_destino_uuid=dre_uuid
            )
        else:
            objects_filtrados = objects_filtrados.filter(dre_uuid=dre_uuid)
        return objects_filtrados.distinct().order_by("-data_log")

    @classmethod
    def get_negados_dieta_especial(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                dre_uuid=dre_uuid,
                status_atual__in=cls.NEGADOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.NEGADOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados_dieta_especial(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                Q(
                    tipo_solicitacao_dieta="ALTERACAO_UE",
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL_TEMP,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP,
                )
                | Q(
                    tipo_solicitacao_dieta="COMUM",
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL,
                ),
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dre_uuid=dre_uuid,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizadas_temporariamente_dieta_especial(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                dre_uuid=dre_uuid,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=False,
                em_vigencia=False,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_temporariamente_dieta_especial(cls, **kwargs):
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                dieta_alterada__isnull=False, tipo_solicitacao="ALTERACAO_UE"
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                dre_uuid=dre_uuid,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                tipo_solicitacao_dieta="COMUM",
                ativo=False,
                id__in=ids_alterados,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_dieta_especial(cls, **kwargs):
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                dieta_alterada__isnull=False, tipo_solicitacao="ALTERACAO_UE"
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                dre_uuid=dre_uuid,
                status_atual__in=cls.INATIVOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.INATIVOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=True,
                ativo=False,
            )
            .exclude(id__in=ids_alterados)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_pendentes_autorizacao(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                status_atual__in=cls.PENDENTES_STATUS,
                status_evento__in=cls.PENDENTES_EVENTO,
                dre_uuid=dre_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_pendentes_validacao(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        manager = cls._get_manager(kwargs)
        return (
            manager.filter(
                status_atual=PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
                status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
                dre_uuid=dre_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_aguardando_codae(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.AGUARDANDO_CODAE_EVENTO,
                status_atual__in=cls.AGUARDANDO_CODAE_STATUS,
                dre_uuid=dre_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_recebidas(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
                dre_uuid=dre_uuid,
                data_evento__lte=datetime.date.today(),
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
                dre_uuid=dre_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.NEGADOS_EVENTO,
                status_atual__in=cls.NEGADOS_STATUS,
                dre_uuid=dre_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.CANCELADOS_EVENTO,
                status_atual__in=cls.CANCELADOS_STATUS,
                dre_uuid=dre_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    #
    # Filtros  consolidados
    #

    @classmethod  # noqa C901
    def filtros_dre(cls, **kwargs):
        # TODO: melhorar esse código, está complexo.
        dre_uuid = kwargs.get("dre_uuid")
        escola_uuid = kwargs.get("escola_uuid")
        data_inicial = kwargs.get("data_inicial", None)
        data_final = kwargs.get("data_final", None)
        tipo_solicitacao = kwargs.get("tipo_solicitacao", cls.TP_SOL_TODOS)
        status_solicitacao = kwargs.get("status_solicitacao", cls.STATUS_TODOS)
        query_set = cls.objects.filter(dre_uuid=dre_uuid)
        if escola_uuid != "TODOS":
            query_set = query_set.filter(
                escola_uuid=escola_uuid,
            )
        return cls._filtro_data_status_tipo(
            data_final, data_inicial, query_set, status_solicitacao, tipo_solicitacao
        )

    @classmethod
    def get_solicitacoes_ano_corrente(cls, **kwargs):
        """Usado para geração do gráfico."""
        dre_uuid = kwargs.get("dre_uuid")
        return (
            cls.objects.filter(
                dre_uuid=dre_uuid, criado_em__year=datetime.date.today().year
            )
            .distinct("uuid")
            .values("criado_em__month", "desc_doc")
        )

    @classmethod
    def resumo_totais_mes(cls, **kwargs):
        dre_uuid = kwargs.get("dre_uuid")
        hoje = datetime.date.today()
        mes_passado = datetime.date(
            year=hoje.year, month=hoje.month, day=1
        ) - datetime.timedelta(days=1)
        query_set = cls.objects.filter(
            dre_uuid=dre_uuid,
            criado_em__date__year=hoje.year,
            criado_em__date__month=hoje.month,
        ).distinct("uuid")
        query_set_mes_passado = cls.objects.filter(
            dre_uuid=dre_uuid,
            criado_em__date__year=mes_passado.year,
            criado_em__date__month=mes_passado.month,
        ).distinct("uuid")

        return cls._conta_totais(query_set, query_set_mes_passado)

    @classmethod
    def map_queryset_por_status(cls, status, **kwargs):
        dre_uuid = kwargs.get("instituicao_uuid")
        if not status:
            return cls.objects.all()
        mapeador = {
            "AUTORIZADOS": f'cls.get_autorizados(dre_uuid="{dre_uuid}")',
            "CANCELADOS": f'cls.get_cancelados(dre_uuid="{dre_uuid}")',
            "NEGADOS": f'cls.get_negados(dre_uuid="{dre_uuid}")',
            "RECEBIDAS": f'cls.get_recebidas(dre_uuid="{dre_uuid}")',
            "DIETAS_AUTORIZADAS": f'cls.get_autorizados_dieta_especial(dre_uuid="{dre_uuid}", eh_relatorio_dietas_autorizadas={True})',
        }
        return eval(mapeador[status])  # nosec


# TODO: voltar quando tiver o Rastro implementado
class SolicitacoesTerceirizada(MoldeConsolidado):
    @classmethod
    def get_pendentes_dieta_especial(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                terceirizada_uuid=terceirizada_uuid,
                status_atual__in=cls.PENDENTES_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.PENDENTES_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizados_dieta_especial(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                Q(em_vigencia=True) | Q(em_vigencia__isnull=True),
                terceirizada_uuid=terceirizada_uuid,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                ativo=True,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados_dieta_especial(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                terceirizada_uuid=terceirizada_uuid,
                status_atual__in=cls.NEGADOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.NEGADOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados_dieta_especial(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                Q(
                    tipo_solicitacao_dieta="ALTERACAO_UE",
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL_TEMP,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL_TEMP,
                )
                | Q(
                    tipo_solicitacao_dieta="COMUM",
                    status_atual__in=cls.CANCELADOS_STATUS_DIETA_ESPECIAL,
                    status_evento__in=cls.CANCELADOS_EVENTO_DIETA_ESPECIAL,
                ),
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                terceirizada_uuid=terceirizada_uuid,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_autorizadas_temporariamente_dieta_especial(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                terceirizada_uuid=terceirizada_uuid,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=False,
                em_vigencia=True,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_aguardando_vigencia_dieta_especial(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                terceirizada_uuid=terceirizada_uuid,
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=False,
                em_vigencia=False,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_temporariamente_dieta_especial(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                rastro_terceirizada__uuid=terceirizada_uuid,
                dieta_alterada__isnull=False,
                tipo_solicitacao="ALTERACAO_UE",
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        return (
            cls.objects.filter(
                status_atual__in=cls.AUTORIZADO_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.AUTORIZADO_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                tipo_solicitacao_dieta="COMUM",
                ativo=False,
                id__in=ids_alterados,
            )
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_inativas_dieta_especial(cls, **kwargs):
        qs = (
            SolicitacaoDietaEspecial.objects.filter(
                dieta_alterada__isnull=False, tipo_solicitacao="ALTERACAO_UE"
            )
            .only("dieta_alterada_id")
            .values("dieta_alterada_id")
        )
        ids_alterados = [s["dieta_alterada_id"] for s in qs]
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                terceirizada_uuid=terceirizada_uuid,
                status_atual__in=cls.INATIVOS_STATUS_DIETA_ESPECIAL,
                status_evento__in=cls.INATIVOS_EVENTO_DIETA_ESPECIAL,
                tipo_doc=cls.TP_SOL_DIETA_ESPECIAL,
                dieta_alterada_id__isnull=True,
                ativo=False,
            )
            .exclude(id__in=ids_alterados)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_questionamentos(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return cls.objects.filter(
            terceirizada_uuid=terceirizada_uuid,
            status_atual=PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU,
        ).order_by("-data_log")

    @classmethod
    def get_pendentes_autorizacao(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        s = cls.objects.filter(
            terceirizada_uuid=terceirizada_uuid,
            status_atual__in=[
                PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
                PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
                PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
                PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
            ],
            status_evento__in=[
                LogSolicitacoesUsuario.DRE_VALIDOU,
                LogSolicitacoesUsuario.INICIO_FLUXO,
                LogSolicitacoesUsuario.CODAE_QUESTIONOU,
                LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
            ],
        ).distinct("uuid")
        return sorted(s, key=operator.attrgetter("data_log"), reverse=True)

    @classmethod
    def get_autorizados(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                status_evento__in=[
                    LogSolicitacoesUsuario.CODAE_AUTORIZOU,
                    LogSolicitacoesUsuario.INICIO_FLUXO,
                    LogSolicitacoesUsuario.TERCEIRIZADA_TOMOU_CIENCIA,
                ],
                status_atual__in=[
                    PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
                    PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                    InformativoPartindoDaEscolaWorkflow.INFORMADO,
                ],
                terceirizada_uuid=terceirizada_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_negados(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                status_evento=LogSolicitacoesUsuario.CODAE_NEGOU,
                status_atual=PedidoAPartirDaEscolaWorkflow.CODAE_NEGOU_PEDIDO,
                terceirizada_uuid=terceirizada_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def get_cancelados(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                status_evento__in=[
                    LogSolicitacoesUsuario.DRE_CANCELOU,
                    LogSolicitacoesUsuario.ESCOLA_CANCELOU,
                ],
                status_atual__in=[
                    PedidoAPartirDaEscolaWorkflow.ESCOLA_CANCELOU,
                    PedidoAPartirDaDiretoriaRegionalWorkflow.DRE_CANCELOU,
                ],
                terceirizada_uuid=terceirizada_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .order_by("-data_log")
            .distinct()
        )

    @classmethod
    def get_pendentes_ciencia(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        manager = cls._get_manager(kwargs)
        return (
            manager.filter(
                status_atual__in=[
                    PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_AUTORIZADO,
                    PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
                    PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
                    InformativoPartindoDaEscolaWorkflow.INFORMADO,
                ],
                status_evento__in=[
                    LogSolicitacoesUsuario.CODAE_AUTORIZOU,
                    LogSolicitacoesUsuario.INICIO_FLUXO,
                ],
                terceirizada_uuid=terceirizada_uuid,
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct("uuid")
        )

    @classmethod
    def get_recebidas(cls, **kwargs):
        terceirizada_uuid = kwargs.get("terceirizada_uuid")
        return (
            cls.objects.filter(
                status_evento__in=cls.AUTORIZADOS_EVENTO,
                status_atual__in=cls.AUTORIZADOS_STATUS,
                terceirizada_uuid=terceirizada_uuid,
                data_evento__lte=datetime.date.today(),
            )
            .exclude(tipo_doc=cls.TP_SOL_DIETA_ESPECIAL)
            .distinct()
            .order_by("-data_log")
        )

    @classmethod
    def map_queryset_por_status(cls, status, **kwargs):
        terceirizada_uuid = kwargs.get("instituicao_uuid")
        if not status:
            return cls.objects.all()
        mapeador = {
            "AUTORIZADOS": f'cls.get_autorizados(terceirizada_uuid="{terceirizada_uuid}")',
            "CANCELADOS": f'cls.get_cancelados(terceirizada_uuid="{terceirizada_uuid}")',
            "NEGADOS": f'cls.get_negados(terceirizada_uuid="{terceirizada_uuid}")',
            "RECEBIDAS": f'cls.get_recebidas(terceirizada_uuid="{terceirizada_uuid}")',
            "DIETAS_AUTORIZADAS": f'cls.get_autorizados_dieta_especial(terceirizada_uuid="{terceirizada_uuid}")',
        }
        return eval(mapeador[status])  # nosec
