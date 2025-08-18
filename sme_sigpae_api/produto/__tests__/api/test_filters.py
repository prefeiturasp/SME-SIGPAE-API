import datetime
from unittest.mock import Mock

import pytest

from sme_sigpae_api.produto.api.filters import (
    CadastroProdutosEditalFilter,
    FabricanteFilter,
    ItemCadastroFilter,
    MarcaFilter,
    ProdutoFilter,
    filtros_produto_reclamacoes,
)
from sme_sigpae_api.produto.models import (
    Fabricante,
    ItemCadastro,
    Marca,
    NomeDeProdutoEdital,
    Produto,
)

pytestmark = pytest.mark.django_db


def test_produto_filter(produtos_edital_41):
    nome_produto = "ARROZ"
    nome_marca = "NAMORADOS"
    nome_fabricante = "Fabricante 001"
    nome_edital = "Edital de Pregão nº 78/sme/2022"

    filtro_nome_produto = ProdutoFilter(
        data={"nome_produto": nome_produto}, queryset=Produto.objects.all()
    )
    assert filtro_nome_produto.qs.count() == 2

    filtro_nome_fabricante = ProdutoFilter(
        data={"nome_fabricante": nome_fabricante}, queryset=Produto.objects.all()
    )
    assert filtro_nome_fabricante.qs.count() == 1

    filtro_nome_marca = ProdutoFilter(
        data={"nome_marca": nome_marca}, queryset=Produto.objects.all()
    )
    assert filtro_nome_marca.qs.count() == 1

    filtro_nome_edital = ProdutoFilter(
        data={"nome_edital": nome_edital}, queryset=Produto.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 1

    filtro = ProdutoFilter(
        data={
            "nome_produto": nome_produto,
            "nome_marca": nome_marca,
            "nome_edital": nome_edital,
            "nome_fabricante": nome_fabricante,
        },
        queryset=Produto.objects.all(),
    )
    assert filtro.qs.count() == 1
    produto = filtro.qs[0]

    assert produto.nome == nome_produto
    assert produto.marca.nome == nome_marca
    assert produto.vinculos.filter(edital__numero=nome_edital).count() == 1

    filtro_aditivos = ProdutoFilter(
        data={"aditivos": "Ad1, Ad2"}, queryset=Produto.objects.all()
    )
    assert filtro_aditivos.qs.count() == 0


def test_marca_filter(produtos_edital_41):
    nome_marca_1 = "NAMORADOS"
    nome_marca_2 = "TIO JOÃO"
    nome_edital_2022 = "Edital de Pregão nº 78/sme/2022"
    nome_edital_2017 = "Edital de Pregão nº 41/sme/2017"
    nome_edital_2016 = "Edital de Pregão nº 78/sme/2016"

    filtro_nome_edital = MarcaFilter(
        data={"nome_edital": nome_edital_2022}, queryset=Marca.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 1
    marca = filtro_nome_edital.qs[0]
    assert marca.nome == nome_marca_1

    filtro_nome_edital = MarcaFilter(
        data={"nome_edital": nome_edital_2017}, queryset=Marca.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 2
    marca = filtro_nome_edital.qs[0]
    assert marca.nome == nome_marca_1
    marca = filtro_nome_edital.qs[1]
    assert marca.nome == nome_marca_2

    filtro_nome_edital = MarcaFilter(
        data={"nome_edital": nome_edital_2016}, queryset=Marca.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 0


def test_fabricante_filter(produtos_edital_41):
    nome_marca_1 = "NAMORADOS"
    nome_marca_2 = "TIO JOÃO"
    nome_edital_2022 = "Edital de Pregão nº 78/sme/2022"
    nome_edital_2017 = "Edital de Pregão nº 41/sme/2017"
    nome_edital_2016 = "Edital de Pregão nº 78/sme/2016"

    filtro_nome_edital = MarcaFilter(
        data={"nome_edital": nome_edital_2022}, queryset=Marca.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 1
    marca = filtro_nome_edital.qs[0]
    assert marca.nome == nome_marca_1

    filtro_nome_edital = MarcaFilter(
        data={"nome_edital": nome_edital_2017}, queryset=Marca.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 2
    marca = filtro_nome_edital.qs[0]
    assert marca.nome == nome_marca_1
    marca = filtro_nome_edital.qs[1]
    assert marca.nome == nome_marca_2

    filtro_nome_edital = MarcaFilter(
        data={"nome_edital": nome_edital_2016}, queryset=Marca.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 0


def test_fabricante_filter(produtos_edital_41):
    nome_fabricante_1 = "Fabricante 001"
    nome_fabricante_2 = "Fabricante 002"
    nome_edital_2022 = "Edital de Pregão nº 78/sme/2022"
    nome_edital_2017 = "Edital de Pregão nº 41/sme/2017"
    nome_edital_2016 = "Edital de Pregão nº 78/sme/2016"

    filtro_nome_edital = FabricanteFilter(
        data={"nome_edital": nome_edital_2022}, queryset=Fabricante.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 1
    fabricante = filtro_nome_edital.qs[0]
    assert fabricante.nome == nome_fabricante_1

    filtro_nome_edital = FabricanteFilter(
        data={"nome_edital": nome_edital_2017}, queryset=Fabricante.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 2
    assert list(filtro_nome_edital.qs.values_list("nome", flat=True)) == [
        nome_fabricante_1,
        nome_fabricante_2,
    ]

    filtro_nome_edital = FabricanteFilter(
        data={"nome_edital": nome_edital_2016}, queryset=Fabricante.objects.all()
    )
    assert filtro_nome_edital.qs.count() == 0


def test_filtros_produto_reclamacoes():
    from django.http import QueryDict

    query_params = QueryDict(mutable=True)
    query_params.setlist(
        "status_reclamacao[]",
        ["APROVADO", "REPROVADO"],
    )
    query_params.setlist("editais[]", ["Edital 1", "Edital 2"])
    query_params.setlist("lotes[]", ["Lote 1", "Lote 2"])
    query_params.setlist("terceirizadas[]", ["Terceirizada 1", "Terceirizada 2"])
    query_params["data_inicial_reclamacao"] = "01/04/2025"
    query_params["data_final_reclamacao"] = "12/04/2025"

    mock_request = Mock()
    mock_request.query_params = query_params
    filtro_reclamacao, filtro_homologacao = filtros_produto_reclamacoes(mock_request)

    data_inicial_reclamacao = datetime.datetime(2025, 4, 1)
    data_final_reclamacao = datetime.datetime(2025, 4, 13)

    assert filtro_reclamacao == {
        "status__in": ["APROVADO", "REPROVADO"],
        "escola__lote__contratos_do_lote__edital__numero__in": ["Edital 1", "Edital 2"],
        "escola__lote__contratos_do_lote__encerrado": False,
        "escola__lote__uuid__in": ["Lote 1", "Lote 2"],
        "escola__lote__terceirizada__uuid__in": ["Terceirizada 1", "Terceirizada 2"],
        "criado_em__gte": data_inicial_reclamacao,
        "criado_em__lte": data_final_reclamacao,
    }

    assert filtro_homologacao == {
        "homologacao__reclamacoes__status__in": ["APROVADO", "REPROVADO"],
        "homologacao__reclamacoes__escola__lote__contratos_do_lote__edital__numero__in": [
            "Edital 1",
            "Edital 2",
        ],
        "homologacao__reclamacoes__escola__lote__contratos_do_lote__encerrado": False,
        "homologacao__reclamacoes__escola__lote__uuid__in": ["Lote 1", "Lote 2"],
        "homologacao__reclamacoes__escola__lote__terceirizada__uuid__in": [
            "Terceirizada 1",
            "Terceirizada 2",
        ],
        "homologacao__reclamacoes__criado_em__gte": data_inicial_reclamacao,
        "homologacao__reclamacoes__criado_em__lte": data_final_reclamacao,
    }


def test_cadastro_produtos_edital_filter(produto_edital):
    filtro_nome = CadastroProdutosEditalFilter(
        data={"nome": produto_edital.nome}, queryset=NomeDeProdutoEdital.objects.all()
    )
    assert filtro_nome.qs.count() == 1
    assert filtro_nome.qs[0] == produto_edital

    filtro_status = CadastroProdutosEditalFilter(
        data={"status": produto_edital.ativo},
        queryset=NomeDeProdutoEdital.objects.all(),
    )
    assert filtro_status.qs.count() == 1
    assert filtro_status.qs[0] == produto_edital

    filtro_status = CadastroProdutosEditalFilter(
        data={"data_cadastro": produto_edital.criado_em},
        queryset=NomeDeProdutoEdital.objects.all(),
    )
    assert filtro_status.qs.count() == 1
    assert filtro_status.qs[0] == produto_edital


def test_item_cadastro_filter(item_cadastrado_2, fabricante):
    filtro_nome = ItemCadastroFilter(
        data={"nome": fabricante.nome},
        queryset=ItemCadastro.objects.all().order_by("-criado_em"),
    )
    assert filtro_nome.qs.count() == 1
    assert filtro_nome.qs[0] == item_cadastrado_2

    filtro_tipo = ItemCadastroFilter(
        data={"tipo": item_cadastrado_2.tipo},
        queryset=ItemCadastro.objects.all().order_by("-criado_em"),
    )
    assert filtro_tipo.qs.count() == 1
    assert filtro_tipo.qs[0] == item_cadastrado_2
