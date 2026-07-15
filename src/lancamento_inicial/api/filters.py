from django_filters.rest_framework import DateFilter, FilterSet, ModelChoiceFilter

from ...escola.models import EscolaPeriodoEscolar


class LancamentoDiarioFilter(FilterSet):
    data = DateFilter()
    escola_periodo_escolar = ModelChoiceFilter(
        to_field_name="uuid", queryset=EscolaPeriodoEscolar.objects.all()
    )
