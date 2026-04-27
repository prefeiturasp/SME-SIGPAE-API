from django_filters import rest_framework as filters

from sme_sigpae_api.dados_comuns.fluxo_status import CronogramaSemanalWorkflow
from sme_sigpae_api.pre_recebimento.cronograma_semanal.models import CronogramaSemanal


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
        field_name="alterado_em",
        lookup_expr="gte",
        label="Data Inicial",
        input_formats=["%d/%m/%Y"],
    )
    data_final = filters.DateFilter(
        field_name="alterado_em",
        lookup_expr="lte",
        label="Data Final",
        input_formats=["%d/%m/%Y"],
    )

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
