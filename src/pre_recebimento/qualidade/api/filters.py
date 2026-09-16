"""Filtros da API do submódulo de qualidade."""

from django_filters import rest_framework as filters


class TipoEmbalagemQldFilter(filters.FilterSet):
    """Filtros dos tipos de embalagem (qualidade).

    Permite filtrar por ``uuid`` (exato), ``nome`` (contém, sem
    diferenciar maiúsculas), ``abreviacao`` (exato) e ``data_cadastro``
    (data exata do campo ``criado_em``).
    """
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
    """Filtros dos laboratórios.

    Permite filtrar por ``uuid`` (exato), ``nome`` (contém, sem
    diferenciar maiúsculas), ``cnpj`` (contém, sem diferenciar
    maiúsculas) e ``credenciado`` (booleano).
    """
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
