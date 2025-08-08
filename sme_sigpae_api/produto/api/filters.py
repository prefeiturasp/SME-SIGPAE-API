from datetime import timedelta

from django.db.models import Q
from django_filters import rest_framework as filters

from sme_sigpae_api.produto.models import Produto
from sme_sigpae_api.produto.utils.genericos import (
    converte_para_datetime,
    cria_filtro_aditivos,
)


class ProdutoFilter(filters.FilterSet):
    uuid = filters.CharFilter(field_name="homologacao__uuid", lookup_expr="iexact")
    nome_produto = filters.CharFilter(
        field_name="nome__unaccent", lookup_expr="icontains"
    )
    data_inicial = filters.DateFilter(
        field_name="homologacao__criado_em", lookup_expr="date__gte"
    )
    data_final = filters.DateFilter(
        field_name="homologacao__criado_em", lookup_expr="date__lte"
    )
    nome_marca = filters.CharFilter(
        field_name="marca__nome__unaccent", lookup_expr="icontains"
    )
    nome_fabricante = filters.CharFilter(
        field_name="fabricante__nome__unaccent", lookup_expr="icontains"
    )
    nome_terceirizada = filters.CharFilter(
        field_name="homologacao__rastro_terceirizada__nome_fantasia",
        lookup_expr="icontains",
    )
    aditivos = filters.CharFilter(field_name="aditivos", method="filtra_aditivos")
    nome_edital = filters.CharFilter(
        field_name="vinculos__edital__numero", lookup_expr="iexact"
    )

    class Meta:
        model = Produto
        fields = [
            "nome_produto",
            "nome_marca",
            "nome_fabricante",
            "nome_terceirizada",
            "data_inicial",
            "data_final",
            "tem_aditivos_alergenicos",
        ]

    def filtra_aditivos(self, qs, name, value):
        filtro = cria_filtro_aditivos(value)
        return qs.filter(filtro)


def aplica_filtro_editais(editais, filtro_reclamacao, filtro_homologacao):
    if editais:
        filtro_reclamacao["escola__lote__contratos_do_lote__edital__numero__in"] = (
            editais
        )
        filtro_reclamacao["escola__lote__contratos_do_lote__encerrado"] = False
        filtro_homologacao[
            "homologacao__reclamacoes__escola__lote__contratos_do_lote__edital__numero__in"
        ] = editais
        filtro_homologacao[
            "homologacao__reclamacoes__escola__lote__contratos_do_lote__encerrado"
        ] = False


def aplica_filtro_lotes(lotes, filtro_reclamacao, filtro_homologacao):
    if lotes:
        filtro_reclamacao["escola__lote__uuid__in"] = lotes
        filtro_homologacao["homologacao__reclamacoes__escola__lote__uuid__in"] = lotes


def aplica_filtro_terceirizadas(terceirizadas, filtro_reclamacao, filtro_homologacao):
    if terceirizadas:
        filtro_reclamacao["escola__lote__terceirizada__uuid__in"] = terceirizadas
        filtro_homologacao[
            "homologacao__reclamacoes__escola__lote__terceirizada__uuid__in"
        ] = terceirizadas


def aplica_filtro_status(status_reclamacao, filtro_reclamacao, filtro_homologacao):
    if status_reclamacao:
        filtro_reclamacao["status__in"] = status_reclamacao
        filtro_homologacao["homologacao__reclamacoes__status__in"] = status_reclamacao


def aplica_filtro_datas(
    data_inicial_reclamacao,
    data_final_reclamacao,
    filtro_reclamacao,
    filtro_homologacao,
):
    if data_inicial_reclamacao:
        data_inicial = converte_para_datetime(data_inicial_reclamacao)
        filtro_reclamacao["criado_em__gte"] = data_inicial
        filtro_homologacao["homologacao__reclamacoes__criado_em__gte"] = data_inicial
    if data_final_reclamacao:
        data_final = converte_para_datetime(data_final_reclamacao) + timedelta(days=1)
        filtro_reclamacao["criado_em__lte"] = data_final
        filtro_homologacao["homologacao__reclamacoes__criado_em__lte"] = data_final


def filtros_produto_reclamacoes(request):
    editais = request.query_params.getlist("editais[]")
    lotes = request.query_params.getlist("lotes[]")
    terceirizadas = request.query_params.getlist("terceirizadas[]")
    status_reclamacao = request.query_params.getlist("status_reclamacao[]")
    data_inicial_reclamacao = request.query_params.get("data_inicial_reclamacao")
    data_final_reclamacao = request.query_params.get("data_final_reclamacao")

    filtro_reclamacao = {}
    filtro_homologacao = {}

    aplica_filtro_editais(editais, filtro_reclamacao, filtro_homologacao)
    aplica_filtro_lotes(lotes, filtro_reclamacao, filtro_homologacao)
    aplica_filtro_terceirizadas(terceirizadas, filtro_reclamacao, filtro_homologacao)
    aplica_filtro_status(status_reclamacao, filtro_reclamacao, filtro_homologacao)
    aplica_filtro_datas(
        data_inicial_reclamacao,
        data_final_reclamacao,
        filtro_reclamacao,
        filtro_homologacao,
    )

    return filtro_reclamacao, filtro_homologacao


class ItemCadastroFilter(filters.FilterSet):
    nome = filters.CharFilter(method="filtra_nome", lookup_expr="icontains")
    tipo = filters.CharFilter(field_name="tipo", lookup_expr="iexact")

    def filtra_nome(self, qs, _, value):
        return qs.filter(
            Q(fabricante__nome__icontains=value)
            | Q(marca__nome__icontains=value)
            | Q(unidade_medida__nome__icontains=value)
            | Q(embalagem_produto__nome__icontains=value)
        )


class CadastroProdutosEditalFilter(filters.FilterSet):
    nome = filters.CharFilter(field_name="nome", lookup_expr="icontains")
    status = filters.CharFilter(field_name="ativo", method="filtra_status")
    data_cadastro = filters.DateFilter(
        field_name="criado_em__date",
        lookup_expr="exact",
    )

    def filtra_status(self, qs, name, value):
        filtro = False if value == "Inativo" else True
        return qs.filter(ativo=filtro)


class MarcaFilter(filters.FilterSet):
    nome_edital = filters.CharFilter(
        field_name="produto__vinculos__edital__numero", lookup_expr="iexact"
    )


class FabricanteFilter(filters.FilterSet):
    nome_edital = filters.CharFilter(
        field_name="produto__vinculos__edital__numero", lookup_expr="iexact"
    )
