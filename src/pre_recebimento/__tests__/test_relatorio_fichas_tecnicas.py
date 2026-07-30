import pytest
from rest_framework import status

from src.dados_comuns.fluxo_status import FichaTecnicaDoProdutoWorkflow
from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto


@pytest.mark.django_db
def test_relatorio_listagem_exclui_flv(
    client_autenticado_qualidade, ficha_tecnica_factory
):
    """FLV entries must be excluded from the report."""
    ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )
    ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )
    ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )

    response = client_autenticado_qualidade.get(
        "/ficha-tecnica/listagem-relatorio/"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # 2 non-FLV entries should be returned
    assert data["count"] == 2


@pytest.mark.django_db
def test_relatorio_totalizadores_por_status(
    client_autenticado_qualidade, ficha_tecnica_factory
):
    """Totalizers should reflect correct counts per status."""
    # Create entries with different statuses
    for _ in range(3):
        ficha_tecnica_factory(
            categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
            status=FichaTecnicaDoProdutoWorkflow.APROVADA,
        )
    for _ in range(2):
        ficha_tecnica_factory(
            categoria=FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
            status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO,
        )
    for _ in range(4):
        ficha_tecnica_factory(
            categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
            status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE,
        )

    response = client_autenticado_qualidade.get(
        "/ficha-tecnica/listagem-relatorio/"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    totalizadores = data["totalizadores"]

    assert totalizadores["Total de Fichas Aprovadas"] == 3
    assert totalizadores["Total de Fichas Enviadas para Correção"] == 2
    assert totalizadores["Total de Fichas Pendentes de Aprovação"] == 4


@pytest.mark.django_db
def test_relatorio_filtro_combinado(
    client_autenticado_qualidade, ficha_tecnica_factory, empresa
):
    """Combined filters must work correctly."""
    ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        programa=FichaTecnicaDoProduto.ALIMENTACAO_ESCOLAR,
        empresa=empresa,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )
    ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
        programa=FichaTecnicaDoProduto.LEVE_LEITE,
        empresa=empresa,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )
    ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        programa=FichaTecnicaDoProduto.LEVE_LEITE,
        empresa=empresa,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )

    # Filter by programa = LEVE_LEITE
    response = client_autenticado_qualidade.get(
        "/ficha-tecnica/listagem-relatorio/",
        {"programa": "Leve Leite"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 2


@pytest.mark.django_db
def test_relatorio_paginacao(
    client_autenticado_qualidade, ficha_tecnica_factory
):
    """Pagination should return 10 items per page by default."""
    ficha_tecnica_factory.create_batch(
        size=15,
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )

    response = client_autenticado_qualidade.get(
        "/ficha-tecnica/listagem-relatorio/"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 15
    assert len(data["results"]) == 10  # DefaultPagination page_size = 10


@pytest.mark.django_db
def test_relatorio_zero_resultados(
    client_autenticado_qualidade, ficha_tecnica_factory
):
    """When no entries match filters, count should be 0 and totalizers 0."""
    ficha_tecnica_factory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        programa=FichaTecnicaDoProduto.ALIMENTACAO_ESCOLAR,
        status=FichaTecnicaDoProdutoWorkflow.APROVADA,
    )

    # Filter by a programa that doesn't exist
    response = client_autenticado_qualidade.get(
        "/ficha-tecnica/listagem-relatorio/",
        {"programa": "Leve Leite"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["count"] == 0
    assert data["totalizadores"]["Total de Fichas Aprovadas"] == 0
    assert data["totalizadores"]["Total de Fichas Enviadas para Correção"] == 0
    assert data["totalizadores"]["Total de Fichas Pendentes de Aprovação"] == 0
