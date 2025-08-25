from django.db.models import Q
from django_filters import rest_framework as filters
from sme_sigpae_api.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow


class QuestoesPorProdutoFilter(filters.FilterSet):
    ficha_tecnica = filters.CharFilter(
        field_name="ficha_tecnica__uuid",
        lookup_expr="exact",
    )
    questao = filters.CharFilter(method="filtrar_questao")

    def filtrar_questao(self, queryset, name, value):
        return queryset.filter(
            Q(questoes_primarias__questao=value)
            | Q(questoes_secundarias__questao=value)
        ).distinct()


class FichaRecebimentoFilter(filters.FilterSet):
    numero_cronograma = filters.CharFilter(
        field_name="etapa__cronograma__numero",
        lookup_expr="icontains",
    )
    nome_produto = filters.CharFilter(
        field_name="etapa__cronograma__ficha_tecnica__produto__nome",
        lookup_expr="icontains",
    )
    nome_empresa = filters.CharFilter(
        field_name="etapa__cronograma__empresa__nome_fantasia",
        lookup_expr="icontains",
    )
    data_inicial = filters.DateFilter(
        field_name="data_entrega",
        lookup_expr="gte",
    )
    data_final = filters.DateFilter(
        field_name="data_entrega",
        lookup_expr="lte",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in FichaDeRecebimentoWorkflow.states],
    )
