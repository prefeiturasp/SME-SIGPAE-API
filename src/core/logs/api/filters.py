from django_filters import rest_framework as filters


class LogAlunosMatriculadosFaixaEtariaDiaFilter(filters.FilterSet):
    escola_uuid = filters.UUIDFilter(field_name="escola__uuid")
    nome_periodo_escolar = filters.CharFilter(field_name="periodo_escolar__nome")
    mes = filters.CharFilter(field_name="data__month", lookup_expr="exact")
    ano = filters.CharFilter(field_name="data__year", lookup_expr="iexact")
    dias = filters.BaseInFilter(field_name="data__day", lookup_expr="in")
