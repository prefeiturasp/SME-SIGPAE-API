from io import BytesIO

import openpyxl
import pandas as pd
import pytest
from openpyxl import load_workbook

from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_excel import (
    _ajusta_layout_tabela,
    _calcula_soma_medicao,
    _define_filtro,
    _formata_filtros,
    _formata_total_geral,
    _generate_columns,
    _get_alimentacoes_por_periodo,
    _get_categorias_dietas,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _get_nome_periodo,
    _get_total_pagamento,
    _get_valores_iniciais,
    _get_valores_tabela,
    _insere_tabela_periodos_na_planilha,
    _preenche_linha_dos_filtros_selecionados,
    _preenche_titulo,
    _processa_dieta_especial,
    _processa_periodo_campo,
    _processa_periodo_regular,
    _sort_and_merge,
    _total_pagamento_emef,
    _total_pagamento_emei,
    _update_dietas_alimentacoes,
    _update_periodos_alimentacoes,
    gera_relatorio_consolidado_xlsx,
    get_solicitacoes_ordenadas,
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


def test_get_alimentacoes_por_periodo(relatorio_consolidado_xlsx_emef):
    colunas = _get_alimentacoes_por_periodo([relatorio_consolidado_xlsx_emef])
    assert isinstance(colunas, list)
    assert len(colunas) == 16
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 4
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 4
    assert sum(1 for tupla in colunas if tupla[0] == "Solicitações de Alimentação") == 2

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 1


def test_get_valores_tabela_unidade_emef(relatorio_consolidado_xlsx_emef, mock_colunas):
    tipos_unidade = ["EMEF"]
    linhas = _get_valores_tabela(
        [relatorio_consolidado_xlsx_emef], mock_colunas, tipos_unidade
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 19
    assert linhas[0] == [
        "EMEF",
        "123456",
        "EMEF TESTE",
        10.0,
        10.0,
        125.0,
        125.0,
        125.0,
        125,
        125.0,
        125,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
        125.0,
    ]


def test_get_valores_tabela_unidade_emei(relatorio_consolidado_xlsx_emei, mock_colunas):
    tipos_unidade = ["EMEI"]
    linhas = _get_valores_tabela(
        [relatorio_consolidado_xlsx_emei], mock_colunas, tipos_unidade
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 19
    assert linhas[0] == [
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


def test_insere_tabela_periodos_na_planilha_unidade_emef(
    informacoes_excel_writer_emef, mock_colunas, mock_linhas_emef
):
    aba, writer, _, _, _, _ = informacoes_excel_writer_emef

    df = _insere_tabela_periodos_na_planilha(
        aba, mock_colunas, mock_linhas_emef, writer
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
        aba, mock_colunas, mock_linhas_emei, writer
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
    assert str(merged_ranges[0]) == "A3:E3"
    assert str(merged_ranges[1]) == "F3:K3"
    assert str(merged_ranges[2]) == "L3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "A1:S1"

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
    assert str(merged_ranges[0]) == "A3:E3"
    assert str(merged_ranges[1]) == "F3:K3"
    assert str(merged_ranges[2]) == "L3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "A2:S2"

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
    assert str(merged_ranges[0]) == "A3:E3"
    assert str(merged_ranges[1]) == "F3:K3"
    assert str(merged_ranges[2]) == "L3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "A2:S2"

    assert sheet["A2"].value == "ABRIL/2025 - DIRETORIA REGIONAL TESTE -  - EMEI"
    assert sheet["A2"].alignment.horizontal == "center"
    assert sheet["A2"].alignment.vertical == "center"
    assert sheet["A2"].font.bold is True
    assert sheet["A2"].font.color.rgb == "FF0C6B45"
    assert sheet["A2"].fill.fgColor.rgb == "FFEAFFF6"

    rows = list(sheet.iter_rows(values_only=True))
    assert tipos_unidades[0] in rows[1][0]
    workbook_openpyxl.close()


def test_ajusta_layout_tabela(informacoes_excel_writer_emef):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emef
    _ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 4
    assert str(merged_ranges[0]) == "A3:E3"
    assert str(merged_ranges[1]) == "F3:K3"
    assert str(merged_ranges[2]) == "L3:O3"
    assert str(merged_ranges[3]) == "P3:S3"

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
    assert str(merged_ranges[0]) == "A3:E3"
    assert str(merged_ranges[1]) == "F3:K3"
    assert str(merged_ranges[2]) == "L3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "A7:C7"

    assert sheet["A7"].value == "TOTAL"
    assert sheet["A7"].alignment.horizontal == "center"
    assert sheet["A7"].alignment.vertical == "center"
    assert sheet["A7"].font.bold is True
    workbook_openpyxl.close()


def test_get_nome_periodo(
    medicao_grupo_solicitacao_alimentacao, medicao_grupo_alimentacao
):
    periodo = _get_nome_periodo(medicao_grupo_solicitacao_alimentacao[0])
    assert isinstance(periodo, str)
    assert periodo == "Solicitações de Alimentação"

    periodo_manha = _get_nome_periodo(medicao_grupo_alimentacao[0])
    assert isinstance(periodo_manha, str)
    assert periodo_manha == "MANHA"


def test_get_lista_alimentacoes(relatorio_consolidado_xlsx_emef):
    medicoes = relatorio_consolidado_xlsx_emef.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    medicao_solicitacao = medicoes[1]

    lista_alimentacoes_manha = _get_lista_alimentacoes(medicao_manha, "MANHA")
    assert isinstance(lista_alimentacoes_manha, list)
    assert lista_alimentacoes_manha == [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    lista_alimentacoes_solicitacao = _get_lista_alimentacoes(
        medicao_solicitacao, "Solicitações de Alimentação"
    )
    assert isinstance(lista_alimentacoes_solicitacao, list)
    assert lista_alimentacoes_solicitacao == ["kit_lanche", "lanche_emergencial"]


def test_update_periodos_alimentacoes():
    lista_alimentacoes_manha = [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]
    lista_alimentacoes_solicitacao = ["kit_lanche", "lanche_emergencial"]

    periodos_alimentacoes = _update_periodos_alimentacoes(
        {}, "MANHA", lista_alimentacoes_manha
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "MANHA" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["MANHA"] == lista_alimentacoes_manha

    periodos_alimentacoes = _update_periodos_alimentacoes(
        periodos_alimentacoes,
        "Solicitações de Alimentação",
        lista_alimentacoes_solicitacao,
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Solicitações de Alimentação" in periodos_alimentacoes.keys()
    assert (
        periodos_alimentacoes["Solicitações de Alimentação"]
        == lista_alimentacoes_solicitacao
    )
    assert "MANHA" in periodos_alimentacoes.keys()


def test_get_categorias_dietas(relatorio_consolidado_xlsx_emef):
    medicoes = relatorio_consolidado_xlsx_emef.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    medicao_solicitacao = medicoes[1]

    categoria_manha = _get_categorias_dietas(medicao_manha)
    assert isinstance(categoria_manha, list)
    assert len(categoria_manha) == 2
    assert categoria_manha == ["DIETA ESPECIAL - TIPO A", "DIETA ESPECIAL - TIPO B"]

    categoria_solicitacao = _get_categorias_dietas(medicao_solicitacao)
    assert isinstance(categoria_solicitacao, list)
    assert len(categoria_solicitacao) == 0


def test_get_lista_alimentacoes_dietas(relatorio_consolidado_xlsx_emef):
    medicoes = relatorio_consolidado_xlsx_emef.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    dieta_a = "DIETA ESPECIAL - TIPO A"
    dieta_b = "DIETA ESPECIAL - TIPO B"

    lista_dietas_a = _get_lista_alimentacoes_dietas(medicao_manha, dieta_a)
    assert isinstance(lista_dietas_a, list)
    assert len(lista_dietas_a) == 4
    assert lista_dietas_a == ["lanche", "lanche_4h", "refeicao", "sobremesa"]

    lista_dietas_b = _get_lista_alimentacoes_dietas(medicao_manha, dieta_b)
    assert isinstance(lista_dietas_b, list)
    assert len(lista_dietas_b) == 4
    assert lista_dietas_b == ["lanche", "lanche_4h", "refeicao", "sobremesa"]


def test_update_dietas_alimentacoes():
    categoria_a = "DIETA ESPECIAL - TIPO A"
    categoria_b = "DIETA ESPECIAL - TIPO B"
    lista_alimentacoes = ["lanche", "lanche_4h", "refeicao", "sobremesa"]

    dietas_alimentacoes = _update_dietas_alimentacoes(
        {}, categoria_a, lista_alimentacoes
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_a in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_a] == lista_alimentacoes

    dietas_alimentacoes = _update_dietas_alimentacoes(
        dietas_alimentacoes, categoria_b, lista_alimentacoes
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_b in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_b] == lista_alimentacoes


def test_sort_and_merge():
    periodos_alimentacoes = {
        "MANHA": [
            "lanche",
            "lanche_4h",
            "refeicao",
            "sobremesa",
            "total_refeicoes_pagamento",
            "total_sobremesas_pagamento",
        ],
        "Solicitações de Alimentação": ["kit_lanche", "lanche_emergencial"],
    }
    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO A": ["lanche", "lanche_4h", "refeicao", "sobremesa"],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h", "refeicao", "sobremesa"],
    }
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    assert isinstance(dict_periodos_dietas, dict)

    assert "DIETA ESPECIAL - TIPO A" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO A"]) == 4
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO A"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
    ]

    assert "DIETA ESPECIAL - TIPO B" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO B"]) == 4
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO B"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
    ]

    assert "MANHA" in dict_periodos_dietas
    assert len(dict_periodos_dietas["MANHA"]) == 6
    assert dict_periodos_dietas["MANHA"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
        "total_refeicoes_pagamento",
        "sobremesa",
        "total_sobremesas_pagamento",
    ]

    assert "Solicitações de Alimentação" in dict_periodos_dietas
    assert len(dict_periodos_dietas["Solicitações de Alimentação"]) == 2
    assert dict_periodos_dietas["Solicitações de Alimentação"] == [
        "kit_lanche",
        "lanche_emergencial",
    ]


def test_generate_columns():
    dict_periodos_dietas = {
        "Solicitações de Alimentação": ["kit_lanche", "lanche_emergencial"],
        "MANHA": [
            "lanche",
            "lanche_4h",
            "refeicao",
            "total_refeicoes_pagamento",
            "sobremesa",
            "total_sobremesas_pagamento",
        ],
        "DIETA ESPECIAL - TIPO A": ["lanche", "lanche_4h", "refeicao", "sobremesa"],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h", "refeicao", "sobremesa"],
    }
    colunas = _generate_columns(dict_periodos_dietas)
    assert isinstance(colunas, list)
    assert len(colunas) == 16
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 4
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 4
    assert sum(1 for tupla in colunas if tupla[0] == "Solicitações de Alimentação") == 2

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 1


def test_get_solicitacoes_ordenadas_unidade_emef(
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
    solicitacao_relatorio_consolidado_grupo_emef,
):
    tipos_de_unidade = ["EMEF"]
    solicitacoes = [
        solicitacao_medicao_inicial_varios_valores_ceu_gestao,
        solicitacao_relatorio_consolidado_grupo_emef,
    ]
    ordenados = get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade)
    assert isinstance(ordenados, list)
    assert (
        ordenados[0].escola.nome
        == solicitacao_relatorio_consolidado_grupo_emef.escola.nome
    )
    assert (
        ordenados[1].escola.nome
        == solicitacao_medicao_inicial_varios_valores_ceu_gestao.escola.nome
    )


def test_get_solicitacoes_ordenadas_unidade_emei(
    solicitacao_escola_ceuemei,
    relatorio_consolidado_xlsx_emei,
):
    tipos_de_unidade = ["EMEI"]
    solicitacoes = [
        solicitacao_escola_ceuemei,
        relatorio_consolidado_xlsx_emei,
    ]
    ordenados = get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade)
    assert isinstance(ordenados, list)
    assert ordenados[0].escola.nome == relatorio_consolidado_xlsx_emei.escola.nome
    assert ordenados[1].escola.nome == solicitacao_escola_ceuemei.escola.nome


def test_get_valores_iniciais(relatorio_consolidado_xlsx_emef):
    valores = _get_valores_iniciais(relatorio_consolidado_xlsx_emef)
    assert isinstance(valores, list)
    assert len(valores) == 3
    assert valores == [
        relatorio_consolidado_xlsx_emef.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_emef.escola.codigo_eol,
        relatorio_consolidado_xlsx_emef.escola.nome,
    ]


def test_processa_periodo_campo_unidade_emef(relatorio_consolidado_xlsx_emef):
    valores_iniciais = [
        relatorio_consolidado_xlsx_emef.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_emef.escola.codigo_eol,
        relatorio_consolidado_xlsx_emef.escola.nome,
    ]
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    manha_refeicao = _processa_periodo_campo(
        relatorio_consolidado_xlsx_emef,
        "MANHA",
        "refeicao",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(manha_refeicao, list)
    assert len(manha_refeicao) == 4
    assert manha_refeicao == ["EMEF", "123456", "EMEF TESTE", 125.0]

    solicitacao_kit_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_emef,
        "Solicitações de Alimentação",
        "kit_lanche",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(solicitacao_kit_lanche, list)
    assert len(solicitacao_kit_lanche) == 5
    assert solicitacao_kit_lanche == ["EMEF", "123456", "EMEF TESTE", 125.0, 10]

    dieta_a_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_emef,
        "DIETA ESPECIAL - TIPO A",
        "lanche_4h",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(dieta_a_lanche, list)
    assert len(dieta_a_lanche) == 6
    assert dieta_a_lanche == ["EMEF", "123456", "EMEF TESTE", 125.0, 10.0, 125.0]


def test_processa_periodo_campo_unidade_emei(relatorio_consolidado_xlsx_emei):
    valores_iniciais = [
        relatorio_consolidado_xlsx_emei.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_emei.escola.codigo_eol,
        relatorio_consolidado_xlsx_emei.escola.nome,
    ]
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    manha_refeicao = _processa_periodo_campo(
        relatorio_consolidado_xlsx_emei,
        "MANHA",
        "refeicao",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(manha_refeicao, list)
    assert len(manha_refeicao) == 4
    assert manha_refeicao == ["EMEI", "987654", "EMEI TESTE", 150.0]

    solicitacao_kit_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_emei,
        "Solicitações de Alimentação",
        "kit_lanche",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(solicitacao_kit_lanche, list)
    assert len(solicitacao_kit_lanche) == 5
    assert solicitacao_kit_lanche == ["EMEI", "987654", "EMEI TESTE", 150.0, 5.0]

    dieta_a_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_emei,
        "DIETA ESPECIAL - TIPO A",
        "lanche_4h",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(dieta_a_lanche, list)
    assert len(dieta_a_lanche) == 6
    assert dieta_a_lanche == ["EMEI", "987654", "EMEI TESTE", 150.0, 5.0, 150.0]


def test_define_filtro(relatorio_consolidado_xlsx_emef):
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    manha = _define_filtro("MANHA", dietas_especiais, periodos_escolares)
    assert isinstance(manha, dict)
    assert "grupo__nome" not in manha
    assert "periodo_escolar__nome" in manha
    assert manha["periodo_escolar__nome"] == "MANHA"

    dieta_especial = _define_filtro(
        "DIETA ESPECIAL - TIPO A", dietas_especiais, periodos_escolares
    )
    assert isinstance(dieta_especial, dict)
    assert "grupo__nome" not in dieta_especial
    assert "periodo_escolar__nome__in" in dieta_especial
    assert dieta_especial["periodo_escolar__nome__in"] == periodos_escolares

    solicitacao = _define_filtro(
        "Solicitações de Alimentação", dietas_especiais, periodos_escolares
    )
    assert isinstance(solicitacao, dict)
    assert "periodo_escolar__nome" not in solicitacao
    assert "grupo__nome" in solicitacao
    assert solicitacao["grupo__nome"] == "Solicitações de Alimentação"


def test_get_total_pagamento_unidade_emef(relatorio_consolidado_xlsx_emef):
    medicoes = relatorio_consolidado_xlsx_emef.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    tipos_unidades = "EMEF"
    total_refeicao = _get_total_pagamento(
        medicao_manha, "total_refeicoes_pagamento", tipos_unidades
    )
    assert total_refeicao == 125
    total_sobremesa = _get_total_pagamento(
        medicao_manha, "total_sobremesas_pagamento", tipos_unidades
    )
    assert total_sobremesa == 125


def test_get_total_pagamento_unidade_emei(relatorio_consolidado_xlsx_emei):
    medicoes = relatorio_consolidado_xlsx_emei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    tipos_unidades = "EMEI"
    total_refeicao = _get_total_pagamento(
        medicao_manha, "total_refeicoes_pagamento", tipos_unidades
    )
    assert total_refeicao == 150
    total_sobremesa = _get_total_pagamento(
        medicao_manha, "total_sobremesas_pagamento", tipos_unidades
    )
    assert total_sobremesa == 150


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


def test_processa_dieta_especial(relatorio_consolidado_xlsx_emef):
    periodo = "MANHA"
    filtros = {"periodo_escolar__nome": periodo}
    campo = "refeicao"
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_emef, filtros, campo, periodo
    )
    assert total == "-"

    periodo = "Solicitações de Alimentação"
    filtros = {"grupo__nome": periodo}
    campo = "kit_lanche"
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_emef, filtros, campo, periodo
    )
    assert total == "-"

    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    filtros = {"periodo_escolar__nome__in": periodos_escolares}
    periodo = "DIETA ESPECIAL - TIPO A"
    campo = "lanche_4h"
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_emef, filtros, campo, periodo
    )
    assert total == 125.0


def test_processa_periodo_regular(relatorio_consolidado_xlsx_emef):
    periodo = "MANHA"
    filtros = {"periodo_escolar__nome": periodo}
    campo = "refeicao"
    total = _processa_periodo_regular(
        relatorio_consolidado_xlsx_emef, filtros, campo, periodo
    )
    assert total == 125.0

    periodo = "Solicitações de Alimentação"
    filtros = {"grupo__nome": periodo}
    campo = "kit_lanche"
    total = _processa_periodo_regular(
        relatorio_consolidado_xlsx_emef, filtros, campo, periodo
    )
    assert total == 10


def test_calcula_soma_medicao(relatorio_consolidado_xlsx_emef):
    medicoes = relatorio_consolidado_xlsx_emef.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    medicao_solicitacao = medicoes[1]

    campo = "refeicao"
    categoria = "ALIMENTAÇÃO"
    total = _calcula_soma_medicao(medicao_manha, campo, categoria)
    assert total == 125.0

    campo = "kit_lanche"
    categoria = "SOLICITAÇÕES DE ALIMENTAÇÃO"
    total = _calcula_soma_medicao(medicao_solicitacao, campo, categoria)
    assert total == 10.0

    campo = "lanche_4h"
    categoria = "DIETA ESPECIAL - TIPO A"
    total = _calcula_soma_medicao(medicao_manha, campo, categoria)
    assert total == 125.0


def test_total_pagamento_emef(relatorio_consolidado_xlsx_emef):
    medicoes = relatorio_consolidado_xlsx_emef.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    total_refeicao = _total_pagamento_emef(medicao_manha, "total_refeicoes_pagamento")
    assert total_refeicao == 125
    total_sobremesa = _total_pagamento_emef(medicao_manha, "total_sobremesas_pagamento")
    assert total_sobremesa == 125


def test_total_pagamento_emei(relatorio_consolidado_xlsx_emei):
    medicoes = relatorio_consolidado_xlsx_emei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    total_refeicao = _total_pagamento_emei(medicao_manha, "total_refeicoes_pagamento")
    assert total_refeicao == 150
    total_sobremesa = _total_pagamento_emei(medicao_manha, "total_sobremesas_pagamento")
    assert total_sobremesa == 150
