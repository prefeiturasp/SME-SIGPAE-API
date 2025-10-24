from io import BytesIO

import openpyxl
import pandas as pd
import pytest

from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_cieja_cmct import (
    get_alimentacoes_por_periodo,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(relatorio_consolidado_xlsx_cieja):
    colunas = get_alimentacoes_por_periodo([relatorio_consolidado_xlsx_cieja])
    assert isinstance(colunas, list)
    assert len(colunas) == 22
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "TARDE") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 3
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "Solicitações de Alimentação") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "Programas e Projetos") == 3

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 4
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 5
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 3


def test_get_valores_tabela_unidade_cieja(
    relatorio_consolidado_xlsx_cieja, mock_colunas_cieja
):
    linhas = get_valores_tabela([relatorio_consolidado_xlsx_cieja], mock_colunas_cieja)
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 25
    assert linhas[0] == [
        "CIEJA",
        "111329",
        "CIEJA TESTE",
        5.0,
        5.0,
        150.0,
        150.0,
        150.0,
        150,
        150.0,
        150,
        150.0,
        150.0,
        150.0,
        150,
        150.0,
        150,
        "-",
        "-",
        "-",
        80.0,
        80.0,
        40.0,
        40.0,
        40.0,
    ]


def test_insere_tabela_periodos_na_planilha_unidade_cieja(
    mock_colunas_cieja,
    mock_linhas_cieja,
    relatorio_consolidado_xlsx_cieja,
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_cieja.mes}-{relatorio_consolidado_xlsx_cieja.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")

    df = insere_tabela_periodos_na_planilha(
        aba, mock_colunas_cieja, mock_linhas_cieja, writer
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 25
    assert sum(1 for tupla in colunas_df if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "TARDE") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "PROGRAMAS E PROJETOS") == 3
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 3
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 2
    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Kit Lanche") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche Emerg.") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 4h") == 5
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeição") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeições p/ Pagamento") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesa") == 2
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesas p/ Pagamento") == 3

    assert df.iloc[0].tolist() == [
        "CIEJA",
        "111329",
        "CIEJA TESTE",
        5.0,
        5.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        20.0,
        0.0,
        0.0,
        80.0,
        80.0,
        40.0,
        40.0,
        40.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        111329.0,
        0.0,
        5.0,
        5.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        20.0,
        0.0,
        0.0,
        80.0,
        80.0,
        40.0,
        40.0,
        40.0,
    ]
