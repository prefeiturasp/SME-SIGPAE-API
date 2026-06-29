from django_filters import rest_framework as filters

from ..models import DiaLetivoSIGPAE


class DiaLetivoFilter(filters.FilterSet):
    """Filtro para listagem de dias letivos.

    Os parâmetros ``mes`` e ``ano`` são obrigatórios e aplicam
    filtro exato sobre o mês e o ano do campo ``data`` do modelo
    DiaLetivoSIGPAE.
    """

    mes = filters.NumberFilter(
        field_name="data__month",
        lookup_expr="exact",
        required=True,
    )
    ano = filters.NumberFilter(
        field_name="data__year",
        lookup_expr="exact",
        required=True,
    )

    class Meta:
        model = DiaLetivoSIGPAE
        fields = ("mes", "ano")
