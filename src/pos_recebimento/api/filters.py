from django_filters import rest_framework as filters

from ..models import TermoRecebimentoDefinitivo


class TermoRecebimentoDefinitivoFilter(filters.FilterSet):
    """Filtros para listagem de Termos de Recebimento Definitivo.

    Permite filtrar por:
    - ``uuid``: UUID exato do termo.
    - ``nome_produto``: Nome do produto (via ficha técnica dos cronogramas).
    - ``nome_empresa``: Nome fantasia da empresa.
    - ``numero_cronograma``: Parte do número de algum cronograma do termo.
    - ``status``: Um ou mais status do termo.
    - ``data_inicial`` / ``data_final``: Intervalo de data de criação.
    """

    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    nome_produto = filters.CharFilter(
        field_name="cronogramas__ficha_tecnica__produto__nome",
        lookup_expr="icontains",
        distinct=True,
    )
    nome_empresa = filters.CharFilter(
        field_name="empresa__nome_fantasia",
        lookup_expr="icontains",
    )
    numero_cronograma = filters.CharFilter(
        field_name="cronogramas__numero",
        lookup_expr="icontains",
        distinct=True,
    )
    numero_contrato = filters.CharFilter(
        field_name="contrato__numero",
        lookup_expr="icontains",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[
            (str(state), state)
            for state, _ in TermoRecebimentoDefinitivo.STATUS_CHOICES
        ],
    )
    status_fornecedor = filters.CharFilter(
        field_name="status",
        method="filter_status_fornecedor",
        help_text=(
            "Filtro agregado para o fornecedor: RECEBIDO agrupa os status "
            "do fluxo de envio; ASSINADO corresponde a ASSINADO_FORNECEDOR."
        ),
    )
    data_inicial = filters.DateFilter(
        field_name="criado_em",
        lookup_expr="date__gte",
    )
    data_final = filters.DateFilter(
        field_name="criado_em",
        lookup_expr="date__lte",
    )

    class Meta:
        model = TermoRecebimentoDefinitivo
        fields = ("uuid", "status")

    def filter_status_fornecedor(self, queryset, name, value):
        """Agrupa os status na visão do fornecedor.

        ``RECEBIDO`` corresponde aos status do fluxo de envio e
        ``ASSINADO`` ao status ``ASSINADO_FORNECEDOR``. Qualquer outro
        valor não aplica filtro.
        """
        if value == "RECEBIDO":
            return queryset.filter(
                status__in=TermoRecebimentoDefinitivo.STATUS_RECEBIDO_FORNECEDOR
            )
        if value == "ASSINADO":
            return queryset.filter(
                status=TermoRecebimentoDefinitivo.ASSINADO_FORNECEDOR
            )
        return queryset
