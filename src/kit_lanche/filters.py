from django_filters import rest_framework as filters


class KitLancheFilter(filters.FilterSet):
    numero_edital = filters.CharFilter(
        field_name="edital__numero",
        lookup_expr="exact",
    )
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    status = filters.CharFilter(field_name="status", lookup_expr="exact")
