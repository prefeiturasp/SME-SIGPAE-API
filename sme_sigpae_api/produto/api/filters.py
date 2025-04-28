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


def filtros_produto_reclamacoes(request):
    status_reclamacao = request.query_params.getlist("status_reclamacao")
    data_inicial_reclamacao = request.query_params.get("data_inicial_reclamacao")
    data_final_reclamacao = request.query_params.get("data_final_reclamacao")
    filtro_homologacao = {}
    filtro_reclamacao = {}

    if status_reclamacao:
        filtro_homologacao["homologacao__reclamacoes__status__in"] = status_reclamacao
        filtro_reclamacao["status__in"] = status_reclamacao
    if data_inicial_reclamacao:
        data_inicial_reclamacao = converte_para_datetime(data_inicial_reclamacao)
        filtro_homologacao[
            "homologacao__reclamacoes__criado_em__gte"
        ] = data_inicial_reclamacao
        filtro_reclamacao["criado_em__gte"] = data_inicial_reclamacao
    if data_final_reclamacao:
        data_final_reclamacao = converte_para_datetime(
            data_final_reclamacao
        ) + timedelta(days=1)
        filtro_homologacao[
            "homologacao__reclamacoes__criado_em__lte"
        ] = data_final_reclamacao
        filtro_reclamacao["criado_em__lte"] = data_final_reclamacao
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
