import openpyxl
import pandas as pd
import pytest
from django.core.exceptions import MultipleObjectsReturned

from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_cei import (
    _calcula_soma_medicao,
    _define_filtro,
    _generate_columns,
    _get_categorias_dietas,
    _get_faixas_etarias,
    _get_lista_alimentacoes_dietas_por_faixa,
    _get_nome_periodo,
    _get_valores_iniciais,
    _processa_dieta_especial,
    _processa_periodo_campo,
    _processa_periodo_regular,
    _sort_and_merge,
    _update_dietas_alimentacoes_por_faixa,
    _update_periodos_alimentacoes,
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_solicitacoes_ordenadas,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    colunas = get_alimentacoes_por_periodo([relatorio_consolidado_xlsx_cei])
    assert isinstance(colunas, list)
    assert len(colunas) == 22
    assert sum(1 for tupla in colunas if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "PARCIAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "TARDE") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 1
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 1

    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[0].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[1].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[2].id) == 4
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[3].id) == 4
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[4].id) == 3
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[5].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[6].id) == 3
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[7].id) == 2


def test_get_nome_periodo(relatorio_consolidado_xlsx_cei):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    integral = _get_nome_periodo(medicoes[0])
    assert isinstance(integral, str)
    assert integral == "INTEGRAL"

    manha = _get_nome_periodo(medicoes[1])
    assert isinstance(manha, str)
    assert manha == "MANHA"

    parcial = _get_nome_periodo(medicoes[2])
    assert isinstance(parcial, str)
    assert parcial == "PARCIAL"

    tarde = _get_nome_periodo(medicoes[3])
    assert isinstance(tarde, str)
    assert tarde == "TARDE"


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


def test_update_periodos_alimentacoes(faixas_etarias_ativas):
    lista_faixas = [faixa.id for faixa in faixas_etarias_ativas]

    periodos_alimentacoes = _update_periodos_alimentacoes({}, "MANHA", lista_faixas)
    assert isinstance(periodos_alimentacoes, dict)
    assert "MANHA" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["MANHA"] == lista_faixas

    periodos_alimentacoes = _update_periodos_alimentacoes(
        periodos_alimentacoes, "INTEGRAL", lista_faixas
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "INTEGRAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["INTEGRAL"] == lista_faixas

    periodos_alimentacoes = _update_periodos_alimentacoes(
        periodos_alimentacoes, "PARCIAL", lista_faixas
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "PARCIAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["PARCIAL"] == lista_faixas

    periodos_alimentacoes = _update_periodos_alimentacoes(
        periodos_alimentacoes, "TARDE", lista_faixas
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "TARDE" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["TARDE"] == lista_faixas

    assert set(["MANHA", "INTEGRAL", "PARCIAL", "TARDE"]).issubset(
        periodos_alimentacoes.keys()
    )


def test_get_categorias_dietas(relatorio_consolidado_xlsx_cei):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    categoria_integral = _get_categorias_dietas(medicoes[0])
    assert isinstance(categoria_integral, list)
    assert len(categoria_integral) == 0

    categoria_manha = _get_categorias_dietas(medicoes[1])
    assert isinstance(categoria_manha, list)
    assert len(categoria_manha) == 1
    assert categoria_manha == ["DIETA ESPECIAL - TIPO A"]

    categoria_parcial = _get_categorias_dietas(medicoes[2])
    assert isinstance(categoria_parcial, list)
    assert len(categoria_parcial) == 0

    categoria_tarde = _get_categorias_dietas(medicoes[3])
    assert isinstance(categoria_tarde, list)
    assert len(categoria_tarde) == 1
    assert categoria_tarde == ["DIETA ESPECIAL - TIPO B"]


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
    assert len(lista_dietas_integral) == 0

    lista_dietas_manha = _get_lista_alimentacoes_dietas_por_faixa(medicoes[1], dieta)
    assert isinstance(lista_dietas_manha, list)
    assert len(lista_dietas_manha) == 1
    assert lista_dietas_manha == [faixas_etarias_ativas[2].id]

    lista_dietas_parcial = _get_lista_alimentacoes_dietas_por_faixa(medicoes[2], dieta)
    assert isinstance(lista_dietas_parcial, list)
    assert len(lista_dietas_parcial) == 0

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
    assert len(lista_dietas_integral) == 0

    lista_dietas_manha = _get_lista_alimentacoes_dietas_por_faixa(medicoes[1], dieta)
    assert isinstance(lista_dietas_manha, list)
    assert len(lista_dietas_manha) == 0

    lista_dietas_parcial = _get_lista_alimentacoes_dietas_por_faixa(medicoes[2], dieta)
    assert isinstance(lista_dietas_parcial, list)
    assert len(lista_dietas_parcial) == 0

    lista_dietas_tarde = _get_lista_alimentacoes_dietas_por_faixa(medicoes[3], dieta)
    assert isinstance(lista_dietas_tarde, list)
    assert len(lista_dietas_tarde) == 1
    assert lista_dietas_tarde == [faixas_etarias_ativas[3].id]


def test_update_dietas_alimentacoes_por_faixa(faixas_etarias_ativas):
    lista_faixa_dietas = [faixa.id for faixa in faixas_etarias_ativas]
    categoria_a = "DIETA ESPECIAL - TIPO A"
    categoria_b = "DIETA ESPECIAL - TIPO B"

    dietas_alimentacoes = _update_dietas_alimentacoes_por_faixa(
        {}, categoria_a, lista_faixa_dietas
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_a in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_a] == lista_faixa_dietas

    dietas_alimentacoes = _update_dietas_alimentacoes_por_faixa(
        dietas_alimentacoes, categoria_b, lista_faixa_dietas
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_b in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_b] == lista_faixa_dietas

    assert set([categoria_a, categoria_b]).issubset(dietas_alimentacoes.keys())


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


def test_generate_columns(faixas_etarias_ativas):
    faixas = [faixa.id for faixa in faixas_etarias_ativas]
    faixas_dietas = [
        faixa.id for faixa in faixas_etarias_ativas if faixa.inicio not in [1, 6, 12]
    ]
    dict_periodos_dietas = {
        "MANHA": faixas,
        "INTEGRAL": faixas,
        "PARCIAL": faixas,
        "TARDE": faixas,
        "DIETA ESPECIAL - TIPO A": faixas_dietas,
        "DIETA ESPECIAL - TIPO B": faixas_dietas,
    }

    colunas = _generate_columns(dict_periodos_dietas)
    assert isinstance(colunas, list)
    assert len(colunas) == 42
    assert sum(1 for tupla in colunas if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "PARCIAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "TARDE") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 5
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 5

    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[0].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[1].id) == 4
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[2].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[3].id) == 4
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[4].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[5].id) == 4
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[6].id) == 6
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[7].id) == 6


def test_get_valores_tabela(relatorio_consolidado_xlsx_cei, mock_colunas_cei):
    tipos_unidade = ["CEI"]
    linhas = get_valores_tabela(
        [relatorio_consolidado_xlsx_cei], mock_colunas_cei, tipos_unidade
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 25
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
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
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
    assert ordenados[0].escola.nome == solicitacao_escola_cci.escola.nome
    assert (
        ordenados[1].escola.nome
        == solicitacao_relatorio_consolidado_grupo_cei.escola.nome
    )


def test_get_valores_iniciais(relatorio_consolidado_xlsx_cei):
    valores = _get_valores_iniciais(relatorio_consolidado_xlsx_cei)
    assert isinstance(valores, list)
    assert len(valores) == 3
    assert valores == [
        relatorio_consolidado_xlsx_cei.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_cei.escola.codigo_eol,
        relatorio_consolidado_xlsx_cei.escola.nome,
    ]


def test_processa_periodo_campo(relatorio_consolidado_xlsx_cei, faixas_etarias_ativas):
    valores_iniciais = [
        relatorio_consolidado_xlsx_cei.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_cei.escola.codigo_eol,
        relatorio_consolidado_xlsx_cei.escola.nome,
    ]
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    integral = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cei,
        "INTEGRAL",
        faixas_etarias_ativas[0].id,
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(integral, list)
    assert len(integral) == 4
    assert integral == ["CEI DIRET", "765432", "CEI DIRET TESTE", 80]

    manha = _processa_periodo_campo(
        relatorio_consolidado_xlsx_cei,
        "TARDE",
        faixas_etarias_ativas[0].id,
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )
    assert isinstance(manha, list)
    assert len(manha) == 5
    assert manha == ["CEI DIRET", "765432", "CEI DIRET TESTE", 80.0, "-"]


def test_define_filtro(relatorio_consolidado_xlsx_cei):
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


def test_processa_dieta_especial(relatorio_consolidado_xlsx_cei, faixas_etarias_ativas):
    periodo = "NOITE"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[2].id
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == "-"

    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    filtros = {"periodo_escolar__nome__in": periodos_escolares}
    periodo = "DIETA ESPECIAL - TIPO A"
    faixa_etaria = faixas_etarias_ativas[2].id
    total = _processa_dieta_especial(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == 8.0


def test_processa_periodo_regular(
    relatorio_consolidado_xlsx_cei, faixas_etarias_ativas
):
    periodo = "MANHA"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = _processa_periodo_regular(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == "-"

    periodo = "INTEGRAL"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = _processa_periodo_regular(
        relatorio_consolidado_xlsx_cei, filtros, faixa_etaria, periodo
    )
    assert total == 80.0

    periodo = "NOITE"
    filtros = {"periodo_escolar__nome": periodo}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = _processa_periodo_regular(
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
    assert integral is None

    manha = _calcula_soma_medicao(medicoes[1], faixa_etaria, categoria)
    assert manha == 8

    parcial = _calcula_soma_medicao(medicoes[2], faixa_etaria, categoria)
    assert parcial is None

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
    assert len(colunas_df) == 25

    assert sum(1 for tupla in colunas_df if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas_df if tupla[0] == "PARCIAL") == 8
    assert sum(1 for tupla in colunas_df if tupla[0] == "MANHA") == 2
    assert sum(1 for tupla in colunas_df if tupla[0] == "TARDE") == 2
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 1
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 1

    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1

    assert sum(1 for tupla in colunas_df if tupla[1] == "00 meses") == 2
    assert sum(1 for tupla in colunas_df if tupla[1] == "01 a 03 meses") == 2
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 a 05 meses") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "06 a 07 meses") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "08 a 11 meses") == 3
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "01 ano a 01 ano e 11 meses") == 2
    )
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "02 anos a 03 anos e 11 meses")
        == 3
    )
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 anos a 06 anos") == 2

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
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
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
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
        80.0,
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
    assert len(merged_ranges) == 5
    assert str(merged_ranges[0]) == "A3:C3"
    assert str(merged_ranges[1]) == "D3:K3"
    assert str(merged_ranges[2]) == "L3:S3"
    assert str(merged_ranges[3]) == "T3:U3"
    assert str(merged_ranges[4]) == "V3:W3"

    assert sheet["A3"].value is None

    assert sheet["D3"].value == "INTEGRAL"
    assert sheet["D3"].fill.fgColor.rgb == "FF198459"

    assert sheet["L3"].value == "PARCIAL"
    assert sheet["L3"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["T3"].value == "MANHA"
    assert sheet["T3"].fill.fgColor.rgb == "FFC13FD6"

    assert sheet["V3"].value == "TARDE"
    assert sheet["V3"].fill.fgColor.rgb == "FF2F80ED"
    workbook_openpyxl.close()
