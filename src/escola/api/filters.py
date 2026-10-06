from datetime import datetime, timedelta

from django_filters import rest_framework as filters

from src.dados_comuns.constants import PayloadVariaveis
from src.escola.models import (
    Aluno,
    DiretoriaRegional,
    Escola,
    HistoricoMatriculaAluno,
    Subprefeitura,
)
from src.terceirizada.models import Terceirizada


def instituicao_da_requisicao(request):
    if not request or not getattr(request.user, "is_authenticated", False):
        return None
    vinculo = getattr(request.user, "vinculo_atual", None)
    if not vinculo:
        return None
    return vinculo.instituicao


def dres_da_terceirizada(terceirizada):
    """DREs dos lotes da empresa com contrato vigente, como em diretorias-regionais-simplissima."""
    return DiretoriaRegional.objects.filter(
        lotes__terceirizada=terceirizada,
        lotes__contratos_do_lote__encerrado=False,
        lotes__contratos_do_lote__edital__uuid__in=terceirizada.editais,
    ).distinct()


def dres_no_escopo(usuario):
    """
    QuerySet de DREs que o usuário pode consultar.

    Retorna None quando o perfil não tem restrição institucional (CODAE e equivalentes).
    """
    instituicao = instituicao_da_requisicao_usuario(usuario)
    if isinstance(instituicao, DiretoriaRegional):
        return DiretoriaRegional.objects.filter(pk=instituicao.pk)
    if isinstance(instituicao, Terceirizada):
        return dres_da_terceirizada(instituicao)
    return None


def instituicao_da_requisicao_usuario(usuario):
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return None
    vinculo = getattr(usuario, "vinculo_atual", None)
    if not vinculo:
        return None
    return vinculo.instituicao


def filtrar_lotes_por_escopo(queryset, request):
    instituicao = instituicao_da_requisicao(request)
    if isinstance(instituicao, DiretoriaRegional):
        return queryset.filter(diretoria_regional=instituicao)
    if isinstance(instituicao, Terceirizada):
        return queryset.filter(terceirizada=instituicao)
    return queryset


def uuids_de_lista(data, chave_lista, chave_simples):
    if not hasattr(data, "getlist"):
        return []
    uuids = data.getlist(chave_lista)
    if not uuids:
        uuids = data.getlist(chave_simples)
    return [uuid for uuid in uuids if uuid]


def restringir_uuids_de_dre(uuids, request):
    instituicao = instituicao_da_requisicao(request)
    if isinstance(instituicao, DiretoriaRegional):
        permitidos = {str(instituicao.uuid)}
        return [uuid for uuid in uuids if str(uuid) in permitidos]
    if isinstance(instituicao, Terceirizada):
        dres = dres_da_terceirizada(instituicao).values_list("uuid", flat=True)
        permitidos = {str(uuid) for uuid in dres}
        return [uuid for uuid in uuids if str(uuid) in permitidos]
    return uuids


def aplicar_escopo_escola_para_filtros(queryset, request):
    instituicao = instituicao_da_requisicao(request)
    if isinstance(instituicao, Terceirizada):
        return queryset.filter(lote__terceirizada=instituicao)
    if isinstance(instituicao, DiretoriaRegional):
        return queryset.filter(diretoria_regional=instituicao)
    return queryset


def _filtrar_uuid_in(queryset, data, chave, lookup):
    valores = data.getlist(chave) if hasattr(data, "getlist") else []
    if valores:
        return queryset.filter(**{lookup: valores})
    return queryset


def _excluir_uuid_in(queryset, data, chave, lookup):
    valores = data.getlist(chave) if hasattr(data, "getlist") else []
    if valores:
        return queryset.exclude(**{lookup: valores})
    return queryset


def aplicar_filtros_lista_escola(queryset, data):
    queryset = _filtrar_uuid_in(
        queryset,
        data,
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        "tipo_unidade__uuid__in",
    )
    queryset = _filtrar_uuid_in(
        queryset, data, PayloadVariaveis.LOTE_UUID.value, "lote__uuid__in"
    )
    queryset = _excluir_uuid_in(
        queryset,
        data,
        PayloadVariaveis.EXCLUIR_TIPO_UNIDADE_UUID.value,
        "tipo_unidade__uuid__in",
    )
    queryset = _filtrar_uuid_in(
        queryset,
        data,
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        "diretoria_regional__uuid__in",
    )
    return _filtrar_uuid_in(
        queryset,
        data,
        PayloadVariaveis.SUBPREFEITURA_UUID.value,
        "subprefeitura__uuid__in",
    )


class DiretoriaRegionalFilter(filters.FilterSet):
    dre = filters.CharFilter(
        field_name="diretoria_regional__uuid", lookup_expr="iexact"
    )


class EscolaParaFiltrosFilter(filters.FilterSet):
    """
    Filtros de escolas usados por relatórios.

    Listas seguem a serialização do front, com a chave repetida e colchetes
    (``diretoria_regional__uuid[]``, ``lote__uuid[]``, ``subprefeitura__uuid[]``,
    ``tipo_unidade__uuid[]``). O valor único sem colchetes continua valendo
    para ``diretoria_regional__uuid``, ``lote__uuid``, ``subprefeitura__uuid``
    e ``tipo_gestao__nome``. ``tipo_unidade__uuid__in`` e
    ``excluir_tipo_unidade__uuid[]`` permanecem compatíveis com os relatórios
    de adesão e financeiro.

    Usuários de DRE e de empresa terceirizada só recebem escolas do próprio escopo.
    """

    class Meta:
        model = Escola
        fields = {
            "tipo_unidade__uuid": ["in"],
            "diretoria_regional__uuid": ["exact"],
            "lote__uuid": ["exact"],
            "subprefeitura__uuid": ["exact"],
            "tipo_gestao__nome": ["exact"],
        }

    def filter_queryset(self, queryset):
        queryset = aplicar_escopo_escola_para_filtros(queryset, self.request)
        queryset = super().filter_queryset(queryset)
        return aplicar_filtros_lista_escola(queryset, self.data)


class SubprefeituraFilter(filters.FilterSet):
    """
    Filtra subprefeituras pela diretoria regional.

    Sem parâmetro, devolve o cadastro completo (Cadastro de Lote).
    Com ``diretoria_regional__uuid`` ou ``diretoria_regional__uuid[]``,
    devolve a união distinta das subprefeituras vinculadas às DREs informadas.
    DRE e Terceirizada não recebem subprefeituras de DREs fora do próprio escopo.
    """

    class Meta:
        model = Subprefeitura
        fields = ["uuid"]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        uuids = uuids_de_lista(
            self.data,
            PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
            "diretoria_regional__uuid",
        )
        if not uuids:
            return queryset
        uuids = restringir_uuids_de_dre(uuids, self.request)
        if not uuids:
            return queryset.none()
        return queryset.filter(diretoria_regional__uuid__in=uuids).distinct()


class AlunoFilter(filters.FilterSet):
    codigo_eol = filters.CharFilter(field_name="codigo_eol", lookup_expr="iexact")
    dre = filters.CharFilter(
        field_name="escola__diretoria_regional__uuid", lookup_expr="iexact"
    )
    escola = filters.CharFilter(field_name="escola__uuid", method="filter_escola")
    nao_tem_dieta_especial = filters.BooleanFilter(
        field_name="dietas_especiais", lookup_expr="isnull"
    )
    periodo_escolar_nome = filters.CharFilter(
        field_name="periodo_escolar__nome", lookup_expr="iexact"
    )

    def filter_escola(self, queryset, name, value):
        _filter = {name: value}

        alunos_atualmente_na_escola = queryset.filter(**_filter)

        if self.request.query_params.get("inclui_alunos_egressos") != "true":
            return alunos_atualmente_na_escola

        historicos_da_escola = HistoricoMatriculaAluno.objects.filter(**_filter)

        mes = self.request.query_params.get("mes")
        ano = self.request.query_params.get("ano")
        if mes is not None and ano is not None:
            ultimo_dia_do_mes = datetime(
                int(ano), min(int(mes) + 1, 12), 1
            ) - timedelta(days=1)
            primeiro_dia_do_mes = datetime(int(ano), int(mes), 1)

            historicos_da_escola_ativos = historicos_da_escola.filter(
                data_inicio__lte=ultimo_dia_do_mes, data_fim__isnull=True
            )
            historicos_da_escola_concluidos = historicos_da_escola.filter(
                data_inicio__lte=ultimo_dia_do_mes, data_fim__gte=primeiro_dia_do_mes
            )
            historicos_da_escola = (
                historicos_da_escola_ativos | historicos_da_escola_concluidos
            )

        alunos_com_historico_na_escola = Aluno.objects.filter(
            id__in=historicos_da_escola.values_list("aluno_id", flat=True)
        )

        return alunos_com_historico_na_escola


class LogAlunosMatriculadosFaixaEtariaDiaFilter(filters.FilterSet):
    escola_uuid = filters.UUIDFilter(field_name="escola__uuid")
    nome_periodo_escolar = filters.CharFilter(field_name="periodo_escolar__nome")
    mes = filters.CharFilter(field_name="data__month", lookup_expr="exact")
    ano = filters.CharFilter(field_name="data__year", lookup_expr="iexact")
    dias = filters.BaseInFilter(field_name="data__day", lookup_expr="in")
