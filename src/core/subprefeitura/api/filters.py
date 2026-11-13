from django_filters import rest_framework as filters

from src.core.models import Subprefeitura
from src.dados_comuns.constants import PayloadVariaveis

from ...api.filters import restringir_uuids_de_dre, uuids_de_lista


class SubprefeituraFilter(filters.FilterSet):
    """
    Filtra subprefeituras pela diretoria regional.

    Sem parâmetro, devolve o cadastro completo.
    Com ``diretoria_regional__uuid`` ou ``diretoria_regional__uuid[]``,
    devolve a união distinta das subprefeituras vinculadas às DREs informadas.
    DRE e Terceirizada não recebem subprefeituras de DREs fora do próprio escopo.
    """

    class Meta:
        model = Subprefeitura
        fields = ["uuid"]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        uuids = uuids_de_lista(
            self.data,
            PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
            "diretoria_regional__uuid",
        )
        if not uuids:
            return queryset
        uuids = restringir_uuids_de_dre(uuids, self.request)
        if not uuids:
            return queryset.none()
        return queryset.filter(diretoria_regional__uuid__in=uuids).distinct()
