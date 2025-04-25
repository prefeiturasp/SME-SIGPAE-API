from io import BytesIO

import openpyxl
import pandas as pd
import pytest
from openpyxl import load_workbook

from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_excel import (
    _ajusta_layout_tabela,
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
    _processa_periodo_campo,
    _sort_and_merge,
    _update_dietas_alimentacoes,
    _update_periodos_alimentacoes,
    gera_relatorio_consolidado_xlsx,
    get_solicitacoes_ordenadas,
)

pytestmark = pytest.mark.django_db


def test_gera_relatorio_consolidado_xlsx(
    mock_relatorio_consolidado_xlsx, mock_query_params_excel
):
    solicitacoes = [mock_relatorio_consolidado_xlsx.uuid]
    tipos_unidade = ["EMEF"]
    arquivo = gera_relatorio_consolidado_xlsx(
        solicitacoes, tipos_unidade, mock_query_params_excel
    )
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
        "Lanche 5h",
        "Lanche 4h",
        "Refeição",
        "Refeições p/ Pagamento",
        "Sobremesa",
        "Sobremesas p/ Pagamento",
        "Lanche 5h",
        "Lanche 4h",
        "Refeição",
        "Sobremesa",
        "Lanche 5h",
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


def test_get_alimentacoes_por_periodo(mock_relatorio_consolidado_xlsx):
    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
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


def test_get_valores_tabela(mock_relatorio_consolidado_xlsx, mock_colunas):
    tipos_unidade = ["EMEF"]
    linhas = _get_valores_tabela(
        [mock_relatorio_consolidado_xlsx], mock_colunas, tipos_unidade
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
        50.0,
        150.0,
        50.0,
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
        50.0,
        150.0,
        50.0,
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


def test_preenche_linha_dos_filtros_selecionados(
    mock_relatorio_consolidado_xlsx, grupo_escolar
):
    query_params = {
        "dre": mock_relatorio_consolidado_xlsx.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": mock_relatorio_consolidado_xlsx.mes,
        "ano": mock_relatorio_consolidado_xlsx.ano,
        "lotes[]": mock_relatorio_consolidado_xlsx.escola.lote.uuid,
        "lotes": [mock_relatorio_consolidado_xlsx.escola.lote.uuid],
    }
    tipos_unidades = ["EMEF"]
    file = BytesIO()
    aba = f"Relatório Consolidado {mock_relatorio_consolidado_xlsx.mes}-{ mock_relatorio_consolidado_xlsx.ano}"
    writer = pd.ExcelWriter(file, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)

    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
    linhas = _get_valores_tabela([mock_relatorio_consolidado_xlsx], colunas)
    df = _insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer)
    _preenche_linha_dos_filtros_selecionados(
        workbook, worksheet, query_params, df.columns, tipos_unidades
    )
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(file)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 6
    assert str(merged_ranges[0]) == "A3:C3"
    assert str(merged_ranges[1]) == "D3:I3"
    assert str(merged_ranges[2]) == "J3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "T3:W3"
    assert str(merged_ranges[5]) == "A2:W2"

    assert sheet["A2"].alignment.horizontal == "center"
    assert sheet["A2"].alignment.vertical == "center"
    assert sheet["A2"].font.bold is True
    assert sheet["A2"].font.color.rgb == "FF0C6B45"
    assert sheet["A2"].fill.fgColor.rgb == "FFEAFFF6"

    rows = list(sheet.iter_rows(values_only=True))
    assert tipos_unidades[0] in rows[1][0]


def test_ajusta_layout_tabela(mock_relatorio_consolidado_xlsx):
    file = BytesIO()
    aba = f"Relatório Consolidado {mock_relatorio_consolidado_xlsx.mes}-{ mock_relatorio_consolidado_xlsx.ano}"
    writer = pd.ExcelWriter(file, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)

    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
    linhas = _get_valores_tabela([mock_relatorio_consolidado_xlsx], colunas)
    df = _insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer)
    _ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(file)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 5
    assert str(merged_ranges[0]) == "A3:C3"
    assert str(merged_ranges[1]) == "D3:I3"
    assert str(merged_ranges[2]) == "J3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "T3:W3"

    assert sheet["D3"].value == "MANHA"
    assert sheet["D3"].fill.fgColor.rgb == "FF198459"
    assert sheet["J3"].value == "TARDE"
    assert sheet["J3"].fill.fgColor.rgb == "FFD06D12"
    assert sheet["P3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["P3"].fill.fgColor.rgb == "FF198459"
    assert sheet["T3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["T3"].fill.fgColor.rgb == "FF20AA73"


def test_formata_total_geral(mock_relatorio_consolidado_xlsx):
    file = BytesIO()
    aba = f"Relatório Consolidado {mock_relatorio_consolidado_xlsx.mes}-{ mock_relatorio_consolidado_xlsx.ano}"
    writer = pd.ExcelWriter(file, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet(aba)
    worksheet.set_default_row(20)

    colunas = _get_alimentacoes_por_periodo([mock_relatorio_consolidado_xlsx])
    linhas = _get_valores_tabela([mock_relatorio_consolidado_xlsx], colunas)
    df = _insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer)
    _formata_total_geral(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(file)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 6
    assert str(merged_ranges[0]) == "A3:C3"
    assert str(merged_ranges[1]) == "D3:I3"
    assert str(merged_ranges[2]) == "J3:O3"
    assert str(merged_ranges[3]) == "P3:S3"
    assert str(merged_ranges[4]) == "T3:W3"
    assert str(merged_ranges[5]) == "A7:C7"

    assert sheet["A7"].value == "TOTAL"
    assert sheet["A7"].alignment.horizontal == "center"
    assert sheet["A7"].alignment.vertical == "center"
    assert sheet["A7"].font.bold is True


def test_get_nome_periodo(
    mock_relatorio_consolidado_xlsx, medico_com_grupo, medico_sem_periodo_escolar
):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    periodo_manha = _get_nome_periodo(medicoes[0])
    assert isinstance(periodo_manha, str)
    assert periodo_manha == "MANHA"

    periodo_tarde = _get_nome_periodo(medicoes[1])
    assert isinstance(periodo_tarde, str)
    assert periodo_tarde == "TARDE"

    periodo_com_grupo = _get_nome_periodo(medico_com_grupo)
    assert isinstance(periodo_com_grupo, str)
    assert periodo_com_grupo == "ALIMENTAÇÃO - TARDE"

    periodo_sem_periodo = _get_nome_periodo(medico_sem_periodo_escolar)
    assert isinstance(periodo_sem_periodo, str)
    assert periodo_sem_periodo == "ALIMENTAÇÃO"


def test_get_lista_alimentacoes(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    periodo_manha = _get_nome_periodo(medicoes[0])
    lista_alimentacoes_manha = _get_lista_alimentacoes(medicoes[0], periodo_manha)
    assert isinstance(lista_alimentacoes_manha, list)
    assert lista_alimentacoes_manha == [
        "lanche",
        "lanche_emergencial",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    periodo_tarde = _get_nome_periodo(medicoes[1])
    lista_alimentacoes_tarde = _get_lista_alimentacoes(medicoes[1], periodo_tarde)
    assert isinstance(lista_alimentacoes_tarde, list)
    assert lista_alimentacoes_tarde == [
        "lanche",
        "lanche_emergencial",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]


def test_update_periodos_alimentacoes(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    periodo_manha = _get_nome_periodo(medicoes[0])
    lista_alimentacoes_manha = _get_lista_alimentacoes(medicoes[0], periodo_manha)
    periodos_alimentacoes_manha = _update_periodos_alimentacoes(
        {}, periodo_manha, lista_alimentacoes_manha
    )
    assert isinstance(periodos_alimentacoes_manha, dict)
    assert periodo_manha in periodos_alimentacoes_manha.keys()

    periodo_tarde = _get_nome_periodo(medicoes[1])
    lista_alimentacoes_tarde = _get_lista_alimentacoes(medicoes[0], periodo_tarde)
    periodos_alimentacoes_tarde = _update_periodos_alimentacoes(
        periodos_alimentacoes_manha, periodo_tarde, lista_alimentacoes_tarde
    )
    assert isinstance(periodos_alimentacoes_tarde, dict)
    assert periodo_tarde in periodos_alimentacoes_tarde.keys()
    assert periodo_manha in periodos_alimentacoes_tarde.keys()


def test_get_categorias_dietas(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    categoria_manha = _get_categorias_dietas(medicoes[0])
    assert isinstance(categoria_manha, list)
    assert len(categoria_manha) == 2
    assert categoria_manha == ["DIETA ESPECIAL - TIPO A", "DIETA ESPECIAL - TIPO B"]

    categoria_tarde = _get_categorias_dietas(medicoes[1])
    assert isinstance(categoria_tarde, list)
    assert len(categoria_tarde) == 2
    assert categoria_tarde == ["DIETA ESPECIAL - TIPO A", "DIETA ESPECIAL - TIPO B"]


def test_get_lista_alimentacoes_dietas(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    categoria_manha = _get_categorias_dietas(medicoes[0])
    lista_dietas_manha = _get_lista_alimentacoes_dietas(medicoes[0], categoria_manha[0])
    assert isinstance(lista_dietas_manha, list)
    assert len(lista_dietas_manha) == 4
    assert lista_dietas_manha == [
        "lanche",
        "lanche_emergencial",
        "refeicao",
        "sobremesa",
    ]

    categoria_tarde = _get_categorias_dietas(medicoes[1])
    lista_dietas_tarde = _get_lista_alimentacoes_dietas(medicoes[0], categoria_tarde[1])
    assert isinstance(lista_dietas_tarde, list)
    assert len(lista_dietas_tarde) == 4
    assert lista_dietas_tarde == [
        "lanche",
        "lanche_emergencial",
        "refeicao",
        "sobremesa",
    ]


def test_update_dietas_alimentacoes(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    categoria_manha = _get_categorias_dietas(medicoes[0])
    lista_dietas_manha = _get_lista_alimentacoes_dietas(medicoes[0], categoria_manha[0])
    dietas_alimentacoes = _update_dietas_alimentacoes(
        {}, categoria_manha[0], lista_dietas_manha
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_manha[0] in dietas_alimentacoes.keys()

    categoria_tarde = _get_categorias_dietas(medicoes[1])
    lista_dietas_tarde = _get_lista_alimentacoes_dietas(medicoes[0], categoria_tarde[1])
    dietas_alimentacoes = _update_dietas_alimentacoes(
        dietas_alimentacoes, categoria_tarde[1], lista_dietas_tarde
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_manha[0] in dietas_alimentacoes.keys()


def test_sort_and_merge(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()

    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    periodo_manha = _get_nome_periodo(medicoes[0])
    lista_alimentacoes_manha = _get_lista_alimentacoes(medicoes[0], periodo_manha)
    periodos_alimentacoes_manha = _update_periodos_alimentacoes(
        {}, periodo_manha, lista_alimentacoes_manha
    )

    categoria_manha = _get_categorias_dietas(medicoes[0])
    lista_dietas_manha = _get_lista_alimentacoes_dietas(medicoes[0], categoria_manha[0])
    dietas_alimentacoes = _update_dietas_alimentacoes(
        {}, categoria_manha[0], lista_dietas_manha
    )

    dict_periodos_dietas = _sort_and_merge(
        periodos_alimentacoes_manha, dietas_alimentacoes
    )
    assert isinstance(dict_periodos_dietas, dict)

    assert "DIETA ESPECIAL - TIPO A" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO A"]) == 4
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO A"] == [
        "lanche",
        "refeicao",
        "sobremesa",
        "lanche_emergencial",
    ]

    assert "MANHA" in dict_periodos_dietas
    assert len(dict_periodos_dietas["MANHA"]) == 6
    assert dict_periodos_dietas["MANHA"] == [
        "lanche",
        "refeicao",
        "total_refeicoes_pagamento",
        "sobremesa",
        "total_sobremesas_pagamento",
        "lanche_emergencial",
    ]


def test_generate_columns(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    periodo_manha = _get_nome_periodo(medicoes[0])
    lista_alimentacoes_manha = _get_lista_alimentacoes(medicoes[0], periodo_manha)
    periodos_alimentacoes_manha = _update_periodos_alimentacoes(
        {}, periodo_manha, lista_alimentacoes_manha
    )

    categoria_manha = _get_categorias_dietas(medicoes[0])
    lista_dietas_manha = _get_lista_alimentacoes_dietas(medicoes[0], categoria_manha[0])
    dietas_alimentacoes = _update_dietas_alimentacoes(
        {}, categoria_manha[0], lista_dietas_manha
    )

    dict_periodos_dietas = _sort_and_merge(
        periodos_alimentacoes_manha, dietas_alimentacoes
    )
    colunas = _generate_columns(dict_periodos_dietas)
    assert isinstance(colunas, list)
    assert len(colunas) == 10
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 4


def test_get_solicitacoes_ordenadas(
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
    mock_relatorio_consolidado_xlsx,
):
    ordenados = get_solicitacoes_ordenadas(
        [
            solicitacao_medicao_inicial_varios_valores_ceu_gestao,
            mock_relatorio_consolidado_xlsx,
        ]
    )
    assert isinstance(ordenados, list)
    assert ordenados[0].escola.nome == mock_relatorio_consolidado_xlsx.escola.nome
    assert (
        ordenados[1].escola.nome
        == solicitacao_medicao_inicial_varios_valores_ceu_gestao.escola.nome
    )


def test_get_valores_iniciais(mock_relatorio_consolidado_xlsx):
    valores = _get_valores_iniciais(mock_relatorio_consolidado_xlsx)
    assert isinstance(valores, list)
    assert len(valores) == 3
    assert valores == [
        mock_relatorio_consolidado_xlsx.escola.tipo_unidade.iniciais,
        mock_relatorio_consolidado_xlsx.escola.codigo_eol,
        mock_relatorio_consolidado_xlsx.escola.nome,
    ]


def test_processa_periodo_campo(mock_relatorio_consolidado_xlsx):
    valores_iniciais = [
        mock_relatorio_consolidado_xlsx.escola.tipo_unidade.iniciais,
        mock_relatorio_consolidado_xlsx.escola.codigo_eol,
        mock_relatorio_consolidado_xlsx.escola.nome,
    ]
    manha_refeicao = _processa_periodo_campo(
        mock_relatorio_consolidado_xlsx, "MANHA", "refeicao", valores_iniciais
    )
    assert isinstance(manha_refeicao, list)
    assert len(manha_refeicao) == 4
    assert manha_refeicao == ["EMEF", "123456", "EMEF TESTE", 150]

    tarde_sobremesa = _processa_periodo_campo(
        mock_relatorio_consolidado_xlsx,
        "TARDE",
        "total_sobremesas_pagamento",
        valores_iniciais,
    )
    assert isinstance(tarde_sobremesa, list)
    assert len(tarde_sobremesa) == 5
    assert tarde_sobremesa == ["EMEF", "123456", "EMEF TESTE", 150, 0]

    integral_sobremesa = _processa_periodo_campo(
        mock_relatorio_consolidado_xlsx, "INTEGRAL", "lanche", valores_iniciais
    )
    assert isinstance(integral_sobremesa, list)
    assert len(integral_sobremesa) == 6
    assert integral_sobremesa == ["EMEF", "123456", "EMEF TESTE", 150, 0, "-"]


def test_define_filtro():
    manha = _define_filtro("MANHA")
    assert isinstance(manha, dict)
    assert "grupo__nome" not in manha
    assert "periodo_escolar__nome" in manha
    assert manha["periodo_escolar__nome"] == "MANHA"

    etec = _define_filtro("ETEC")
    assert isinstance(etec, dict)
    assert "periodo_escolar__nome" not in etec
    assert "grupo__nome" in etec
    assert etec["grupo__nome"] == "ETEC"


def test_get_total_pagamento(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all()
    total_lanche = _get_total_pagamento(medicoes[0], "lanche")
    assert total_lanche == 50
    total_refeicao = _get_total_pagamento(medicoes[0], "refeicao")
    assert total_refeicao == 50
    total_lanche_emergencial = _get_total_pagamento(medicoes[0], "lanche_emergencial")
    assert total_lanche_emergencial == 50
    total_sobremesa = _get_total_pagamento(medicoes[0], "sobremesa")
    assert total_sobremesa == 50


def test_formata_filtros(mock_relatorio_consolidado_xlsx, grupo_escolar):
    query_params = {
        "dre": mock_relatorio_consolidado_xlsx.escola.diretoria_regional.uuid,
        "status": "MEDICAO_APROVADA_PELA_CODAE",
        "grupo_escolar": grupo_escolar,
        "mes": mock_relatorio_consolidado_xlsx.mes,
        "ano": mock_relatorio_consolidado_xlsx.ano,
        "lotes[]": mock_relatorio_consolidado_xlsx.escola.lote.uuid,
        "lotes": [mock_relatorio_consolidado_xlsx.escola.lote.uuid],
    }
    tipos_unidades = ["EMEF"]
    filtros = _formata_filtros(query_params, tipos_unidades)
    assert isinstance(filtros, str)
    assert filtros == "Abril/2025 - DIRETORIA REGIONAL IPIRANGA - 1 - EMEF"
