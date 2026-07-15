import functools
import operator

from django.db.models import Q
from django_filters import rest_framework as filters

from src.terceirizada.models import Terceirizada

from ...dados_comuns.fluxo_status import (
    GuiaRemessaWorkFlow,
    NotificacaoOcorrenciaWorkflow,
    SolicitacaoRemessaWorkFlow,
)
from ..models.guia import ConferenciaIndividualPorAlimento


class SolicitacaoFilter(filters.FilterSet):
    uuid = filters.CharFilter(
        field_name="uuid",
        lookup_expr="exact",
    )
    numero_requisicao = filters.CharFilter(
        field_name="numero_solicitacao",
        lookup_expr="icontains",
    )
    nome_distribuidor = filters.CharFilter(
        field_name="distribuidor__nome_fantasia",
        lookup_expr="icontains",
    )
    distribuidor = filters.ModelMultipleChoiceFilter(
        field_name="distribuidor__uuid",
        to_field_name="uuid",
        queryset=Terceirizada.objects.filter(
            tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
        ),
    )
    data_inicial = filters.DateFilter(
        field_name="guias__data_entrega",
        lookup_expr="gte",
    )
    data_final = filters.DateFilter(
        field_name="guias__data_entrega",
        lookup_expr="lte",
    )
    numero_guia = filters.CharFilter(
        field_name="guias__numero_guia",
        lookup_expr="exact",
    )
    codigo_unidade = filters.CharFilter(
        field_name="guias__codigo_unidade",
        lookup_expr="exact",
    )
    nome_unidade = filters.CharFilter(
        field_name="guias__nome_unidade__unaccent",
        lookup_expr="icontains",
    )
    nome_produto = filters.CharFilter(
        field_name="guias__alimentos__nome_alimento__unaccent",
        lookup_expr="icontains",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in SolicitacaoRemessaWorkFlow.states],
    )
    status_guia = filters.MultipleChoiceFilter(
        field_name="guias__status",
        choices=[(str(state), state) for state in GuiaRemessaWorkFlow.states],
    )


class GuiaFilter(filters.FilterSet):
    codigo_unidade = filters.CharFilter(
        field_name="codigo_unidade",
        lookup_expr="exact",
    )
    nome_unidade = filters.CharFilter(
        field_name="nome_unidade",
        lookup_expr="icontains",
    )
    numero_guia = filters.CharFilter(
        field_name="numero_guia",
        lookup_expr="exact",
    )
    numero_requisicao = filters.CharFilter(
        field_name="solicitacao__numero_solicitacao",
        lookup_expr="icontains",
    )
    data_inicial = filters.DateFilter(
        field_name="data_entrega",
        lookup_expr="gte",
    )
    data_final = filters.DateFilter(
        field_name="data_entrega",
        lookup_expr="lte",
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in GuiaRemessaWorkFlow.states],
    )
    motivos_ocorrencia = filters.MultipleChoiceFilter(
        field_name="conferencias__conferencia_dos_alimentos__ocorrencia__icontains",
        choices=[
            (str(state), state)
            for state in ConferenciaIndividualPorAlimento.OCORRENCIA_NOMES
        ],
    )
    empresa = filters.ModelMultipleChoiceFilter(
        field_name="solicitacao__distribuidor__uuid",
        to_field_name="uuid",
        queryset=Terceirizada.objects.filter(
            tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
        ),
    )


class SolicitacaoAlteracaoFilter(filters.FilterSet):
    numero_solicitacao = filters.CharFilter(
        field_name="numero_solicitacao",
        lookup_expr="exact",
    )
    numero_requisicao = filters.CharFilter(
        field_name="requisicao__numero_solicitacao",
        lookup_expr="icontains",
    )
    nome_distribuidor = filters.CharFilter(
        field_name="requisicao__distribuidor__razao_social",
        lookup_expr="icontains",
    )
    distribuidor = filters.ModelMultipleChoiceFilter(
        field_name="requisicao__distribuidor__uuid",
        to_field_name="uuid",
        queryset=Terceirizada.objects.filter(
            tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
        ),
    )
    data_inicial = filters.DateFilter(
        field_name="requisicao__guias__data_entrega",
        lookup_expr="gte",
    )
    data_final = filters.DateFilter(
        field_name="requisicao__guias__data_entrega",
        lookup_expr="lte",
    )
    motivos = filters.CharFilter(field_name="motivo", method="filtra_motivos")

    def filtra_motivos(self, qs, name, value):
        motivos = value.replace(", ", ",").split(",")
        filtro = functools.reduce(
            operator.or_, (Q(motivo__icontains=motivo) for motivo in motivos)
        )
        return qs.filter(filtro)


class NotificacaoFilter(filters.FilterSet):
    numero = filters.CharFilter(
        field_name="numero",
        lookup_expr="icontains",
    )
    empresa = filters.ModelMultipleChoiceFilter(
        field_name="empresa__uuid",
        to_field_name="uuid",
        queryset=Terceirizada.objects.filter(
            tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM
        ),
    )
    status = filters.MultipleChoiceFilter(
        field_name="status",
        choices=[(str(state), state) for state in NotificacaoOcorrenciaWorkflow.states],
    )
    processo_sei = filters.CharFilter(
        field_name="processo_sei",
        lookup_expr="icontains",
    )
