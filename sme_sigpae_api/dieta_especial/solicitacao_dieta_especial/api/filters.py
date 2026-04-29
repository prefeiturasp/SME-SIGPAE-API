from django_filters import rest_framework as filters

from sme_sigpae_api.dados_comuns.fluxo_status import DietaEspecialWorkflow
from sme_sigpae_api.dieta_especial.protocolo_padrao.models import (
    Alimento,
    ProtocoloPadraoDietaEspecial,
)
from sme_sigpae_api.dieta_especial.solicitacao_dieta_especial.models import (
    ClassificacaoDieta,
    MotivoNegacao,
)


class DietaEspecialFilter(filters.FilterSet):
    aluno = filters.CharFilter(field_name="aluno__uuid", lookup_expr="iexact")
    nome_aluno = filters.CharFilter(field_name="aluno__nome", lookup_expr="icontains")
    nome_completo_aluno = filters.CharFilter(
        field_name="aluno__nome", lookup_expr="iexact"
    )
    codigo_eol_aluno = filters.CharFilter(
        field_name="aluno__codigo_eol", lookup_expr="iexact"
    )
    escola = filters.CharFilter(field_name="rastro_escola__uuid", lookup_expr="iexact")
    dre = filters.CharFilter(
        field_name="rastro_escola__diretoria_regional__uuid", lookup_expr="iexact"
    )
    cpf_responsavel = filters.CharFilter(
        field_name="aluno__responsaveis__cpf", lookup_expr="iexact"
    )
    ativo = filters.BooleanFilter(field_name="ativo")
    tipo_solicitacao = filters.CharFilter(
        field_name="tipo_solicitacao", lookup_expr="iexact"
    )
    data_inicial = filters.DateFilter(field_name="criado_em", lookup_expr="date__gte")
    data_final = filters.DateFilter(field_name="criado_em", lookup_expr="date__lte")
    classificacao = filters.ModelMultipleChoiceFilter(
        field_name="classificacao__id",
        to_field_name="id",
        queryset=ClassificacaoDieta.objects.all(),
    )
    status = filters.MultipleChoiceFilter(
        choices=[(str(state), state) for state in DietaEspecialWorkflow.states]
    )
    terceirizada = filters.CharFilter(
        field_name="rastro_terceirizada__uuid", lookup_expr="iexact"
    )
    protocolos_padrao = filters.ModelMultipleChoiceFilter(
        field_name="protocolo_padrao__uuid",
        to_field_name="uuid",
        queryset=ProtocoloPadraoDietaEspecial.objects.all(),
    )
    tipo_gestao = filters.CharFilter(
        field_name="escola_destino__tipo_gestao__uuid", lookup_expr="iexact"
    )
    lote = filters.CharFilter(
        field_name="escola_destino__lote__uuid", lookup_expr="iexact"
    )


class AlimentoFilter(filters.FilterSet):
    tipo = filters.MultipleChoiceFilter(choices=Alimento.TIPO_CHOICES)
    ativo = filters.BooleanFilter(field_name="ativo")


class MotivoNegacaoFilter(filters.FilterSet):
    processo = filters.MultipleChoiceFilter(choices=MotivoNegacao.PROCESSO_CHOICES)
