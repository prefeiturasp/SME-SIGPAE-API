from io import BytesIO

import openpyxl
import pandas as pd
import pytest
from openpyxl import load_workbook

from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_excel import (
    _ajusta_layout_tabela,
    _formata_filtros,
    _formata_total_geral,
    _insere_tabela_periodos_na_planilha,
    _preenche_linha_dos_filtros_selecionados,
    _preenche_titulo,
    gera_relatorio_consolidado_xlsx,
)

pytestmark = pytest.mark.django_db


def test_gera_relatorio_consolidado_xlsx_emef(
    relatorio_consolidado_xlsx_emef, mock_query_params_excel_emef
):
    solicitacoes = [relatorio_consolidado_xlsx_emef.uuid]
    tipos_unidade = ["EMEF"]
    arquivo = gera_relatorio_consolidado_xlsx(
        solicitacoes, tipos_unidade, mock_query_params_excel_emef
    )
    assert isinstance(arquivo, bytes)
    excel_buffer = BytesIO(arquivo)

    workbook = load_workbook(filename=excel_buffer)
    nome_aba = f"Relatório Consolidado { relatorio_consolidado_xlsx_emef.mes}-{ relatorio_consolidado_xlsx_emef.ano}"
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
    )
    assert rows[2] == (
        None,
        None,
        None,
        None,
        None,
        "MANHA",
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
        "Kit Lanche",
        "Lanche Emerg.",
        "Lanche",
        "Lanche 4h",
        "Refeição",
        "Refeições p/ Pagamento",
        "Sobremesa",
        "Sobremesas p/ Pagamento",
        "Lanche",
        "Lanche 4h",
        "Refeição",
        "Sobremesa",
        "Lanche",
        "Lanche 4h",
        "Refeição",
        "Sobremesa",
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
    )
    assert rows[5] == (
        "EMEF",
        "123456",
        "EMEF TESTE",
        10,
        10,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
    )
    assert rows[6] == (
        "TOTAL",
        None,
        None,
        10,
        10,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
        125,
    )


def test_gera_relatorio_consolidado_xlsx_emei(
    relatorio_consolidado_xlsx_emei, mock_query_params_excel_emei
):
    solicitacoes = [relatorio_consolidado_xlsx_emei.uuid]
    tipos_unidade = ["EMEI"]
    arquivo = gera_relatorio_consolidado_xlsx(
        solicitacoes, tipos_unidade, mock_query_params_excel_emei
    )
    assert isinstance(arquivo, bytes)
    excel_buffer = BytesIO(arquivo)

    workbook = load_workbook(filename=excel_buffer)
    nome_aba = f"Relatório Consolidado { relatorio_consolidado_xlsx_emei.mes}-{ relatorio_consolidado_xlsx_emei.ano}"
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
    )
    assert rows[1] == (
        "ABRIL/2025 - DIRETORIA REGIONAL TESTE -  - EMEI",
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
        None,
        None,
        "MANHA",
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
        "Kit Lanche",
        "Lanche Emerg.",
        "Lanche",
        "Lanche 4h",
        "Refeição",
        "Refeições p/ Pagamento",
        "Sobremesa",
        "Sobremesas p/ Pagamento",
        "Lanche",
        "Lanche 4h",
        "Refeição",
        "Sobremesa",
        "Lanche",
        "Lanche 4h",
        "Refeição",
        "Sobremesa",
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
    )
    assert rows[5] == (
        "EMEI",
        "987654",
        "EMEI TESTE",
        5,
        5,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
    )
    assert rows[6] == (
        "TOTAL",
        None,
        None,
        5,
        5,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
        150,
    )


def test_insere_tabela_periodos_na_planilha_unidade_emef(
    informacoes_excel_writer_emef, mock_colunas, mock_linhas_emef
):
    aba, writer, _, _, _, _ = informacoes_excel_writer_emef

    df = _insere_tabela_periodos_na_planilha(
        ["EMEF"], aba, mock_colunas, mock_linhas_emef, writer
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 19
    assert sum(1 for tupla in colunas_df if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 4
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Kit Lanche") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche Emerg.") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 4h") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeição") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeições p/ Pagamento") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesa") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesas p/ Pagamento") == 1

    assert df.iloc[0].tolist() == [
        "EMEF",
        "123456",
        "EMEF TESTE",
        10.0,
        10.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        123456.0,
        0.0,
        10.0,
        10.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
    ]


def test_insere_tabela_periodos_na_planilha_unidade_emei(
    informacoes_excel_writer_emei, mock_colunas, mock_linhas_emei
):
    aba, writer, _, _, _, _ = informacoes_excel_writer_emei

    df = _insere_tabela_periodos_na_planilha(
        ["EMEI"], aba, mock_colunas, mock_linhas_emei, writer
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 19
    assert sum(1 for tupla in colunas_df if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 4
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Kit Lanche") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche Emerg.") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 4h") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeição") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeições p/ Pagamento") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesa") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesas p/ Pagamento") == 1

    assert df.iloc[0].tolist() == [
        "EMEI",
        "987654",
        "EMEI TESTE",
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
        150.0,
        150.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        987654.0,
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
        150.0,
        150.0,
    ]


def test_preenche_titulo(informacoes_excel_writer_emef):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emef
    _preenche_titulo(workbook, worksheet, df.columns)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]

    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 5
    esperados = {"A3:E3", "F3:K3", "L3:O3", "P3:S3", "A1:S1"}
    assert {str(r) for r in merged_ranges} == esperados

    assert (
        sheet["A1"].value
        == "Relatório de Totalização da Medição Inicial do Serviço de Fornecimento da Alimentação Escolar"
    )
    assert sheet["A1"].alignment.horizontal == "center"
    assert sheet["A1"].alignment.vertical == "center"
    assert sheet["A1"].font.bold is True
    assert sheet["A1"].font.color.rgb == "FF42474A"
    assert sheet["A1"].fill.fgColor.rgb == "FFD6F2E7"
    workbook_openpyxl.close()


def test_preenche_linha_dos_filtros_selecionados_unidade_emef(
    mock_query_params_excel_emef, informacoes_excel_writer_emef
):
    tipos_unidades = ["EMEF"]
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emef
    _preenche_linha_dos_filtros_selecionados(
        workbook, worksheet, mock_query_params_excel_emef, df.columns, tipos_unidades
    )
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]

    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 5
    esperados = {"A3:E3", "F3:K3", "L3:O3", "P3:S3", "A2:S2"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A2"].value == "ABRIL/2025 - DIRETORIA REGIONAL IPIRANGA - 1 - EMEF"
    assert sheet["A2"].alignment.horizontal == "center"
    assert sheet["A2"].alignment.vertical == "center"
    assert sheet["A2"].font.bold is True
    assert sheet["A2"].font.color.rgb == "FF0C6B45"
    assert sheet["A2"].fill.fgColor.rgb == "FFEAFFF6"

    rows = list(sheet.iter_rows(values_only=True))
    assert tipos_unidades[0] in rows[1][0]
    workbook_openpyxl.close()


def test_preenche_linha_dos_filtros_selecionados_unidade_emei(
    mock_query_params_excel_emei, informacoes_excel_writer_emei
):
    tipos_unidades = ["EMEI"]
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emei
    _preenche_linha_dos_filtros_selecionados(
        workbook, worksheet, mock_query_params_excel_emei, df.columns, tipos_unidades
    )
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]

    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 5
    esperados = {"A3:E3", "F3:K3", "L3:O3", "P3:S3", "A2:S2"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A2"].value == "ABRIL/2025 - DIRETORIA REGIONAL TESTE -  - EMEI"
    assert sheet["A2"].alignment.horizontal == "center"
    assert sheet["A2"].alignment.vertical == "center"
    assert sheet["A2"].font.bold is True
    assert sheet["A2"].font.color.rgb == "FF0C6B45"
    assert sheet["A2"].fill.fgColor.rgb == "FFEAFFF6"

    rows = list(sheet.iter_rows(values_only=True))
    assert tipos_unidades[0] in rows[1][0]
    workbook_openpyxl.close()


def test_ajusta_layout_tabela_emef(informacoes_excel_writer_emef):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emef
    _ajusta_layout_tabela(["EMEF"], workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 4
    esperados = {"A3:E3", "F3:K3", "L3:O3", "P3:S3"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A3"].value is None
    assert sheet["F3"].value == "MANHA"
    assert sheet["F3"].fill.fgColor.rgb == "FF198459"
    assert sheet["L3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["L3"].fill.fgColor.rgb == "FF198459"
    assert sheet["P3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["P3"].fill.fgColor.rgb == "FF20AA73"
    workbook_openpyxl.close()


def test_ajusta_layout_tabela_emei(informacoes_excel_writer_emei):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emei
    _ajusta_layout_tabela(["EMEI"], workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 4
    esperados = {"A3:E3", "F3:K3", "L3:O3", "P3:S3"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A3"].value is None
    assert sheet["F3"].value == "MANHA"
    assert sheet["F3"].fill.fgColor.rgb == "FF198459"
    assert sheet["L3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["L3"].fill.fgColor.rgb == "FF198459"
    assert sheet["P3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["P3"].fill.fgColor.rgb == "FF20AA73"
    workbook_openpyxl.close()


def test_formata_total_geral(informacoes_excel_writer_emef):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emef
    _formata_total_geral(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 5
    esperados = {"A3:E3", "F3:K3", "L3:O3", "P3:S3", "A7:C7"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A7"].value == "TOTAL"
    assert sheet["A7"].alignment.horizontal == "center"
    assert sheet["A7"].alignment.vertical == "center"
    assert sheet["A7"].font.bold is True
    workbook_openpyxl.close()


def test_formata_filtros_unidade_emef(mock_query_params_excel_emef):
    tipos_unidades = ["EMEF"]
    filtros = _formata_filtros(mock_query_params_excel_emef, tipos_unidades)
    assert isinstance(filtros, str)
    assert filtros == "Abril/2025 - DIRETORIA REGIONAL IPIRANGA - 1 - EMEF"


def test_formata_filtros_unidade_emei(mock_query_params_excel_emei):
    tipos_unidades = ["EMEI"]
    filtros = _formata_filtros(mock_query_params_excel_emei, tipos_unidades)
    assert isinstance(filtros, str)
    assert filtros == "Abril/2025 - DIRETORIA REGIONAL TESTE -  - EMEI"
