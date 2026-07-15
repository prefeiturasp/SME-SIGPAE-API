from django_filters import rest_framework as filters

from src.recebimento.ajuste_saldo_laudo.models import AjusteSaldo


class AjusteSaldoFilter(filters.FilterSet):
    """
    Filtros para listagem de Ajustes de Saldo.

    Filtros disponíveis:
    - numero_cronograma: Número do cronograma relacionado (icontains)
    - nome_empresa: Nome da empresa relacionada (icontains)
    - nome_produto: Nome do produto relacionado (icontains)
    """

    numero_cronograma = filters.CharFilter(
        field_name="documento_recebimento__cronograma__numero",
        lookup_expr="icontains",
        label="Número do Cronograma",
    )
    nome_empresa = filters.CharFilter(
        field_name="documento_recebimento__cronograma__empresa__nome_fantasia",
        lookup_expr="icontains",
        label="Nome da Empresa",
    )
    nome_produto = filters.CharFilter(
        field_name="documento_recebimento__cronograma__ficha_tecnica__produto__nome",
        lookup_expr="icontains",
        label="Nome do Produto",
    )

    class Meta:
        model = AjusteSaldo
        fields = [
            "numero_cronograma",
            "nome_empresa",
            "nome_produto",
        ]
