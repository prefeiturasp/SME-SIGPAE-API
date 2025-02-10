import os
from pathlib import Path

import pytest
from openpyxl import load_workbook

from ..utils import cria_arquivo_excel, meses_to_mes_e_ano_string
from .conftest import mocked_response


def test_meses_para_mes_e_ano_string():
    assert meses_to_mes_e_ano_string(0) == "00 meses"
    assert meses_to_mes_e_ano_string(1) == "01 mês"
    assert meses_to_mes_e_ano_string(2) == "02 meses"
    assert meses_to_mes_e_ano_string(3) == "03 meses"
    assert meses_to_mes_e_ano_string(11) == "11 meses"
    assert meses_to_mes_e_ano_string(12) == "01 ano"
    assert meses_to_mes_e_ano_string(13) == "01 ano e 01 mês"
    assert meses_to_mes_e_ano_string(14) == "01 ano e 02 meses"
    assert meses_to_mes_e_ano_string(15) == "01 ano e 03 meses"
    assert meses_to_mes_e_ano_string(23) == "01 ano e 11 meses"
    assert meses_to_mes_e_ano_string(24) == "02 anos"
    assert meses_to_mes_e_ano_string(25) == "02 anos e 01 mês"
    assert meses_to_mes_e_ano_string(26) == "02 anos e 02 meses"
    assert meses_to_mes_e_ano_string(27) == "02 anos e 03 meses"
    assert meses_to_mes_e_ano_string(35) == "02 anos e 11 meses"
    assert meses_to_mes_e_ano_string(36) == "03 anos"


def test_cria_arquivo_excel():
    dados = [
        {"Nome": "Alice", "Idade": "25", "Cidade": "São Paulo"},
        {"Nome": "Bob", "Idade": "30", "Cidade": "Rio de Janeiro"},
    ]
    caminho_arquivo = Path("/tmp/teste.xlsx")
    cria_arquivo_excel(caminho_arquivo, dados)
    assert caminho_arquivo.exists(), "O arquivo Excel não foi criado."

    wb = load_workbook(caminho_arquivo)
    ws = wb.active

    assert [cell.value for cell in ws[1]] == list(dados[0].keys())

    for idx, row in enumerate(dados, start=2):
        assert [cell.value for cell in ws[idx]] == list(row.values())

    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)
