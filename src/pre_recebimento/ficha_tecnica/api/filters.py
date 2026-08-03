from django_filters import rest_framework as filters

from ....dados_comuns.fluxo_status import (
    FichaTecnicaDoProdutoWorkflow,
)


class FichaTecnicaFilter(filters.FilterSet):
    numero_ficha = filters.CharFilter(
        field_name="numero",
        lookup_expr="icontains",
    )
    nome_produto = filters.CharFilter(
        field_name="produto__nome",
        lookup_expr="icontains",
    )
    nome_empresa = filters.CharFilter(
        field_name="empresa__nome_fantasia",
        lookup_expr="icontains",
    )
    empresa = filters.UUIDFilter(
        field_name="empresa__uuid",
        lookup_expr="exact",
    )
    pregao = filters.CharFilter(
        field_name="pregao_chamada_publica",
        lookup_expr="icontains",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in FichaTecnicaDoProdutoWorkflow.states],
    )
    data_cadastro = filters.DateFilter(
        field_name="criado_em__date",
        lookup_expr="exact",
    )
    categoria = filters.CharFilter(
        field_name="categoria",
        lookup_expr="exact",
    )
    programa = filters.CharFilter(
        field_name="programa",
        lookup_expr="exact",
    )
