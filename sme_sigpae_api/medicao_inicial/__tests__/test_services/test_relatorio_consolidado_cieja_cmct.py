import math
from io import BytesIO

import openpyxl
import pandas as pd
import pytest

from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_cieja_cmct import (
    _calcula_soma_medicao,
    _define_filtro,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _processa_periodo_campo,
    _sort_and_merge,
    _unificar_dietas_tipo_a,
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
    processa_dieta_especial,
    processa_periodo_regular,
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


def test_ajusta_layout_tabela(informacoes_excel_writer_cieja_cmct):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_cieja_cmct
    ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 6
    esperados = {"R3:T3", "L3:Q3", "U3:W3", "X3:Y3", "F3:K3", "A3:E3"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A3"].value is None
    assert sheet["F3"].value == "MANHA"
    assert sheet["F3"].fill.fgColor.rgb == "FF198459"
    assert sheet["L3"].value == "TARDE"
    assert sheet["L3"].fill.fgColor.rgb == "FFD06D12"
    assert sheet["R3"].value == "PROGRAMAS E PROJETOS"
    assert sheet["R3"].fill.fgColor.rgb == "FF72BC17"
    assert sheet["U3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["U3"].fill.fgColor.rgb == "FF198459"
    assert sheet["X3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["X3"].fill.fgColor.rgb == "FF20AA73"
    workbook_openpyxl.close()


def test_get_lista_alimentacoes(relatorio_consolidado_xlsx_cieja):
    medicoes = relatorio_consolidado_xlsx_cieja.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    medicao_manha = medicoes[0]
    medicao_programas_projetos = medicoes[2]
    medicao_solicitacao = medicoes[3]

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

    lista_alimentacoes_programa_projetos = _get_lista_alimentacoes(
        medicao_programas_projetos, "Programas e Projetos"
    )
    assert isinstance(lista_alimentacoes_programa_projetos, list)
    assert lista_alimentacoes_programa_projetos == [
        "lanche_4h",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]


def test_get_lista_alimentacoes_dietas(relatorio_consolidado_xlsx_cieja):
    medicoes = relatorio_consolidado_xlsx_cieja.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    dieta_a = "DIETA ESPECIAL - TIPO A"
    dieta_a_enteral_restricao = (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    )
    dieta_b = "DIETA ESPECIAL - TIPO B"

    lista_dietas_a = _get_lista_alimentacoes_dietas(medicao_manha, dieta_a)
    assert isinstance(lista_dietas_a, list)
    assert len(lista_dietas_a) == 2
    assert lista_dietas_a == ["lanche", "lanche_4h"]

    lista_dietas_a_er = _get_lista_alimentacoes_dietas(
        medicao_manha, dieta_a_enteral_restricao
    )
    assert isinstance(lista_dietas_a_er, list)
    assert len(lista_dietas_a_er) == 3
    assert lista_dietas_a_er == ["lanche", "lanche_4h", "refeicao"]

    lista_dietas_b = _get_lista_alimentacoes_dietas(medicao_manha, dieta_b)
    assert isinstance(lista_dietas_b, list)
    assert len(lista_dietas_b) == 2
    assert lista_dietas_b == ["lanche", "lanche_4h"]


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


def test_processa_periodo_campo_unidade(relatorio_consolidado_xlsx_cieja):
    valores_iniciais = [
        relatorio_consolidado_xlsx_cieja.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_cieja.escola.codigo_eol,
        relatorio_consolidado_xlsx_cieja.escola.nome,
    ]
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    manha_refeicao = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cieja,
        "MANHA",
        "refeicao",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(manha_refeicao, list)
    assert len(manha_refeicao) == 4
    assert manha_refeicao == ["CIEJA", "111329", "CIEJA TESTE", 150.0]

    solicitacao_kit_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cieja,
        "Solicitações de Alimentação",
        "kit_lanche",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(solicitacao_kit_lanche, list)
    assert len(solicitacao_kit_lanche) == 5
    assert solicitacao_kit_lanche == ["CIEJA", "111329", "CIEJA TESTE", 150.0, 5.0]

    dieta_a_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cieja,
        "DIETA ESPECIAL - TIPO A",
        "lanche_4h",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(dieta_a_lanche, list)
    assert len(dieta_a_lanche) == 6
    assert dieta_a_lanche == ["CIEJA", "111329", "CIEJA TESTE", 150.0, 5.0, 80.0]

    pp_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cieja,
        "Programas e Projetos",
        "lanche_4h",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(pp_lanche, list)
    assert len(pp_lanche) == 7
    assert pp_lanche == ["CIEJA", "111329", "CIEJA TESTE", 150.0, 5.0, 80.0, 20.0]


def test_define_filtro(relatorio_consolidado_xlsx_cieja):
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
    assert "grupo__nome__in" in dieta_especial
    assert dieta_especial["periodo_escolar__nome__in"] == periodos_escolares
    assert dieta_especial["grupo__nome__in"] == ["Programas e Projetos", "ETEC"]

    solicitacao = _define_filtro(
        "Solicitações de Alimentação", dietas_especiais, periodos_escolares
    )
    assert isinstance(solicitacao, dict)
    assert "periodo_escolar__nome" not in solicitacao
    assert "grupo__nome" in solicitacao
    assert solicitacao["grupo__nome"] == "Solicitações de Alimentação"


def test_processa_dieta_especial(relatorio_consolidado_xlsx_cieja):
    periodo = "MANHA"
    filtros = {"periodo_escolar__nome": periodo}
    campo = "refeicao"
    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_cieja, filtros, campo, periodo
    )
    assert total == "-"

    periodo = "Solicitações de Alimentação"
    filtros = {"grupo__nome": periodo}
    campo = "kit_lanche"
    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_cieja, filtros, campo, periodo
    )
    assert total == "-"

    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    filtros = {"periodo_escolar__nome__in": periodos_escolares}
    periodo = "DIETA ESPECIAL - TIPO A"
    campo = "lanche_4h"
    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_cieja, filtros, campo, periodo
    )
    assert math.isclose(total, 80.0, rel_tol=1e-9)


def test_processa_periodo_regular(relatorio_consolidado_xlsx_cieja):
    periodo = "MANHA"
    filtros = {"periodo_escolar__nome": periodo}
    campo = "refeicao"
    total = processa_periodo_regular(
        relatorio_consolidado_xlsx_cieja, filtros, campo, periodo
    )
    assert math.isclose(total, 150.0, rel_tol=1e-9)

    periodo = "Solicitações de Alimentação"
    filtros = {"grupo__nome": periodo}
    campo = "kit_lanche"
    total = processa_periodo_regular(
        relatorio_consolidado_xlsx_cieja, filtros, campo, periodo
    )
    assert total == 5


def test_calcula_soma_medicao(relatorio_consolidado_xlsx_cieja):
    medicoes = relatorio_consolidado_xlsx_cieja.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    medicao_manha = medicoes[0]
    medicao_solicitacao = medicoes[3]

    campo = "refeicao"
    categoria = ["ALIMENTAÇÃO"]
    total = _calcula_soma_medicao(medicao_manha, campo, categoria)
    assert math.isclose(total, 150.0, rel_tol=1e-9)

    campo = "kit_lanche"
    categoria = ["SOLICITAÇÕES DE ALIMENTAÇÃO"]
    total = _calcula_soma_medicao(medicao_solicitacao, campo, categoria)
    assert math.isclose(total, 5.0, rel_tol=1e-9)

    campo = "lanche_4h"
    categoria = [
        "DIETA ESPECIAL - TIPO A",
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
    ]
    total = _calcula_soma_medicao(medicao_manha, campo, categoria)
    assert math.isclose(total, 40.0, rel_tol=1e-9)


def test_unificar_dietas_tipo_a():
    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO A": ["lanche", "lanche_4h"],
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS": [
            "lanche",
            "lanche_4h",
            "refeicao",
        ],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
    }
    resultado = _unificar_dietas_tipo_a(dietas_alimentacoes)
    assert "DIETA ESPECIAL - TIPO A" in resultado
    assert "DIETA ESPECIAL - TIPO B" in resultado
    assert (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS" not in resultado
    )
    assert len(resultado["DIETA ESPECIAL - TIPO A"]) == 5


def test_unificar_dietas_tipo_a_sem_dieta_enteral():
    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO A": ["lanche", "lanche_4h"],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
    }
    resultado = _unificar_dietas_tipo_a(dietas_alimentacoes)
    assert "DIETA ESPECIAL - TIPO A" in resultado
    assert "DIETA ESPECIAL - TIPO B" in resultado
    assert (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS" not in resultado
    )
    assert len(resultado["DIETA ESPECIAL - TIPO A"]) == 2


def test_unificar_dietas_tipo_a_sem_dieta_principal():
    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS": [
            "lanche",
            "lanche_4h",
            "refeicao",
        ],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
    }
    resultado = _unificar_dietas_tipo_a(dietas_alimentacoes)
    assert "DIETA ESPECIAL - TIPO A" in resultado
    assert "DIETA ESPECIAL - TIPO B" in resultado
    assert (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS" not in resultado
    )
    assert len(resultado["DIETA ESPECIAL - TIPO A"]) == 3


def test_unificar_dietas_tipo_a_sem_dietas_do_tipo_a():
    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
    }
    resultado = _unificar_dietas_tipo_a(dietas_alimentacoes)
    assert "DIETA ESPECIAL - TIPO A" not in resultado
    assert "DIETA ESPECIAL - TIPO B" in resultado
    assert (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS" not in resultado
    )
    assert len(resultado["DIETA ESPECIAL - TIPO B"]) == 2
