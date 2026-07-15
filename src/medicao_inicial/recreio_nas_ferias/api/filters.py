from django_filters import rest_framework as filters


class RecreioNasFeriasFilter(filters.FilterSet):
    escola_uuid = filters.CharFilter(
        field_name="unidades_participantes__unidade_educacional__uuid",
        lookup_expr="iexact",
    )
