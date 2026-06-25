from io import BytesIO

import openpyxl
import pandas as pd
import pytest

from src.medicao_inicial.services.relatorio_consolidado_recreio_emei_emef import (
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(solicitacao_recreio_emei):
    colunas = get_alimentacoes_por_periodo([solicitacao_recreio_emei], {})
    assert isinstance(colunas, list)
    assert len(colunas) == 13
    assert sum(1 for tupla in colunas if tupla[0] == "Recreio nas Férias") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 1
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "Colaboradores") == 6

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 2


def test_get_valores_tabela_unidade_emei(
    solicitacao_recreio_emei, mock_colunas_recreio_emei
):
    tipos_unidade = ["EMEI"]
    linhas = get_valores_tabela(
        [solicitacao_recreio_emei], mock_colunas_recreio_emei, tipos_unidade, {}
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 16
    assert linhas[0] == [
        "EMEI",
        "987654",
        "EMEI TESTE",
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        "-",
        280.0,
        280.0,
        280.0,
        280.0,
        280.0,
        280.0,
    ]


def test_insere_tabela_periodos_na_planilha_unidade_emei(
    solicitacao_recreio_emei, mock_colunas_recreio_emei, mock_linhas_recreio_emei
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {solicitacao_recreio_emei.mes}-{ solicitacao_recreio_emei.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")

    df = insere_tabela_periodos_na_planilha(
        aba, mock_colunas_recreio_emei, mock_linhas_recreio_emei, writer
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 16
    assert (
        sum(
            1 for tupla in colunas_df if tupla[0] == "ALIMENTAÇÕES ALUNOS PARTICIPANTES"
        )
        == 6
    )
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 1
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Kit Lanche") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche Emerg.") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 4h") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeição") == 3
    assert (
        sum(
            1 for tupla in colunas_df if tupla[1] == "Total de Refeições para Pagamento"
        )
        == 2
    )
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesa") == 2
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[1] == "Total de Sobremesas para Pagamento"
        )
        == 2
    )
    assert sum(1 for tupla in colunas_df if tupla[0] == "COLABORADORES") == 6

    assert df.iloc[0].tolist() == [
        "EMEI",
        "987654",
        "EMEI TESTE",
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        "-",
        280.0,
        280.0,
        280.0,
        280.0,
        280.0,
        280.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        987654.0,
        0.0,
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        1260.0,
        0.0,
        280.0,
        280.0,
        280.0,
        280.0,
        280.0,
        280.0,
    ]


def test_ajusta_layout_tabela(informacoes_excel_writer_recreio_emei):
    aba, writer, workbook, worksheet, df, arquivo = (
        informacoes_excel_writer_recreio_emei
    )
    ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 3
    esperados = {"A3:C3", "D3:I3", "K3:P3"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A3"].value is None
    assert sheet["D3"].value == "ALIMENTAÇÕES ALUNOS PARTICIPANTES"
    assert sheet["D3"].fill.fgColor.rgb == "FF198459"
    assert sheet["J3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["K3"].value == "COLABORADORES"
    assert sheet["K3"].fill.fgColor.rgb == "FFB40C02"
    workbook_openpyxl.close()
