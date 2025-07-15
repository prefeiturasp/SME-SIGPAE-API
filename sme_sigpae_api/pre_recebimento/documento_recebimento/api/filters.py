from django_filters import rest_framework as filters

from ....dados_comuns.fluxo_status import (
    DocumentoDeRecebimentoWorkflow,
)


class DocumentoDeRecebimentoFilter(filters.FilterSet):
    numero_cronograma = filters.CharFilter(
        field_name="cronograma__numero",
        lookup_expr="icontains",
    )
    nome_produto = filters.CharFilter(
        field_name="cronograma__ficha_tecnica__produto__nome",
        lookup_expr="icontains",
    )
    nome_fornecedor = filters.CharFilter(
        field_name="cronograma__empresa__razao_social",
        lookup_expr="icontains",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[
            (str(state), state) for state in DocumentoDeRecebimentoWorkflow.states
        ],
    )
    data_cadastro = filters.DateFilter(
        field_name="criado_em__date",
        lookup_expr="exact",
    )
