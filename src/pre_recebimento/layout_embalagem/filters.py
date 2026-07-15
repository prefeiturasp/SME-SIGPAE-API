from django_filters import rest_framework as filters

from ...dados_comuns.fluxo_status import (
    LayoutDeEmbalagemWorkflow,
)


class LayoutDeEmbalagemFilter(filters.FilterSet):
    numero_ficha_tecnica = filters.CharFilter(
        field_name="ficha_tecnica__numero",
        lookup_expr="icontains",
    )
    nome_produto = filters.CharFilter(
        field_name="ficha_tecnica__produto__nome",
        lookup_expr="icontains",
    )
    nome_fornecedor = filters.CharFilter(
        field_name="ficha_tecnica__empresa__razao_social",
        lookup_expr="icontains",
    )
    pregao_chamada_publica = filters.CharFilter(
        field_name="ficha_tecnica__pregao_chamada_publica",
        lookup_expr="icontains",
    )
    numero_cronograma = filters.CharFilter(
        field_name="ficha_tecnica__cronograma__numero",
        lookup_expr="icontains",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in LayoutDeEmbalagemWorkflow.states],
    )
