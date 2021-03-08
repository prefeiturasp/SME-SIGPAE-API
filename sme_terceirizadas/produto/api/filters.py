from datetime import timedelta

from django_filters import rest_framework as filters

from ...dados_comuns.fluxo_status import HomologacaoProdutoWorkflow
from ..models import Produto
from ..utils import converte_para_datetime, cria_filtro_aditivos


class ProdutoFilter(filters.FilterSet):
    uuid = filters.CharFilter(field_name='homologacoes__uuid', lookup_expr='iexact')
    nome_produto = filters.CharFilter(field_name='nome__unaccent', lookup_expr='icontains')
    data_inicial = filters.DateFilter(field_name='homologacoes__criado_em', lookup_expr='date__gte')
    data_final = filters.DateFilter(field_name='homologacoes__criado_em', lookup_expr='date__lte')
    nome_marca = filters.CharFilter(field_name='marca__nome__unaccent', lookup_expr='icontains')
    nome_fabricante = filters.CharFilter(field_name='fabricante__nome__unaccent', lookup_expr='icontains')
    nome_terceirizada = filters.CharFilter(field_name='homologacoes__rastro_terceirizada__nome_fantasia',
                                           lookup_expr='icontains')
    aditivos = filters.CharFilter(field_name='aditivos', method='filtra_aditivos')

    status = filters.MultipleChoiceFilter(
        field_name='homologacoes__status',
        choices=[(str(state), state) for state in HomologacaoProdutoWorkflow.states]
    )

    class Meta:
        model = Produto
        fields = ['nome_produto',
                  'nome_marca',
                  'nome_fabricante',
                  'nome_terceirizada',
                  'data_inicial',
                  'data_final',
                  'tem_aditivos_alergenicos',
                  'eh_para_alunos_com_dieta']

    def filtra_aditivos(self, qs, name, value):
        filtro = cria_filtro_aditivos(value)
        return qs.filter(filtro)


def filtros_produto_reclamacoes(request):
    status_reclamacao = request.query_params.getlist('status_reclamacao')
    data_inicial_reclamacao = request.query_params.get('data_inicial_reclamacao')
    data_final_reclamacao = request.query_params.get('data_final_reclamacao')
    filtro_homologacao = {}
    filtro_reclamacao = {}

    if status_reclamacao:
        filtro_homologacao['homologacoes__reclamacoes__status__in'] = status_reclamacao
        filtro_reclamacao['status__in'] = status_reclamacao
    if data_inicial_reclamacao:
        data_inicial_reclamacao = converte_para_datetime(data_inicial_reclamacao)
        filtro_homologacao['homologacoes__reclamacoes__criado_em__gte'] = data_inicial_reclamacao
        filtro_reclamacao['criado_em__gte'] = data_inicial_reclamacao
    if data_final_reclamacao:
        data_final_reclamacao = converte_para_datetime(data_final_reclamacao) + timedelta(days=1)
        filtro_homologacao['homologacoes__reclamacoes__criado_em__lte'] = data_final_reclamacao
        filtro_reclamacao['criado_em__lte'] = data_final_reclamacao
    return filtro_reclamacao, filtro_homologacao
