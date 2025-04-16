import pytest

from sme_sigpae_api.produto.api.filters import (
    FabricanteFilter,
    MarcaFilter,
    ProdutoFilter,
)
from sme_sigpae_api.produto.models import Fabricante, Marca, Produto

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
