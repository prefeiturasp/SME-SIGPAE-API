from django_filters import rest_framework as filters


class SolicitacoesCODAEFilter(filters.FilterSet):
    busca = filters.CharFilter(field_name="uuid_original", lookup_expr="iexact")
