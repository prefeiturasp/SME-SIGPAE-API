from django_filters import rest_framework as filters

from sme_sigpae_api.terceirizada.models import Terceirizada

from ....dados_comuns.fluxo_status import (
    CronogramaAlteracaoWorkflow,
    CronogramaWorkflow,
)


class CronogramaFilter(filters.FilterSet):
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    numero = filters.CharFilter(
        field_name="numero",
        lookup_expr="icontains",
    )
    nome_empresa = filters.CharFilter(
        field_name="empresa__nome_fantasia",
        lookup_expr="icontains",
    )
    nome_produto = filters.CharFilter(
        field_name="ficha_tecnica__produto__nome",
        lookup_expr="icontains",
    )
    data_inicial = filters.DateFilter(
        field_name="etapas__data_programada",
        lookup_expr="gte",
    )
    data_final = filters.DateFilter(
        field_name="etapas__data_programada",
        lookup_expr="lte",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in CronogramaWorkflow.states],
    )
    armazem = filters.ModelMultipleChoiceFilter(
        field_name="armazem__uuid",
        to_field_name="uuid",
        queryset=Terceirizada.objects.filter(
            tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
        ),
    )
    empresa = filters.ModelMultipleChoiceFilter(
        field_name="empresa__uuid",
        to_field_name="uuid",
        queryset=Terceirizada.objects.filter(
            tipo_servico__in=[
                Terceirizada.FORNECEDOR,
                Terceirizada.FORNECEDOR_E_DISTRIBUIDOR,
            ]
        ),
    )


class SolicitacaoAlteracaoCronogramaFilter(filters.FilterSet):
    numero_cronograma = filters.CharFilter(
        field_name="cronograma__numero",
        lookup_expr="icontains",
    )
    fornecedor = filters.CharFilter(
        field_name="cronograma__empresa__nome_fantasia",
        lookup_expr="icontains",
    )
    data = filters.DateFromToRangeFilter(
        field_name="criado_em",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in CronogramaAlteracaoWorkflow.states],
    )



