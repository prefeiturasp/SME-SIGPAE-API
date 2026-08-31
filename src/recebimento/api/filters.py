"""Filtros da API do módulo de recebimento."""

from django.db.models import Q
from django_filters import rest_framework as filters

from src.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow


class QuestoesPorProdutoFilter(filters.FilterSet):
    """Filtros das questões por produto.

    Permite filtrar por ``ficha_tecnica`` (uuid exato) e por ``questao``
    (texto da questão, considerando questões primárias e secundárias).
    """

    ficha_tecnica = filters.CharFilter(
        field_name="ficha_tecnica__uuid",
        lookup_expr="exact",
    )
    questao = filters.CharFilter(method="filtrar_questao")

    def filtrar_questao(self, queryset, name, value):
        """Filtra pelas questões primárias ou secundárias com o texto."""
        return queryset.filter(
            Q(questoes_primarias__questao=value)
            | Q(questoes_secundarias__questao=value)
        ).distinct()


class FichaRecebimentoFilter(filters.FilterSet):
    """Filtros das fichas de recebimento.

    Permite filtrar por ``numero_cronograma`` (contém), ``nome_produto``
    (contém), ``nome_empresa`` (nome fantasia, contém), período de entrega
    (``data_inicial``/``data_final``) e ``status`` (múltipla escolha pelos
    estados do ``FichaDeRecebimentoWorkflow``).
    """

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
