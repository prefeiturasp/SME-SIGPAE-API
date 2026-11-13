from django_filters import rest_framework as filters

from src.core.models import Escola

from ...api.filters import (
    aplicar_escopo_escola_para_filtros,
    aplicar_filtros_lista_escola,
)


class EscolaParaFiltrosFilter(filters.FilterSet):
    """
    Filtros de escolas usados por relatórios.
    Usuários de DRE e de empresa terceirizada só recebem escolas do próprio escopo.
    """

    class Meta:
        model = Escola
        fields = {
            "tipo_unidade__uuid": ["in"],
            "diretoria_regional__uuid": ["exact"],
            "lote__uuid": ["exact"],
            "subprefeitura__uuid": ["exact"],
            "tipo_gestao__nome": ["exact"],
        }

    def filter_queryset(self, queryset):
        queryset = aplicar_escopo_escola_para_filtros(queryset, self.request)
        queryset = super().filter_queryset(queryset)
        return aplicar_filtros_lista_escola(queryset, self.data)
