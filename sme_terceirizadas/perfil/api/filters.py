from django_filters import rest_framework as filters

from sme_terceirizadas.dados_comuns.constants import StatusProcessamentoArquivo
from sme_terceirizadas.perfil.models.perfil import Perfil


class VinculoFilter(filters.FilterSet):
    usuario = filters.CharFilter(
        field_name='usuario__username',
        lookup_expr='exact',
    )
    nome = filters.CharFilter(
        field_name='usuario__nome',
        lookup_expr='icontains',
    )
    perfil = filters.CharFilter(
        field_name='perfil__nome',
        lookup_expr='exact',
    )
    visao = filters.MultipleChoiceFilter(
        field_name='perfil__visao',
        choices=Perfil.VISAO_CHOICES,
    )


class ImportacaoPlanilhaUsuarioCoreSSOFilter(filters.FilterSet):
    nome = filters.CharFilter(
        field_name='conteudo',
        lookup_expr='icontains',
    )
    data_inicial = filters.DateFilter(
        field_name='criado_em__date',
        lookup_expr='gte',
    )
    data_final = filters.DateFilter(
        field_name='criado_em__date',
        lookup_expr='lte',
    )
    status = filters.MultipleChoiceFilter(
        field_name='status',
        choices=StatusProcessamentoArquivo.choices(),
    )
