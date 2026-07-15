from django_filters import rest_framework as filters

from src.dados_comuns.fluxo_status import FormularioSupervisaoWorkflow


class FormularioSupervisaoFilter(filters.FilterSet):
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    diretoria_regional = filters.CharFilter(
        field_name="escola__lote__diretoria_regional__uuid",
        lookup_expr="exact",
    )
    unidade_educacional = filters.CharFilter(
        field_name="escola__uuid",
        lookup_expr="exact",
    )
    data_inicial = filters.DateFilter(
        field_name="formulario_base__data",
        lookup_expr="gte",
    )
    data_final = filters.DateFilter(
        field_name="formulario_base__data",
        lookup_expr="lte",
    )
    status = filters.MultipleChoiceFilter(
        choices=[(str(state), state) for state in FormularioSupervisaoWorkflow.states]
    )
    nome_nutricionista = filters.CharFilter(
        field_name="formulario_base__usuario__nome",
        lookup_expr="exact",
    )
