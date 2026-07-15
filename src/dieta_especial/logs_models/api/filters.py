from django_filters import rest_framework as filters


class LogQuantidadeDietasEspeciaisFilter(filters.FilterSet):
    escola_uuid = filters.UUIDFilter(field_name="escola__uuid")
    classificacao = filters.CharFilter(field_name="classificacao")
    periodo_escolar = filters.UUIDFilter(field_name="periodo_escolar__uuid")
    nome_periodo_escolar = filters.CharFilter(field_name="periodo_escolar__nome")
    mes = filters.CharFilter(field_name="data__month", lookup_expr="exact")
    ano = filters.CharFilter(field_name="data__year", lookup_expr="iexact")
    unificado = filters.BooleanFilter(
        field_name="periodo_escolar", lookup_expr="isnull"
    )
    cei_ou_emei = filters.CharFilter(field_name="cei_ou_emei")


class LogQuantidadeDietasRecreioNasFeriasFilter(filters.FilterSet):
    escola_uuid = filters.UUIDFilter(field_name="escola__uuid")
    mes = filters.CharFilter(field_name="data__month", lookup_expr="exact")
    ano = filters.CharFilter(field_name="data__year", lookup_expr="iexact")
