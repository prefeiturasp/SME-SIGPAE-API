import openpyxl
import pandas as pd
import pytest

from sme_sigpae_api.medicao_inicial.models import GrupoMedicao
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_cemei import (
    _define_filtro,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _processa_dieta_especial,
    _processa_periodo_campo,
    _processa_periodo_regular,
    _sort_and_merge,
    _unificar_dietas,
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_solicitacoes_ordenadas,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(
    relatorio_consolidado_xlsx_cemei, faixas_etarias_ativas
):
    colunas = get_alimentacoes_por_periodo([relatorio_consolidado_xlsx_cemei])
    assert isinstance(colunas, list)
    assert len(colunas) == 73
    assert sum(1 for tupla in colunas if tupla[0] == "Solicitações de Alimentação") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "PARCIAL") == 8
    assert (
        sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A - INTEGRAL")
        == 8
    )
    assert (
        sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B - INTEGRAL")
        == 8
    )
    assert (
        sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A - PARCIAL")
        == 8
    )
    assert (
        sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B - PARCIAL")
        == 8
    )
    assert sum(1 for tupla in colunas if tupla[0] == "Infantil INTEGRAL") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "Infantil MANHA") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "Infantil TARDE") == 6
    assert (
        sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A - INFANTIL")
        == 3
    )
    assert (
        sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B - INFANTIL")
        == 2
    )

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 1
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[0].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[1].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[2].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[3].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[4].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[5].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[6].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[7].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 5
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 5
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 4
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 3


def test_get_lista_alimentacoes(
    relatorio_consolidado_xlsx_cemei, faixas_etarias_ativas
):
    retorno_cei = [faixa.id for faixa in faixas_etarias_ativas]
    retorno_emei = [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    medicoes = relatorio_consolidado_xlsx_cemei.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    assert medicoes.count() == 6

    integral_cei = _get_lista_alimentacoes(medicoes[0], "INTEGRAL")
    assert isinstance(integral_cei, list)
    assert integral_cei == retorno_cei

    parcial = _get_lista_alimentacoes(medicoes[1], "PARCIAL")
    assert isinstance(parcial, list)
    assert parcial == retorno_cei

    integral = _get_lista_alimentacoes(medicoes[2], "Infantil INTEGRAL")
    assert isinstance(integral, list)
    assert integral == retorno_emei

    manha = _get_lista_alimentacoes(medicoes[3], "Infantil MANHA")
    assert isinstance(manha, list)
    assert manha == retorno_emei

    tarde = _get_lista_alimentacoes(medicoes[4], "Infantil TARDE")
    assert isinstance(tarde, list)
    assert tarde == retorno_emei

    solicitacao = _get_lista_alimentacoes(medicoes[5], "Solicitações de Alimentação")
    assert isinstance(solicitacao, list)
    assert solicitacao == ["kit_lanche", "lanche_emergencial"]


def test_get_lista_alimentacoes_dietas(
    relatorio_consolidado_xlsx_cemei, faixas_etarias_ativas
):
    medicoes = relatorio_consolidado_xlsx_cemei.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    retorno_cei = [faixa.id for faixa in faixas_etarias_ativas]

    lista_dietas_integral_cei = _get_lista_alimentacoes_dietas(
        medicoes[0], "DIETA ESPECIAL - TIPO A"
    )
    assert isinstance(lista_dietas_integral_cei, list)
    assert lista_dietas_integral_cei == retorno_cei

    lista_dietas_integral_emei = _get_lista_alimentacoes_dietas(
        medicoes[3], "DIETA ESPECIAL - TIPO A"
    )
    assert isinstance(lista_dietas_integral_emei, list)
    assert lista_dietas_integral_emei == ["lanche", "lanche_4h"]


def test_unificar_dietas():
    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO A - INFANTIL": ["lanche", "lanche_4h"],
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS - INFANTIL": [
            "lanche",
            "lanche_4h",
            "refeicao",
        ],
        "DIETA ESPECIAL - TIPO B - INFANTIL": ["lanche", "lanche_4h"],
    }
    resultado = _unificar_dietas(dietas_alimentacoes)
    assert "DIETA ESPECIAL - TIPO A - INFANTIL" in resultado
    assert "DIETA ESPECIAL - TIPO B - INFANTIL" in resultado
    assert (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS - INFANTIL"
        not in resultado
    )
    assert len(resultado["DIETA ESPECIAL - TIPO A - INFANTIL"]) == 5


def test_sort_and_merge(faixas_etarias_ativas):
    faixas = [faixa.id for faixa in faixas_etarias_ativas]
    periodos_alimentacoes = {
        "INTEGRAL": faixas,
        "Infantil INTEGRAL": [
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
        "DIETA ESPECIAL - TIPO A - INFANTIL": ["lanche", "lanche_4h", "refeicao"],
        "DIETA ESPECIAL - TIPO B - INFANTIL": ["lanche", "lanche_4h"],
    }
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    assert isinstance(dict_periodos_dietas, dict)

    assert "INTEGRAL" in dict_periodos_dietas
    assert len(dict_periodos_dietas["INTEGRAL"]) == 8
    assert dict_periodos_dietas["INTEGRAL"] == faixas

    assert "Infantil INTEGRAL" in dict_periodos_dietas
    assert len(dict_periodos_dietas["Infantil INTEGRAL"]) == 6
    assert dict_periodos_dietas["Infantil INTEGRAL"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
        "total_refeicoes_pagamento",
        "sobremesa",
        "total_sobremesas_pagamento",
    ]

    assert "DIETA ESPECIAL - TIPO A - INFANTIL" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO A - INFANTIL"]) == 3
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO A - INFANTIL"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
    ]

    assert "DIETA ESPECIAL - TIPO B - INFANTIL" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO B - INFANTIL"]) == 2
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO B - INFANTIL"] == [
        "lanche",
        "lanche_4h",
    ]

    assert "Solicitações de Alimentação" in dict_periodos_dietas
    assert len(dict_periodos_dietas["Solicitações de Alimentação"]) == 2
    assert dict_periodos_dietas["Solicitações de Alimentação"] == [
        "kit_lanche",
        "lanche_emergencial",
    ]


def test_get_valores_tabela(relatorio_consolidado_xlsx_cemei, mock_colunas_cemei):
    linhas = get_valores_tabela([relatorio_consolidado_xlsx_cemei], mock_colunas_cemei)
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 76
    assert linhas[0] == [
        "CEMEI",
        "543210",
        "CEMEI TESTE",
        5.0,
        5.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
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
        150.0,
        150.0,
        150.0,
        150.0,
        30.0,
        30.0,
        15.0,
        15.0,
        15.0,
    ]


def test_get_solicitacoes_ordenadas(
    solicitacao_escola_ceu_cemei,
    solicitacao_relatorio_consolidado_grupo_cemei,
):
    solicitacoes = [
        solicitacao_escola_ceu_cemei,
        solicitacao_relatorio_consolidado_grupo_cemei,
    ]
    ordenados = get_solicitacoes_ordenadas(solicitacoes)
    assert isinstance(ordenados, list)
    assert (
        ordenados[0].escola.nome
        == solicitacao_relatorio_consolidado_grupo_cemei.escola.nome
    )
    assert ordenados[1].escola.nome == solicitacao_escola_ceu_cemei.escola.nome


def test_processa_periodo_campo(
    relatorio_consolidado_xlsx_cemei, faixas_etarias_ativas
):
    valores_iniciais = [
        relatorio_consolidado_xlsx_cemei.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_cemei.escola.codigo_eol,
        relatorio_consolidado_xlsx_cemei.escola.nome,
    ]
    grupos_medicao = GrupoMedicao.objects.filter(
        nome__icontains="Infantil"
    ).values_list("nome", flat=True)

    integral_cei = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cemei,
        "INTEGRAL",
        faixas_etarias_ativas[0].id,
        valores_iniciais,
        grupos_medicao,
    )
    assert isinstance(integral_cei, list)
    assert len(integral_cei) == 4
    assert integral_cei == ["CEMEI", "543210", "CEMEI TESTE", 100.0]

    dieta_a_integral = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cemei,
        "DIETA ESPECIAL - TIPO A - INTEGRAL",
        faixas_etarias_ativas[0].id,
        valores_iniciais,
        grupos_medicao,
    )
    assert isinstance(dieta_a_integral, list)
    assert len(dieta_a_integral) == 5
    assert dieta_a_integral == ["CEMEI", "543210", "CEMEI TESTE", 100.0, 10.0]

    integral_emei = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cemei,
        "Infantil INTEGRAL",
        "refeicao",
        valores_iniciais,
        grupos_medicao,
    )
    assert isinstance(integral_emei, list)
    assert len(integral_emei) == 6
    assert integral_emei == ["CEMEI", "543210", "CEMEI TESTE", 100.0, 10.0, 150.0]

    dieta_a_lanche = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cemei,
        "DIETA ESPECIAL - TIPO A - INFANTIL",
        "lanche_4h",
        valores_iniciais,
        grupos_medicao,
    )
    assert isinstance(dieta_a_lanche, list)
    assert len(dieta_a_lanche) == 7
    assert dieta_a_lanche == [
        "CEMEI",
        "543210",
        "CEMEI TESTE",
        100.0,
        10.0,
        150.0,
        30.0,
    ]


def test_define_filtro(relatorio_consolidado_xlsx_cemei):
    grupos_medicao = GrupoMedicao.objects.filter(
        nome__icontains="Infantil"
    ).values_list("nome", flat=True)

    integral_cei = _define_filtro("INTEGRAL", grupos_medicao)
    assert isinstance(integral_cei, dict)
    assert "grupo__nome" not in integral_cei
    assert "periodo_escolar__nome" in integral_cei
    assert integral_cei["periodo_escolar__nome"] == "INTEGRAL"

    integral_emei = _define_filtro("Infantil INTEGRAL", grupos_medicao)
    assert isinstance(integral_emei, dict)
    assert "grupo__nome" in integral_emei
    assert "periodo_escolar__nome" not in integral_emei
    assert integral_emei["grupo__nome"] == "Infantil INTEGRAL"

    dieta_especial_cei = _define_filtro(
        "DIETA ESPECIAL - TIPO A - INTEGRAL", grupos_medicao
    )
    assert isinstance(dieta_especial_cei, dict)
    assert "grupo__nome__in" not in dieta_especial_cei
    assert "periodo_escolar__nome" in dieta_especial_cei
    assert dieta_especial_cei["periodo_escolar__nome"] == "INTEGRAL"

    dieta_especial_emei = _define_filtro(
        "DIETA ESPECIAL - TIPO A - INFANTIL", grupos_medicao
    )
    assert isinstance(dieta_especial_emei, dict)
    assert "grupo__nome__in" in dieta_especial_emei
    assert "periodo_escolar__nome__in" not in dieta_especial_emei
    assert dieta_especial_emei["grupo__nome__in"] == grupos_medicao


def test_processa_dieta_especial(
    relatorio_consolidado_xlsx_cemei, faixas_etarias_ativas
):
    grupos_medicao = GrupoMedicao.objects.filter(
        nome__icontains="Infantil"
    ).values_list("nome", flat=True)

    periodo = "INTEGRAL"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[2].id
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_cemei, filtros, faixa_etaria, periodo
    )
    assert total == "-"

    filtros = {"periodo_escolar__nome": "INTEGRAL"}
    periodo = "DIETA ESPECIAL - TIPO A - INTEGRAL"
    faixa_etaria = faixas_etarias_ativas[2].id
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_cemei, filtros, faixa_etaria, periodo
    )
    assert total == 10.0

    filtros = {"grupo__nome__in": grupos_medicao}
    periodo = "DIETA ESPECIAL - TIPO A - INFANTIL"
    campo = "lanche"
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_cemei, filtros, campo, periodo
    )
    assert total == 30.0


def test_processa_periodo_regular(
    relatorio_consolidado_xlsx_cemei, faixas_etarias_ativas
):
    periodo = "INTEGRAL"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = _processa_periodo_regular(
        relatorio_consolidado_xlsx_cemei, filtros, faixa_etaria, periodo
    )
    assert total == 100.0

    periodo = "Infantil INTEGRAL"
    filtros = {"grupo__nome": periodo}
    campo = "lanche"
    total = _processa_periodo_regular(
        relatorio_consolidado_xlsx_cemei, filtros, campo, periodo
    )
    assert total == 150.0

    filtros = {"nome": "INTEGRAL"}
    periodo = "DIETA ESPECIAL - TIPO A - INTEGRAL"
    campo = "lanche"
    total = _processa_periodo_regular(
        relatorio_consolidado_xlsx_cemei, filtros, campo, periodo
    )
    assert total == "-"


def test_insere_tabela_periodos_na_planilha(
    informacoes_excel_writer_cemei, mock_colunas_cemei, mock_linhas_cemei
):
    aba, writer, _, _, _, _ = informacoes_excel_writer_cemei

    df = insere_tabela_periodos_na_planilha(
        aba, mock_colunas_cemei, mock_linhas_cemei, writer
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 76

    assert sum(1 for tupla in colunas_df if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas_df if tupla[0] == "PARCIAL") == 8
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO A - INTEGRAL"
        )
        == 8
    )
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO B - INTEGRAL"
        )
        == 8
    )
    assert (
        sum(
            1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A - PARCIAL"
        )
        == 8
    )
    assert (
        sum(
            1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B - PARCIAL"
        )
        == 8
    )
    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL INTEGRAL") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL MANHA") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL TARDE") == 6
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO A - INFANTIL"
        )
        == 3
    )
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO B - INFANTIL"
        )
        == 2
    )

    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Kit Lanche") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche Emerg.") == 1

    assert sum(1 for tupla in colunas_df if tupla[1] == "00 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "01 a 03 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 a 05 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "06 a 07 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "08 a 11 meses") == 6
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "01 ano a 01 ano e 11 meses") == 6
    )
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "02 anos a 03 anos e 11 meses")
        == 6
    )
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 anos a 06 anos") == 6

    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche") == 5
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 4h") == 5
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeição") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeições p/ Pagamento") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesa") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesas p/ Pagamento") == 3

    assert df.iloc[0].tolist() == [
        "CEMEI",
        "543210",
        "CEMEI TESTE",
        5.0,
        5.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
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
        150.0,
        150.0,
        150.0,
        150.0,
        30.0,
        30.0,
        15.0,
        15.0,
        15.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        543210.0,
        0.0,
        5.0,
        5.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
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
        150.0,
        150.0,
        150.0,
        150.0,
        30.0,
        30.0,
        15.0,
        15.0,
        15.0,
    ]


def test_ajusta_layout_tabela(informacoes_excel_writer_cemei):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_cemei
    ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 12
    esperados = {
        "A3:E3",
        "F3:M3",
        "N3:U3",
        "V3:AC3",
        "AD3:AK3",
        "AL3:AS3",
        "AT3:BA3",
        "BB3:BG3",
        "BH3:BM3",
        "BN3:BS3",
        "BT3:BV3",
        "BW3:BX3",
    }
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A3"].value is None

    assert sheet["F3"].value == "INTEGRAL"
    assert sheet["F3"].fill.fgColor.rgb == "FF198459"

    assert sheet["N3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["N3"].fill.fgColor.rgb == "FF198459"

    assert sheet["V3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["V3"].fill.fgColor.rgb == "FF198459"

    assert sheet["AD3"].value == "PARCIAL"
    assert sheet["AD3"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["AL3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["AL3"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["AT3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["AT3"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["BB3"].value == "INFANTIL INTEGRAL"
    assert sheet["BB3"].fill.fgColor.rgb == "FFB40C02"

    assert sheet["BH3"].value == "INFANTIL MANHA"
    assert sheet["BH3"].fill.fgColor.rgb == "FFC13FD6"

    assert sheet["BN3"].value == "INFANTIL TARDE"
    assert sheet["BN3"].fill.fgColor.rgb == "FF2F80ED"

    assert sheet["BT3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["BT3"].fill.fgColor.rgb == "FF20AA73"

    assert sheet["BW3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["BW3"].fill.fgColor.rgb == "FF198459"

    workbook_openpyxl.close()
