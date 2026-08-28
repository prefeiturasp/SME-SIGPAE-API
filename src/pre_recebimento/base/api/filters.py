"""Filtros da API do submódulo base de pré-recebimento."""

from django_filters import rest_framework as filters


class UnidadeMedidaFilter(filters.FilterSet):
    """Filtros das unidades de medida.

    Permite filtrar por ``nome`` (contém, sem diferenciar maiúsculas),
    ``abreviacao`` (contém, sem diferenciar maiúsculas) e ``data_cadastro``
    (data exata do campo ``criado_em``).
    """
    nome = filters.CharFilter(field_name="nome", lookup_expr="icontains")
    abreviacao = filters.CharFilter(field_name="abreviacao", lookup_expr="icontains")
    data_cadastro = filters.DateFilter(
        field_name="criado_em__date", lookup_expr="exact"
    )
