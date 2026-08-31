"""Filtros da API do submódulo de cronograma semanal."""

from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from src.dados_comuns.fluxo_status import CronogramaSemanalWorkflow
from src.pre_recebimento.cronograma_semanal.models import (
    CronogramaSemanal,
    ProgramacaoEntregaSemanal,
)


class CronogramaSemanalFilter(filters.FilterSet):
    """
    Filtros para listagem de Cronogramas Semanais.

    Filtros disponíveis:
    - numero: Número do cronograma mensal (icontains)
    - nome_empresa: Nome da empresa do cronograma mensal (icontains)
    - nome_produto: Nome do produto do cronograma mensal (icontains)
    - status: Status do cronograma semanal (múltipla escolha)
    - data_inicial: Data inicial do período de Lançamento (gte)
    - data_final: Data final do período de Lançamento (lte)
    """

    numero = filters.CharFilter(
        field_name="cronograma_mensal__numero",
        lookup_expr="icontains",
        label="Número do Cronograma",
    )
    nome_empresa = filters.CharFilter(
        field_name="cronograma_mensal__empresa__nome_fantasia",
        lookup_expr="icontains",
        label="Nome da Empresa",
    )
    nome_produto = filters.CharFilter(
        field_name="cronograma_mensal__ficha_tecnica__produto__nome",
        lookup_expr="icontains",
        label="Nome do Produto",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in CronogramaSemanalWorkflow.states],
    )
    data_inicial = filters.DateFilter(
        method="filter_por_periodo",
        label="Data Inicial",
        input_formats=[FORMATO_DATA_BRASILEIRO],
    )
    data_final = filters.DateFilter(
        method="filter_por_periodo",
        label="Data Final",
        input_formats=[FORMATO_DATA_BRASILEIRO],
    )

    def filter_por_periodo(self, queryset, name, value):
        """Filtro de período (sem efeito direto).

        O filtro por período é aplicado em ``filter_queryset`` por meio de
        uma subquery nas programações de entrega, pois o período se refere
        às programações e não ao cronograma em si.
        """
        return queryset

    def filter_queryset(self, queryset):
        """Aplica os filtros padrão e o filtro por período.

        Quando ``data_inicial`` ou ``data_final`` são informados, mantém
        apenas os cronogramas que possuem programações de entrega cujo
        período (``data_inicio``/``data_fim``) intercepta o intervalo
        informado.
        """
        queryset = super().filter_queryset(queryset)

        data_inicial = self.form.cleaned_data.get("data_inicial")
        data_final = self.form.cleaned_data.get("data_final")

        if data_inicial or data_final:
            programacoes = ProgramacaoEntregaSemanal.objects.filter(
                cronograma_semanal=OuterRef("pk")
            )
            if data_inicial:
                programacoes = programacoes.filter(data_fim__gte=data_inicial)
            if data_final:
                programacoes = programacoes.filter(data_inicio__lte=data_final)

            queryset = queryset.filter(Exists(programacoes))

        return queryset

    class Meta:
        model = CronogramaSemanal
        fields = [
            "numero",
            "nome_empresa",
            "nome_produto",
            "status",
            "data_inicial",
            "data_final",
        ]
