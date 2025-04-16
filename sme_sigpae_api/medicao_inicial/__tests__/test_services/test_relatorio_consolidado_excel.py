from io import BytesIO

import openpyxl
import pandas as pd
import pytest
from openpyxl import load_workbook

from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_excel import (
    _get_alimentacoes_por_periodo,
    _get_valores_tabela,
    _insere_tabela_periodos_na_planilha,
    _preenche_titulo,
    gera_relatorio_consolidado_xlsx,
)

pytestmark = pytest.mark.django_db


def test_gera_relatorio_consolidado_xlsx(
    mock_relatorio_consolidado_xlsx, grupo_escolar
):
    solicitacoes = [mock_relatorio_consolidado_xlsx.uuid]
    tipos_unidade = ["EMEF"]
    query_params = {
        "dre": mock_relatorio_consolidado_xlsx.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": mock_relatorio_consolidado_xlsx.mes,
        "ano": mock_relatorio_consolidado_xlsx.ano,
        "lotes[]": mock_relatorio_consolidado_xlsx.escola.lote.uuid,
        "lotes": [mock_relatorio_consolidado_xlsx.escola.lote.uuid],
    }
    arquivo = gera_relatorio_consolidado_xlsx(solicitacoes, tipos_unidade, query_params)
    assert isinstance(arquivo, bytes)
    excel_buffer = BytesIO(arquivo)

    workbook = load_workbook(filename=excel_buffer)
    nome_aba = f"Relatório Consolidado { mock_relatorio_consolidado_xlsx.mes}-{ mock_relatorio_consolidado_xlsx.ano}"
    assert nome_aba in workbook.sheetnames
    sheet = workbook[nome_aba]
    rows = list(sheet.iter_rows(values_only=True))
    assert rows[0] == (
        "Relatório de Totalização da Medição Inicial do Serviço de Fornecimento da Alimentação Escolar",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert rows[1] == (
        "ABRIL/2025 - DIRETORIA REGIONAL IPIRANGA - 1 - EMEF",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert rows[2] == (
        None,
        None,
        None,
        "MANHA",
        None,
        None,
        None,
        None,
        None,
        "TARDE",
        None,
        None,
        None,
        None,
        None,
        "DIETA ESPECIAL - TIPO A",
        None,
        None,
        None,
        "DIETA ESPECIAL - TIPO B",
        None,
        None,
        None,
    )
    assert rows[3] == (
        "Tipo",
        "Cód. EOL",
        "Unidade Escolar",
        "Lanche 5h",
        "Refeição",
        "Refeições p/ Pagamento",
        "Sobremesa",
        "Sobremesas p/ Pagamento",
        "Lanche Emerg.",
        "Lanche 5h",
        "Refeição",
        "Refeições p/ Pagamento",
        "Sobremesa",
        "Sobremesas p/ Pagamento",
        "Lanche Emerg.",
        "Lanche 5h",
        "Refeição",
        "Sobremesa",
        "Lanche Emerg.",
        "Lanche 5h",
        "Refeição",
        "Sobremesa",
        "Lanche Emerg.",
    )
    assert rows[4] == (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert rows[5] == (
        "EMEF",
        "123456",
        "EMEF TESTE",
        150,
        150,
        0,
        150,
        0,
        150,
        150,
        150,
        0,
        150,
        0,
        150,
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    )
    assert rows[6] == (
        "TOTAL",
        None,
        None,
        150,
        150,
        0,
        150,
        0,
        150,
        150,
        150,
        0,
        150,
        0,
        150,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )


def test_get_alimentacoes_por_periodo(mock_relatorio_consolidado_xlsx):
    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
    assert isinstance(colunas, list)
    assert len(colunas) == 20
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "TARDE") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 4
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 4


def test_get_valores_tabela(mock_relatorio_consolidado_xlsx):
    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
    linhas = _get_valores_tabela([mock_relatorio_consolidado_xlsx], colunas)
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 23
    assert linhas[0] == [
        "EMEF",
        "123456",
        "EMEF TESTE",
        150,
        150,
        0,
        150,
        0,
        150,
        150,
        150,
        0,
        150,
        0,
        150,
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    ]


def test_insere_tabela_periodos_na_planilha(mock_relatorio_consolidado_xlsx):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {mock_relatorio_consolidado_xlsx.mes}-{ mock_relatorio_consolidado_xlsx.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
    linhas = _get_valores_tabela([mock_relatorio_consolidado_xlsx], colunas)
    df = _insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer)
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 23
    assert sum(1 for tupla in colunas_df if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "TARDE") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 4
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert df.iloc[0].tolist() == [
        "EMEF",
        "123456",
        "EMEF TESTE",
        150.0,
        150.0,
        0.0,
        150.0,
        0.0,
        150.0,
        150.0,
        150.0,
        0.0,
        150.0,
        0.0,
        150.0,
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        123456.0,
        0.0,
        150.0,
        150.0,
        0.0,
        150.0,
        0.0,
        150.0,
        150.0,
        150.0,
        0.0,
        150.0,
        0.0,
        150.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ]


def test_preenche_titulo(mock_relatorio_consolidado_xlsx):
    file = BytesIO()
    aba = f"Relatório Consolidado {mock_relatorio_consolidado_xlsx.mes}-{ mock_relatorio_consolidado_xlsx.ano}"
    writer = pd.ExcelWriter(file, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)

    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
    linhas = _get_valores_tabela([mock_relatorio_consolidado_xlsx], colunas)
    df = _insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer)
    _preenche_titulo(workbook, worksheet, df.columns)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(file)
    sheet = workbook_openpyxl[aba]
    assert (
        sheet["A1"].value
        == "Relatório de Totalização da Medição Inicial do Serviço de Fornecimento da Alimentação Escolar"
    )
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 6
    assert str(merged_ranges[0]) == "A3:C3"
    assert str(merged_ranges[1]) == "D3:I3"
    assert str(merged_ranges[2]) == "J3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "T3:W3"
    assert str(merged_ranges[5]) == "A1:W1"

    assert sheet["A1"].alignment.horizontal == "center"
    assert sheet["A1"].alignment.vertical == "center"
    assert sheet["A1"].font.bold is True
    assert sheet["A1"].font.color.rgb == "FF42474A"
    assert sheet["A1"].fill.fgColor.rgb == "FFD6F2E7"

    workbook_openpyxl.close()


def test_preenche_linha_dos_filtros_selecionados():
    pass


def test_ajusta_layout_tabela():
    pass


def test_formata_total_geral():
    pass
