from django_filters import rest_framework as filters


class UnidadeMedidaFilter(filters.FilterSet):
    nome = filters.CharFilter(field_name="nome", lookup_expr="icontains")
    abreviacao = filters.CharFilter(field_name="abreviacao", lookup_expr="icontains")
    data_cadastro = filters.DateFilter(
        field_name="criado_em__date", lookup_expr="exact"
    )
