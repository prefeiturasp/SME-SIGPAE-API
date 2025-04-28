from io import BytesIO

import openpyxl
import pandas as pd
import pytest
from openpyxl import load_workbook

from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
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


def test_insere_tabela_periodos_na_planilha(
    informacoes_excel_writer, mock_colunas, mock_linhas
):
    aba, writer, _, _, _, _ = informacoes_excel_writer

    df = _insere_tabela_periodos_na_planilha(aba, mock_colunas, mock_linhas, writer)
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
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 5h") == 3
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


def test_preenche_titulo(informacoes_excel_writer):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer
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


def test_preenche_linha_dos_filtros_selecionados(
    mock_query_params_excel, informacoes_excel_writer
):
    tipos_unidades = ["EMEF"]
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer
    _preenche_linha_dos_filtros_selecionados(
        workbook, worksheet, mock_query_params_excel, df.columns, tipos_unidades
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


def test_ajusta_layout_tabela(informacoes_excel_writer):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer
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


def test_formata_total_geral(informacoes_excel_writer):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer
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
    periodo = _get_nome_periodo(medicao_grupo_solicitacao_alimentacao)
    assert isinstance(periodo, str)
    assert periodo == "Solicitações de Alimentação"

    periodo_manha = _get_nome_periodo(medicao_grupo_alimentacao)
    assert isinstance(periodo_manha, str)
    assert periodo_manha == "MANHA"


def test_get_lista_alimentacoes(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all().order_by(
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


def test_get_categorias_dietas(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all().order_by(
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


def test_get_lista_alimentacoes_dietas(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all().order_by(
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


def test_get_solicitacoes_ordenadas(
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
    mock_relatorio_consolidado_xlsx,
):
    tipos_de_unidade = ["EMEF"]
    solicitacoes = [
        solicitacao_medicao_inicial_varios_valores_ceu_gestao,
        mock_relatorio_consolidado_xlsx,
    ]
    ordenados = get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade)
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
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    manha_refeicao = _processa_periodo_campo(
        mock_relatorio_consolidado_xlsx,
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
        mock_relatorio_consolidado_xlsx,
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
        mock_relatorio_consolidado_xlsx,
        "DIETA ESPECIAL - TIPO A",
        "lanche_4h",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(dieta_a_lanche, list)
    assert len(dieta_a_lanche) == 6
    assert dieta_a_lanche == ["EMEF", "123456", "EMEF TESTE", 125.0, 10.0, 125.0]


def test_define_filtro(mock_relatorio_consolidado_xlsx):
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


def test_get_total_pagamento(mock_relatorio_consolidado_xlsx):
    medicoes = mock_relatorio_consolidado_xlsx.medicoes.all().order_by(
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


def test_formata_filtros(mock_query_params_excel):
    tipos_unidades = ["EMEF"]
    filtros = _formata_filtros(mock_query_params_excel, tipos_unidades)
    assert isinstance(filtros, str)
    assert filtros == "Abril/2025 - DIRETORIA REGIONAL IPIRANGA - 1 - EMEF"
