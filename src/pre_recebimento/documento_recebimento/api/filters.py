from django_filters import rest_framework as filters

from src.terceirizada.models import Terceirizada

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


class CronogramaRelatorioDocumentosFilter(filters.FilterSet):
    empresa = filters.ModelMultipleChoiceFilter(
        field_name="empresa__uuid",
        to_field_name="uuid",
        queryset=Terceirizada.objects.all(),
    )
    nome_produto = filters.CharFilter(
        field_name="ficha_tecnica__produto__nome",
        lookup_expr="icontains",
    )
    numero_cronograma = filters.CharFilter(
        field_name="numero",
        lookup_expr="icontains",
    )
