from django_filters import rest_framework as filters


class TipoEmbalagemQldFilter(filters.FilterSet):
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    nome = filters.CharFilter(
        field_name="nome",
        lookup_expr="icontains",
    )
    abreviacao = filters.CharFilter(
        field_name="abreviacao",
        lookup_expr="exact",
    )
    data_cadastro = filters.DateFilter(
        field_name="criado_em__date",
        lookup_expr="exact",
    )


class LaboratorioFilter(filters.FilterSet):
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    nome = filters.CharFilter(
        field_name="nome",
        lookup_expr="icontains",
    )
    cnpj = filters.CharFilter(
        field_name="cnpj",
        lookup_expr="icontains",
    )
    credenciado = filters.BooleanFilter(field_name="credenciado")
