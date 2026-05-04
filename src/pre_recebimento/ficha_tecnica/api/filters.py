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
    pregao_chamada_publica = filters.CharFilter(
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
