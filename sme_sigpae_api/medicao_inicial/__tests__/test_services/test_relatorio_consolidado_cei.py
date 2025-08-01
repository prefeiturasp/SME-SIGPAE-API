import openpyxl
import pandas as pd
import pytest

from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_cei import (
    _calcula_soma_medicao,
    _define_filtro,
    _get_faixas_etarias,
    _get_lista_alimentacoes_dietas_por_faixa,
    _processa_periodo_campo,
    _sort_and_merge,
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_solicitacoes_ordenadas,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
    processa_dieta_especial,
    processa_periodo_regular,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    colunas = get_alimentacoes_por_periodo([relatorio_consolidado_xlsx_cei])
    assert isinstance(colunas, list)
    assert len(colunas) == 54
    assert sum(1 for tupla in colunas if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "PARCIAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "TARDE") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 1
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 1
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

    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[0].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[1].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[2].id) == 8
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[3].id) == 8
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[4].id) == 7
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[5].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[6].id) == 7
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[7].id) == 6


def test_get_faixas_etarias(relatorio_consolidado_xlsx_cei, faixas_etarias_ativas):
    faixas = [faixa.id for faixa in faixas_etarias_ativas]
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    faixa_integral = _get_faixas_etarias(medicoes[0])
    assert isinstance(faixa_integral, list)
    assert len(faixa_integral) == 8
    assert faixa_integral == faixas

    faixa_manha = _get_faixas_etarias(medicoes[1])
    assert isinstance(faixa_manha, list)
    assert len(faixa_manha) == 2
    assert faixa_manha == [faixas_etarias_ativas[2].id, faixas_etarias_ativas[4].id]

    faixa_parcial = _get_faixas_etarias(medicoes[2])
    assert isinstance(faixa_parcial, list)
    assert len(faixa_parcial) == 8
    assert faixa_parcial == faixas

    faixa_tarde = _get_faixas_etarias(medicoes[3])
    assert isinstance(faixa_tarde, list)
    assert len(faixa_tarde) == 2
    assert faixa_tarde == [faixas_etarias_ativas[3].id, faixas_etarias_ativas[6].id]


def test_get_lista_alimentacoes_dietas_por_faixa_dieta_a(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    dieta = "DIETA ESPECIAL - TIPO A"

    lista_dietas_integral = _get_lista_alimentacoes_dietas_por_faixa(medicoes[0], dieta)
    assert isinstance(lista_dietas_integral, list)
    assert len(lista_dietas_integral) == 8

    lista_dietas_manha = _get_lista_alimentacoes_dietas_por_faixa(medicoes[1], dieta)
    assert isinstance(lista_dietas_manha, list)
    assert len(lista_dietas_manha) == 1
    assert lista_dietas_manha == [faixas_etarias_ativas[2].id]

    lista_dietas_parcial = _get_lista_alimentacoes_dietas_por_faixa(medicoes[2], dieta)
    assert isinstance(lista_dietas_parcial, list)
    assert len(lista_dietas_parcial) == 8

    lista_dietas_tarde = _get_lista_alimentacoes_dietas_por_faixa(medicoes[3], dieta)
    assert isinstance(lista_dietas_tarde, list)
    assert len(lista_dietas_tarde) == 0


def test_get_lista_alimentacoes_dietas_por_faixa_dieta_b(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    dieta = "DIETA ESPECIAL - TIPO B"

    lista_dietas_integral = _get_lista_alimentacoes_dietas_por_faixa(medicoes[0], dieta)
    assert isinstance(lista_dietas_integral, list)
    assert len(lista_dietas_integral) == 8

    lista_dietas_manha = _get_lista_alimentacoes_dietas_por_faixa(medicoes[1], dieta)
    assert isinstance(lista_dietas_manha, list)
    assert len(lista_dietas_manha) == 0

    lista_dietas_parcial = _get_lista_alimentacoes_dietas_por_faixa(medicoes[2], dieta)
    assert isinstance(lista_dietas_parcial, list)
    assert len(lista_dietas_parcial) == 8

    lista_dietas_tarde = _get_lista_alimentacoes_dietas_por_faixa(medicoes[3], dieta)
    assert isinstance(lista_dietas_tarde, list)
    assert len(lista_dietas_tarde) == 1
    assert lista_dietas_tarde == [faixas_etarias_ativas[3].id]


def test_sort_and_merge(faixas_etarias_ativas):
    faixas = [faixa.id for faixa in faixas_etarias_ativas]
    periodos_alimentacoes = {
        "MANHA": faixas,
        "INTEGRAL": faixas,
        "PARCIAL": faixas,
        "TARDE": faixas,
    }
    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO A": faixas,
        "DIETA ESPECIAL - TIPO B": faixas,
    }
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    assert isinstance(dict_periodos_dietas, dict)

    assert "INTEGRAL" in dict_periodos_dietas
    assert len(dict_periodos_dietas["INTEGRAL"]) == 8
    assert dict_periodos_dietas["INTEGRAL"] == faixas

    assert "MANHA" in dict_periodos_dietas
    assert len(dict_periodos_dietas["MANHA"]) == 8
    assert dict_periodos_dietas["MANHA"] == faixas

    assert "PARCIAL" in dict_periodos_dietas
    assert len(dict_periodos_dietas["PARCIAL"]) == 8
    assert dict_periodos_dietas["PARCIAL"] == faixas

    assert "TARDE" in dict_periodos_dietas
    assert len(dict_periodos_dietas["TARDE"]) == 8
    assert dict_periodos_dietas["TARDE"] == faixas

    assert "DIETA ESPECIAL - TIPO A" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO A"]) == 8
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO A"] == faixas

    assert "DIETA ESPECIAL - TIPO B" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO B"]) == 8
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO B"] == faixas


def test_get_valores_tabela(relatorio_consolidado_xlsx_cei, mock_colunas_cei):
    tipos_unidade = ["CEI"]
    linhas = get_valores_tabela(
        [relatorio_consolidado_xlsx_cei], mock_colunas_cei, tipos_unidade
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 57
    assert linhas[0] == [
        "CEI DIRET",
        "765432",
        "CEI DIRET TESTE",
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        80.0,
        60.0,
        60.0,
        80.0,
        8.0,
        4.0,
    ]


def test_get_solicitacoes_ordenadas(
    solicitacao_escola_cci,
    solicitacao_relatorio_consolidado_grupo_cei,
):
    tipos_de_unidade = ["CEI"]
    solicitacoes = [
        solicitacao_relatorio_consolidado_grupo_cei,
        solicitacao_escola_cci,
    ]
    ordenados = get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade)
    assert isinstance(ordenados, list)
    assert (
        ordenados[0].escola.nome
        == solicitacao_relatorio_consolidado_grupo_cei.escola.nome
    )
    assert ordenados[1].escola.nome == solicitacao_escola_cci.escola.nome


def test_processa_periodo_campo(relatorio_consolidado_xlsx_cei, faixas_etarias_ativas):
    valores_iniciais = [
        relatorio_consolidado_xlsx_cei.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_cei.escola.codigo_eol,
        relatorio_consolidado_xlsx_cei.escola.nome,
    ]

    integral = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cei,
        "INTEGRAL",
        faixas_etarias_ativas[0].id,
        valores_iniciais,
    )
    assert isinstance(integral, list)
    assert len(integral) == 4
    assert integral == ["CEI DIRET", "765432", "CEI DIRET TESTE", 80]

    manha = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cei,
        "TARDE",
        faixas_etarias_ativas[0].id,
        valores_iniciais,
    )
    assert isinstance(manha, list)
    assert len(manha) == 5
    assert manha == ["CEI DIRET", "765432", "CEI DIRET TESTE", 80.0, "-"]


def test_define_filtro(relatorio_consolidado_xlsx_cei):

    manha = _define_filtro("MANHA")
    assert isinstance(manha, dict)
    assert "grupo__nome" not in manha
    assert "periodo_escolar__nome" in manha
    assert manha["periodo_escolar__nome"] == "MANHA"

    dieta_especial = _define_filtro("DIETA ESPECIAL - TIPO A")
    assert isinstance(dieta_especial, dict)
    assert "grupo__nome" not in dieta_especial
    assert "periodo_escolar__nome__in" in dieta_especial
    assert dieta_especial["periodo_escolar__nome__in"] == ["MANHA", "TARDE"]

    dieta_especial = _define_filtro("DIETA ESPECIAL - TIPO A - PARCIAL")
    assert isinstance(dieta_especial, dict)
    assert "grupo__nome" not in dieta_especial
    assert "periodo_escolar__nome" in dieta_especial
    assert dieta_especial["periodo_escolar__nome"] == "PARCIAL"

    solicitacao = _define_filtro("Solicitações de Alimentação")
    assert isinstance(solicitacao, dict)
    assert "periodo_escolar__nome" not in solicitacao
    assert "grupo__nome" in solicitacao
    assert solicitacao["grupo__nome"] == "Solicitações de Alimentação"


def test_processa_dieta_especial(relatorio_consolidado_xlsx_cei, faixas_etarias_ativas):
    periodo = "NOITE"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[2].id
    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == "-"

    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    filtros = {"periodo_escolar__nome__in": ["MANHA", "TARDE"]}
    periodo = "DIETA ESPECIAL - TIPO A"
    faixa_etaria = faixas_etarias_ativas[2].id
    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == 8.0

    filtros = {"periodo_escolar__nome": "PARCIAL"}
    periodo = "DIETA ESPECIAL - TIPO A - PARCIAL"
    faixa_etaria = faixas_etarias_ativas[2].id
    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == 8.0


def test_processa_periodo_regular(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    periodo = "MANHA"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = processa_periodo_regular(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == "-"

    periodo = "INTEGRAL"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = processa_periodo_regular(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == 80.0

    periodo = "NOITE"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = processa_periodo_regular(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == "-"


def test_calcula_soma_medicao_alimentacao(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )

    faixa_etaria = faixas_etarias_ativas[0].id
    categoria = "ALIMENTAÇÃO"

    integral = _calcula_soma_medicao(medicoes[0], faixa_etaria, categoria)
    assert integral == 80.0

    manha = _calcula_soma_medicao(medicoes[1], faixa_etaria, categoria)
    assert manha is None

    parcial = _calcula_soma_medicao(medicoes[2], faixa_etaria, categoria)
    assert parcial == 80.0

    tarde = _calcula_soma_medicao(medicoes[3], faixa_etaria, categoria)
    assert tarde is None


def test_calcula_soma_medicao_dieta_especial(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )

    faixa_etaria = faixas_etarias_ativas[2].id
    categoria = "DIETA ESPECIAL - TIPO A"

    integral = _calcula_soma_medicao(medicoes[0], faixa_etaria, categoria)
    assert integral == 8.0

    manha = _calcula_soma_medicao(medicoes[1], faixa_etaria, categoria)
    assert manha == 8.0

    parcial = _calcula_soma_medicao(medicoes[2], faixa_etaria, categoria)
    assert parcial == 8.0

    tarde = _calcula_soma_medicao(medicoes[3], faixa_etaria, categoria)
    assert tarde is None


def test_insere_tabela_periodos_na_planilha(
    informacoes_excel_writer_cei,
    mock_colunas_cei,
    mock_linhas_cei,
):
    aba, writer, _, _, _, _ = informacoes_excel_writer_cei
    df = insere_tabela_periodos_na_planilha(
        aba, mock_colunas_cei, mock_linhas_cei, writer
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 57

    assert sum(1 for tupla in colunas_df if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas_df if tupla[0] == "PARCIAL") == 8
    assert sum(1 for tupla in colunas_df if tupla[0] == "MANHA") == 2
    assert sum(1 for tupla in colunas_df if tupla[0] == "TARDE") == 2
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 1
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 1
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

    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1

    assert sum(1 for tupla in colunas_df if tupla[1] == "00 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "01 a 03 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 a 05 meses") == 8
    assert sum(1 for tupla in colunas_df if tupla[1] == "06 a 07 meses") == 8
    assert sum(1 for tupla in colunas_df if tupla[1] == "08 a 11 meses") == 7
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "01 ano a 01 ano e 11 meses") == 6
    )
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "02 anos a 03 anos e 11 meses")
        == 7
    )
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 anos a 06 anos") == 6

    assert df.iloc[0].tolist() == [
        "CEI DIRET",
        "765432",
        "CEI DIRET TESTE",
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        80.0,
        60.0,
        60.0,
        80.0,
        8.0,
        4.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        765432.0,
        0.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        8.0,
        80.0,
        60.0,
        60.0,
        80.0,
        8.0,
        4.0,
    ]


def test_ajusta_layout_tabela(informacoes_excel_writer_cei):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_cei
    ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 9
    assert "A3:C3" in str(merged_ranges)
    assert "D3:K3" in str(merged_ranges)
    assert "L3:S3" in str(merged_ranges)
    assert "T3:AA3" in str(merged_ranges)
    assert "AB3:AI3" in str(merged_ranges)
    assert "AJ3:AQ3" in str(merged_ranges)
    assert "AR3:AY3" in str(merged_ranges)
    assert "AZ3:BA3" in str(merged_ranges)
    assert "BB3:BC3" in str(merged_ranges)

    assert sheet["A3"].value is None

    assert sheet["D3"].value == "INTEGRAL"
    assert sheet["D3"].fill.fgColor.rgb == "FF198459"

    assert sheet["L3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["L3"].fill.fgColor.rgb == "FF198459"

    assert sheet["T3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["T3"].fill.fgColor.rgb == "FF198459"

    assert sheet["AB3"].value == "PARCIAL"
    assert sheet["AB3"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["AJ3"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["AJ3"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["AR3"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["AR3"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["AZ3"].value == "MANHA"
    assert sheet["AZ3"].fill.fgColor.rgb == "FFC13FD6"

    assert sheet["BB3"].value == "TARDE"
    assert sheet["BB3"].fill.fgColor.rgb == "FF2F80ED"
    workbook_openpyxl.close()
