from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from sme_sigpae_api.terceirizada.utils import (
    TerceirizadasEmailsPagination,
    obtem_dados_relatorio_quantitativo,
    serializa_emails_terceirizadas,
    transforma_dados_relatorio_quantitativo,
)


@pytest.mark.django_db
def test_obtem_dados_relatorio_quantitativo(mock_form_data, mock_connection):
    """Testa a função `obtem_dados_relatorio_quantitativo`."""
    form_data = mock_form_data
    form_data["nome_terceirizada"] = "Terceirizada A"
    form_data["data_inicial"] = datetime(2024, 1, 1)
    form_data["data_final"] = datetime(2024, 1, 31)

    resultado = obtem_dados_relatorio_quantitativo(form_data)

    assert "results" in resultado
    assert len(resultado["results"]) == 2
    assert resultado["results"][0]["nome_terceirizada"] == "Terceirizada A"
    assert resultado["results"][0]["qtde_por_status"] == [
        {"status": "CODAE_HOMOLOGADO", "qtde": 5},
        {"status": "CODAE_QUESTIONADO", "qtde": 3},
    ]


def test_transforma_dados_relatorio_quantitativo():
    """Testa a função `transforma_dados_relatorio_quantitativo`."""
    dados_mock = {
        "results": [
            {
                "nome_terceirizada": "Terceirizada A",
                "qtde_por_status": [
                    {"status": "CODAE_HOMOLOGADO", "qtde": 5},
                    {"status": "CODAE_QUESTIONADO", "qtde": 3},
                ],
            }
        ],
        "dias": 30,
    }

    resultado = transforma_dados_relatorio_quantitativo(dados_mock)

    assert "totalProdutos" in resultado
    assert resultado["totalProdutos"] == 8
    assert "detalhes" in resultado
    assert resultado["detalhes"][0]["nomeTerceirizada"] == "Terceirizada A"
    assert resultado["qtdeDias"] == 30


def test_terceirizadas_emails_pagination():
    """Testa a classe `TerceirizadasEmailsPagination`."""
    pagination = TerceirizadasEmailsPagination()

    assert pagination.page_size == 10
    assert pagination.page_size_query_param == "page_size"
    assert pagination.max_page_size == 100
