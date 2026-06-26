from io import BytesIO

import openpyxl
import pandas as pd
import pytest

from src.medicao_inicial.models import CategoriaMedicao
from src.medicao_inicial.services.relatorio_consolidado_recreio_emei_emef import (
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _processa_periodo_campo,
    _sort_and_merge,
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


def test_get_lista_alimentacoes(solicitacao_recreio_emei):
    medicoes = solicitacao_recreio_emei.medicoes.all().order_by("grupo__nome")
    medicao_colaboradores = medicoes[0]
    medicao_recreio_nas_ferias = medicoes[1]

    lista_alimentacoes_colaboradores = _get_lista_alimentacoes(
        medicao_colaboradores, "Colaboradores", {}
    )
    assert isinstance(lista_alimentacoes_colaboradores, list)
    assert lista_alimentacoes_colaboradores == [
        "refeicao",
        "repeticao_refeicao",
        "repeticao_sobremesa",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    lista_alimentacoes_recreio = _get_lista_alimentacoes(
        medicao_recreio_nas_ferias, "Recreio nas Férias", {}
    )
    assert isinstance(lista_alimentacoes_recreio, list)
    assert lista_alimentacoes_recreio == [
        "refeicao",
        "repeticao_refeicao",
        "repeticao_sobremesa",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    lista_alimentacoes_solicitacao = _get_lista_alimentacoes(
        medicao_recreio_nas_ferias, "Solicitações de Alimentação", {}
    )
    assert isinstance(lista_alimentacoes_solicitacao, list)
    assert lista_alimentacoes_solicitacao == [
        "refeicao",
        "repeticao_refeicao",
        "repeticao_sobremesa",
        "sobremesa",
    ]


def test_get_lista_alimentacoes_dietas(solicitacao_recreio_emei):
    medicoes = solicitacao_recreio_emei.medicoes.all().order_by("grupo__nome")
    medicao_recreio_nas_ferias = medicoes[1]
    dieta_a = "DIETA ESPECIAL - TIPO A"
    dieta_a_enteral_restricao = (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    )
    dieta_b = "DIETA ESPECIAL - TIPO B"

    lista_dietas_a = _get_lista_alimentacoes_dietas(
        medicao_recreio_nas_ferias, dieta_a, {}
    )
    assert isinstance(lista_dietas_a, list)
    assert len(lista_dietas_a) == 0

    lista_dietas_a_er = _get_lista_alimentacoes_dietas(
        medicao_recreio_nas_ferias, dieta_a_enteral_restricao, {}
    )
    assert isinstance(lista_dietas_a_er, list)
    assert len(lista_dietas_a_er) == 1
    assert lista_dietas_a_er == ["refeicao"]

    lista_dietas_b = _get_lista_alimentacoes_dietas(
        medicao_recreio_nas_ferias, dieta_b, {}
    )
    assert isinstance(lista_dietas_b, list)
    assert len(lista_dietas_b) == 0

    medicao_colaboradores = medicoes[0]
    lista_dietas_a = _get_lista_alimentacoes_dietas(medicao_colaboradores, dieta_a, {})
    assert isinstance(lista_dietas_a, list)
    assert len(lista_dietas_a) == 0

    lista_dietas_a_er = _get_lista_alimentacoes_dietas(
        medicao_colaboradores, dieta_a_enteral_restricao, {}
    )
    assert isinstance(lista_dietas_a_er, list)
    assert len(lista_dietas_a_er) == 0

    lista_dietas_b = _get_lista_alimentacoes_dietas(medicao_colaboradores, dieta_b, {})
    assert isinstance(lista_dietas_b, list)
    assert len(lista_dietas_b) == 0


def test_sort_and_merge():
    periodos_alimentacoes = {
        "Recreio nas Férias": [
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
        "DIETA ESPECIAL - TIPO A": ["lanche", "lanche_4h", "refeicao"],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
    }
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    assert isinstance(dict_periodos_dietas, dict)

    assert "DIETA ESPECIAL - TIPO A" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO A"]) == 3
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO A"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
    ]

    assert "DIETA ESPECIAL - TIPO B" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO B"]) == 2
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO B"] == ["lanche", "lanche_4h"]

    assert "Recreio nas Férias" in dict_periodos_dietas
    assert len(dict_periodos_dietas["Recreio nas Férias"]) == 6
    assert dict_periodos_dietas["Recreio nas Férias"] == [
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


def test_processa_periodo_campo_unidade_emei(solicitacao_recreio_emei):
    valores_iniciais = [
        solicitacao_recreio_emei.escola.tipo_unidade.iniciais,
        solicitacao_recreio_emei.escola.codigo_eol,
        solicitacao_recreio_emei.escola.nome,
    ]
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    recreio_refeicao = _processa_periodo_campo(
        solicitacao_recreio_emei,
        "Recreio nas Férias",
        "refeicao",
        valores_iniciais,
        dietas_especiais,
        {},
    )
    assert isinstance(recreio_refeicao, list)
    assert len(recreio_refeicao) == 4
    assert recreio_refeicao == ["EMEI", "987654", "EMEI TESTE", 1260.0]

    solicitacao_kit_lanche = _processa_periodo_campo(
        solicitacao_recreio_emei,
        "Solicitações de Alimentação",
        "kit_lanche",
        valores_iniciais,
        dietas_especiais,
        {},
    )
    assert isinstance(solicitacao_kit_lanche, list)
    assert len(solicitacao_kit_lanche) == 5
    assert solicitacao_kit_lanche == ["EMEI", "987654", "EMEI TESTE", 1260.0, "-"]

    dieta_a_lanche = _processa_periodo_campo(
        solicitacao_recreio_emei,
        "DIETA ESPECIAL - TIPO A",
        "lanche_4h",
        valores_iniciais,
        dietas_especiais,
        {},
    )
    assert isinstance(dieta_a_lanche, list)
    assert len(dieta_a_lanche) == 6
    assert dieta_a_lanche == ["EMEI", "987654", "EMEI TESTE", 1260.0, "-", "-"]
