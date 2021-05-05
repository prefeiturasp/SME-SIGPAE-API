import functools
import operator

from django.db.models import Q
from django_filters import rest_framework as filters

from ...dados_comuns.fluxo_status import GuiaRemessaWorkFlow, SolicitacaoRemessaWorkFlow


class SolicitacaoFilter(filters.FilterSet):

    numero_requisicao = filters.CharFilter(
        field_name='numero_solicitacao',
        lookup_expr='exact',
    )
    nome_distribuidor = filters.CharFilter(
        field_name='distribuidor__nome_fantasia',
        lookup_expr='icontains',
    )
    data_inicial = filters.DateFilter(
        field_name='guias__data_entrega',
        lookup_expr='gte',
    )
    data_final = filters.DateFilter(
        field_name='guias__data_entrega',
        lookup_expr='lte',
    )
    numero_guia = filters.CharFilter(
        field_name='guias__numero_guia',
        lookup_expr='exact',
    )
    codigo_unidade = filters.CharFilter(
        field_name='guias__codigo_unidade',
        lookup_expr='exact',
    )
    nome_unidade = filters.CharFilter(
        field_name='guias__nome_unidade__unaccent',
        lookup_expr='icontains',
    )
    nome_produto = filters.CharFilter(
        field_name='guias__alimentos__nome_alimento__unaccent',
        lookup_expr='icontains',
    )
    status = filters.MultipleChoiceFilter(
        field_name='status',
        choices=[(str(state), state) for state in SolicitacaoRemessaWorkFlow.states],
    )


class GuiaFilter(filters.FilterSet):
    codigo_unidade = filters.CharFilter(
        field_name='codigo_unidade',
        lookup_expr='exact',
    )
    nome_unidade = filters.CharFilter(
        field_name='nome_unidade',
        lookup_expr='icontains',
    )
    numero_guia = filters.CharFilter(
        field_name='numero_guia',
        lookup_expr='exact',
    )
    numero_requisicao = filters.CharFilter(
        field_name='solicitacao__numero_solicitacao',
        lookup_expr='exact',
    )
    data_inicial = filters.DateFilter(
        field_name='data_entrega',
        lookup_expr='gte',
    )
    data_final = filters.DateFilter(
        field_name='data_entrega',
        lookup_expr='lte',
    )
    status = filters.MultipleChoiceFilter(
        field_name='status',
        choices=[(str(state), state) for state in GuiaRemessaWorkFlow.states],
    )


class SolicitacaoAlteracaoFilter(filters.FilterSet):

    numero_solicitacao = filters.CharFilter(
        field_name='numero_solicitacao',
        lookup_expr='exact',
    )
    numero_requisicao = filters.CharFilter(
        field_name='requisicao__numero_solicitacao',
        lookup_expr='exact',
    )
    nome_distribuidor = filters.CharFilter(
        field_name='requisicao__distribuidor__razao_social',
        lookup_expr='icontains',
    )
    data_inicial = filters.DateFilter(
        field_name='requisicao__guias__data_entrega',
        lookup_expr='gte',
    )
    data_final = filters.DateFilter(
        field_name='requisicao__guias__data_entrega',
        lookup_expr='lte',
    )
    motivos = filters.CharFilter(field_name='motivo', method='filtra_motivos')

    def filtra_motivos(self, qs, name, value):
        motivos = value.replace(', ', ',').split(',')
        filtro = functools.reduce(
            operator.or_, (Q(motivo__icontains=motivo) for motivo in motivos)
        )
        return qs.filter(filtro)
