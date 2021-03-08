from django_filters import rest_framework as filters

from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ..models import Alimento, ClassificacaoDieta


class DietaEspecialFilter(filters.FilterSet):
    aluno = filters.CharFilter(field_name='aluno__uuid', lookup_expr='iexact')
    nome_aluno = filters.CharFilter(field_name='aluno__nome', lookup_expr='icontains')
    nome_completo_aluno = filters.CharFilter(field_name='aluno__nome', lookup_expr='iexact')
    codigo_eol_aluno = filters.CharFilter(field_name='aluno__codigo_eol', lookup_expr='iexact')
    escola = filters.CharFilter(field_name='rastro_escola__uuid', lookup_expr='iexact')
    dre = filters.CharFilter(field_name='rastro_escola__diretoria_regional__uuid', lookup_expr='iexact')
    cpf_responsavel = filters.CharFilter(field_name='aluno__responsaveis__cpf', lookup_expr='iexact')
    ativo = filters.BooleanFilter(field_name='ativo')
    tipo_solicitacao = filters.CharFilter(field_name='tipo_solicitacao', lookup_expr='iexact')
    data_inicial = filters.DateFilter(field_name='criado_em', lookup_expr='date__gte')
    data_final = filters.DateFilter(field_name='criado_em', lookup_expr='date__lte')
    classificacao = filters.ModelMultipleChoiceFilter(field_name='classificacao__id',
                                                      to_field_name='id',
                                                      queryset=ClassificacaoDieta.objects.all())
    status = filters.MultipleChoiceFilter(choices=[(str(state), state) for state in DietaEspecialWorkflow.states])


class AlimentoFilter(filters.FilterSet):
    tipo = filters.MultipleChoiceFilter(choices=Alimento.TIPO_CHOICES)
