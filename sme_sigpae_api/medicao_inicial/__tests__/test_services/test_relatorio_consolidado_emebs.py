from io import BytesIO

import openpyxl
import pandas as pd
import pytest

from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_emebs import (
    _calcula_soma_medicao,
    _define_filtro,
    _generate_columns,
    _get_categorias_dietas,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _get_total_pagamento,
    _obter_dietas_especiais,
    _processa_periodo_campo,
    _sort_and_merge,
    _total_pagamento_fundamental,
    _total_pagamento_infantil,
    _unificar_dietas_tipo_a,
    _update_dietas_alimentacoes,
    _update_periodos_alimentacoes,
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_solicitacoes_ordenadas,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
    processa_dieta_especial,
    processa_periodo_regular,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(relatorio_consolidado_xlsx_emebs):
    colunas = get_alimentacoes_por_periodo([relatorio_consolidado_xlsx_emebs])
    assert isinstance(colunas, list)
    assert len(colunas) == 66
    assert sum(1 for tupla in colunas if tupla[0] == "INFANTIL") == 29
    assert sum(1 for tupla in colunas if tupla[0] == "FUNDAMENTAL") == 35
    assert sum(1 for tupla in colunas if tupla[1] == "Solicitações de Alimentação") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "MANHA") == 12
    assert sum(1 for tupla in colunas if tupla[1] == "TARDE") == 12
    assert sum(1 for tupla in colunas if tupla[1] == "INTEGRAL") == 12
    assert sum(1 for tupla in colunas if tupla[1] == "NOITE") == 6
    assert sum(1 for tupla in colunas if tupla[1] == "Programas e Projetos") == 12
    assert sum(1 for tupla in colunas if tupla[1] == "DIETA ESPECIAL - TIPO A") == 6
    assert sum(1 for tupla in colunas if tupla[1] == "DIETA ESPECIAL - TIPO B") == 4
    assert sum(1 for tupla in colunas if tupla[2] == "kit_lanche") == 1
    assert sum(1 for tupla in colunas if tupla[2] == "lanche_emergencial") == 1
    assert sum(1 for tupla in colunas if tupla[2] == "lanche") == 13
    assert sum(1 for tupla in colunas if tupla[2] == "lanche_4h") == 13
    assert sum(1 for tupla in colunas if tupla[2] == "refeicao") == 11
    assert sum(1 for tupla in colunas if tupla[2] == "sobremesa") == 9
    assert sum(1 for tupla in colunas if tupla[2] == "total_refeicoes_pagamento") == 9
    assert sum(1 for tupla in colunas if tupla[2] == "total_sobremesas_pagamento") == 9


def test_get_lista_alimentacoes(relatorio_consolidado_xlsx_emebs):
    retorno = [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    assert medicoes.count() == 6

    integral = _get_lista_alimentacoes(medicoes[0], "INTEGRAL")
    assert isinstance(integral, tuple)
    assert integral == (
        retorno,
        retorno,
    )

    manha = _get_lista_alimentacoes(medicoes[1], "MANHA")
    assert isinstance(manha, tuple)
    assert manha == (
        retorno,
        retorno,
    )

    noite = _get_lista_alimentacoes(medicoes[2], "NOITE")
    assert isinstance(noite, tuple)
    assert noite == (
        [],
        retorno,
    )

    tarde = _get_lista_alimentacoes(medicoes[3], "TARDE")
    assert isinstance(tarde, tuple)
    assert tarde == (
        retorno,
        retorno,
    )

    programas_projetos = _get_lista_alimentacoes(medicoes[4], "Programas e Projetos")
    assert isinstance(programas_projetos, tuple)
    assert programas_projetos == (
        retorno,
        retorno,
    )

    solicitacao = _get_lista_alimentacoes(medicoes[5], "Solicitações de Alimentação")
    assert isinstance(solicitacao, tuple)
    assert solicitacao == (
        [],
        ["kit_lanche", "lanche_emergencial"],
    )


def test_update_periodos_alimentacoes():
    lista_alimentacoes = [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]
    periodos_alimentacoes = {}

    periodos_alimentacoes = _update_periodos_alimentacoes(
        periodos_alimentacoes, "MANHA", lista_alimentacoes, turma="INFANTIL"
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "INFANTIL" in periodos_alimentacoes.keys()
    assert "MANHA" in periodos_alimentacoes["INFANTIL"].keys()
    assert periodos_alimentacoes["INFANTIL"]["MANHA"] == lista_alimentacoes

    periodos_alimentacoes = _update_periodos_alimentacoes(
        periodos_alimentacoes, "NOITE", lista_alimentacoes, turma="FUNDAMENTAL"
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "FUNDAMENTAL" in periodos_alimentacoes.keys()
    assert "NOITE" in periodos_alimentacoes["FUNDAMENTAL"].keys()
    assert periodos_alimentacoes["FUNDAMENTAL"]["NOITE"] == lista_alimentacoes

    assert set(["INFANTIL", "FUNDAMENTAL"]).issubset(periodos_alimentacoes.keys())


def test_get_categorias_dietas(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    dietas = [
        "DIETA ESPECIAL - TIPO A",
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
        "DIETA ESPECIAL - TIPO B",
    ]

    categoria_integral = _get_categorias_dietas(medicoes[0])
    assert isinstance(categoria_integral, tuple)
    assert len(categoria_integral) == 2
    assert categoria_integral == (
        dietas,
        dietas,
    )

    categoria_programas_projetos = _get_categorias_dietas(medicoes[4])
    assert isinstance(categoria_programas_projetos, tuple)
    assert len(categoria_programas_projetos) == 2
    assert categoria_programas_projetos == (
        dietas,
        dietas,
    )


def test_obter_dietas_especiais(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    dietas = [
        "DIETA ESPECIAL - TIPO A",
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
        "DIETA ESPECIAL - TIPO B",
    ]
    dietas_alimentacoes = {}
    dietas_alimentacoes = _obter_dietas_especiais(
        dietas_alimentacoes, medicoes[0], dietas, turma="INFANTIL"
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert "INFANTIL" in dietas_alimentacoes.keys()
    assert set(dietas).issubset(dietas_alimentacoes["INFANTIL"].keys())
    assert dietas_alimentacoes["INFANTIL"]["DIETA ESPECIAL - TIPO A"] == [
        "lanche",
        "lanche_4h",
    ]
    assert dietas_alimentacoes["INFANTIL"][
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    ] == ["lanche", "lanche_4h", "refeicao"]
    assert dietas_alimentacoes["INFANTIL"]["DIETA ESPECIAL - TIPO B"] == [
        "lanche",
        "lanche_4h",
    ]


def test_get_lista_alimentacoes_dietas(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )

    lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
        medicoes[4],
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
        turma="FUNDAMENTAL",
    )
    assert isinstance(lista_alimentacoes_dietas, list)
    assert lista_alimentacoes_dietas == ["lanche", "lanche_4h", "refeicao"]

    lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
        medicoes[4], "DIETA ESPECIAL - TIPO B", turma="FUNDAMENTAL"
    )
    assert isinstance(lista_alimentacoes_dietas, list)
    assert lista_alimentacoes_dietas == ["lanche", "lanche_4h"]


def test_update_dietas_alimentacoes():
    lista_alimentacoes = ["lanche", "lanche_4h"]
    dietas_alimentacoes = _update_dietas_alimentacoes(
        {}, "DIETA ESPECIAL - TIPO A", lista_alimentacoes, turma="FUNDAMENTAL"
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert "FUNDAMENTAL" in dietas_alimentacoes.keys()
    assert "DIETA ESPECIAL - TIPO A" in dietas_alimentacoes["FUNDAMENTAL"].keys()
    assert (
        dietas_alimentacoes["FUNDAMENTAL"]["DIETA ESPECIAL - TIPO A"]
        == lista_alimentacoes
    )


def test_unificar_dietas():
    dietas_alimentacoes = {
        "FUNDAMENTAL": {
            "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS": [
                "lanche",
                "lanche_4h",
                "refeicao",
            ],
            "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
        }
    }
    resultado = _unificar_dietas_tipo_a(dietas_alimentacoes, turma="FUNDAMENTAL")
    assert "FUNDAMENTAL" in resultado.keys()
    assert "DIETA ESPECIAL - TIPO A" in resultado["FUNDAMENTAL"]
    assert "DIETA ESPECIAL - TIPO B" in resultado["FUNDAMENTAL"]
    assert (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
        not in resultado["FUNDAMENTAL"]
    )
    assert len(resultado["FUNDAMENTAL"]["DIETA ESPECIAL - TIPO A"]) == 3


def test_sort_and_merge():
    refeicoes = [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]
    dieta_a = [
        "refeicao",
        "lanche",
        "lanche_4h",
    ]
    dieta_b = [
        "lanche_4h",
        "lanche",
    ]
    periodos_alimentacoes = {
        "INFANTIL": {
            "MANHA": refeicoes,
        },
        "FUNDAMENTAL": {
            "MANHA": refeicoes,
            "Solicitações de Alimentação": ["kit_lanche", "lanche_emergencial"],
        },
    }

    dietas_alimentacoes = {
        "INFANTIL": {
            "DIETA ESPECIAL - TIPO A": dieta_a,
            "DIETA ESPECIAL - TIPO B": dieta_b,
        },
        "FUNDAMENTAL": {
            "DIETA ESPECIAL - TIPO A": dieta_a,
            "DIETA ESPECIAL - TIPO B": dieta_b,
        },
    }

    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    assert isinstance(dict_periodos_dietas, dict)
    assert set(["INFANTIL", "FUNDAMENTAL"]).issubset(dict_periodos_dietas.keys())

    assert dict_periodos_dietas["INFANTIL"]["MANHA"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
        "total_refeicoes_pagamento",
        "sobremesa",
        "total_sobremesas_pagamento",
    ]
    assert dict_periodos_dietas["FUNDAMENTAL"]["MANHA"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
        "total_refeicoes_pagamento",
        "sobremesa",
        "total_sobremesas_pagamento",
    ]
    assert dict_periodos_dietas["FUNDAMENTAL"]["Solicitações de Alimentação"] == [
        "kit_lanche",
        "lanche_emergencial",
    ]

    assert dict_periodos_dietas["INFANTIL"]["DIETA ESPECIAL - TIPO A"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
    ]
    assert dict_periodos_dietas["FUNDAMENTAL"]["DIETA ESPECIAL - TIPO A"] == [
        "lanche",
        "lanche_4h",
        "refeicao",
    ]
    assert dict_periodos_dietas["INFANTIL"]["DIETA ESPECIAL - TIPO B"] == [
        "lanche",
        "lanche_4h",
    ]
    assert dict_periodos_dietas["FUNDAMENTAL"]["DIETA ESPECIAL - TIPO B"] == [
        "lanche",
        "lanche_4h",
    ]


def test_generate_columns():
    periodos_dietas = {
        "MANHA": [
            "lanche",
            "lanche_4h",
            "refeicao",
            "total_refeicoes_pagamento",
            "sobremesa",
            "total_sobremesas_pagamento",
        ],
        "DIETA ESPECIAL - TIPO A": ["lanche", "lanche_4h", "refeicao"],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
    }

    dict_periodos_dietas = {
        "INFANTIL": periodos_dietas,
        "FUNDAMENTAL": {
            **periodos_dietas,
            "Solicitações de Alimentação": ["kit_lanche", "lanche_emergencial"],
        },
    }
    colunas = _generate_columns(dict_periodos_dietas)
    assert isinstance(colunas, list)
    assert len(colunas) == 24
    assert sum(1 for tupla in colunas if tupla[0] == "INFANTIL") == 11
    assert sum(1 for tupla in colunas if tupla[0] == "FUNDAMENTAL") == 11
    assert sum(1 for tupla in colunas if tupla[1] == "Solicitações de Alimentação") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "MANHA") == 12
    assert sum(1 for tupla in colunas if tupla[1] == "DIETA ESPECIAL - TIPO A") == 6
    assert sum(1 for tupla in colunas if tupla[1] == "DIETA ESPECIAL - TIPO B") == 4
    assert sum(1 for tupla in colunas if tupla[2] == "kit_lanche") == 1
    assert sum(1 for tupla in colunas if tupla[2] == "lanche_emergencial") == 1
    assert sum(1 for tupla in colunas if tupla[2] == "lanche") == 6
    assert sum(1 for tupla in colunas if tupla[2] == "lanche_4h") == 6
    assert sum(1 for tupla in colunas if tupla[2] == "refeicao") == 4
    assert sum(1 for tupla in colunas if tupla[2] == "sobremesa") == 2
    assert sum(1 for tupla in colunas if tupla[2] == "total_refeicoes_pagamento") == 2
    assert sum(1 for tupla in colunas if tupla[2] == "total_sobremesas_pagamento") == 2


def test_get_valores_tabela(relatorio_consolidado_xlsx_emebs, mock_colunas_emebs):
    linhas = get_valores_tabela([relatorio_consolidado_xlsx_emebs], mock_colunas_emebs)
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 67
    assert linhas[0] == [
        "EMEBS",
        "000329",
        "EMEBS TESTE",
        5.0,
        5.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        40.0,
        40.0,
        20.0,
        20.0,
        20.0,
        350.0,
        350.0,
        350.0,
        350,
        350.0,
        350,
        350.0,
        350.0,
        350.0,
        350,
        350.0,
        350,
        350.0,
        350.0,
        350.0,
        350,
        350.0,
        350,
        350.0,
        350.0,
        350.0,
        350,
        350.0,
        350,
        350.0,
        350.0,
        350.0,
        350,
        350,
        50.0,
        50.0,
        25.0,
        25.0,
        25.0,
    ]


def test_get_solicitacoes_ordenadas(
    solicitacao_escola_emebs,
    solicitacao_relatorio_consolidado_grupo_emebs,
):
    solicitacoes = [
        solicitacao_relatorio_consolidado_grupo_emebs,
        solicitacao_escola_emebs,
    ]
    ordenados = get_solicitacoes_ordenadas(solicitacoes)
    assert isinstance(ordenados, list)
    assert ordenados[0].escola.nome == solicitacao_escola_emebs.escola.nome
    assert (
        ordenados[1].escola.nome
        == solicitacao_relatorio_consolidado_grupo_emebs.escola.nome
    )


def test_processa_periodo_campo(relatorio_consolidado_xlsx_emebs):
    valores_iniciais = [
        relatorio_consolidado_xlsx_emebs.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_emebs.escola.codigo_eol,
        relatorio_consolidado_xlsx_emebs.escola.nome,
    ]
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    integral = _processa_periodo_campo(
        relatorio_consolidado_xlsx_emebs,
        "INFANTIL",
        "INTEGRAL",
        "lanche",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
    )

    assert isinstance(integral, list)
    assert len(integral) == 4
    assert integral == ["EMEBS", "000329", "EMEBS TESTE", 350.0]


def test_define_filtro(relatorio_consolidado_xlsx_emebs):
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
    assert "grupo__nome__in" in dieta_especial
    assert "periodo_escolar__nome__in" in dieta_especial
    assert dieta_especial["periodo_escolar__nome__in"] == periodos_escolares
    assert dieta_especial["grupo__nome__in"] == ["Programas e Projetos", "ETEC"]

    solicitacao = _define_filtro(
        "Solicitações de Alimentação", dietas_especiais, periodos_escolares
    )
    assert isinstance(solicitacao, dict)
    assert "periodo_escolar__nome" not in solicitacao
    assert "grupo__nome" in solicitacao
    assert solicitacao["grupo__nome"] == "Solicitações de Alimentação"


def test_processa_dieta_especial(relatorio_consolidado_xlsx_emebs):
    periodo = "NOITE"
    filtros = {"periodo_escolar__nome": periodo}
    campo = "refeicao"
    turma = "INFANTIL"

    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_emebs, filtros, campo, periodo, turma
    )
    assert total == "-"

    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    filtros = {
        "periodo_escolar__nome__in": periodos_escolares,
        "grupo__nome__in": ["Programas e Projetos", "ETEC"],
    }
    periodo = "DIETA ESPECIAL - TIPO A"
    total = processa_dieta_especial(
        relatorio_consolidado_xlsx_emebs, filtros, campo, periodo, turma
    )
    assert total == 20.0


def test_processa_periodo_regular(relatorio_consolidado_xlsx_emebs):
    periodo = "NOITE"
    filtros = {"periodo_escolar__nome": periodo}
    campo = "refeicao"
    turma = "INFANTIL"
    total = processa_periodo_regular(
        relatorio_consolidado_xlsx_emebs, filtros, campo, periodo, turma
    )
    assert total == "-"

    turma = "FUNDAMENTAL"
    total = processa_periodo_regular(
        relatorio_consolidado_xlsx_emebs, filtros, campo, periodo, turma
    )
    assert total == 350.0


def test_calcula_soma_medicao_alimentacao(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    campo = "refeicao"
    categoria = ["ALIMENTAÇÃO"]

    turma = ["INFANTIL"]
    manha = _calcula_soma_medicao(medicoes[1], campo, categoria, turma)
    assert manha == 350.0

    noite = _calcula_soma_medicao(medicoes[2], campo, categoria, turma)
    assert noite is None

    turma = ["FUNDAMENTAL"]
    manha = _calcula_soma_medicao(medicoes[1], campo, categoria, turma)
    assert manha == 350.0

    noite = _calcula_soma_medicao(medicoes[2], campo, categoria, turma)
    assert noite == 350.0

    categoria = ["Solicitações de Alimentação".upper()]
    turma = ["INFANTIL", "FUNDAMENTAL"]
    solicitacao = _calcula_soma_medicao(medicoes[5], "kit_lanche", categoria, turma)
    assert solicitacao == 5.0


def test_get_total_pagamento(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    campo = "total_refeicoes_pagamento"
    turma = "INFANTIL"

    integral = _get_total_pagamento(medicoes[0], campo, turma)
    assert integral == 350.0

    manha = _get_total_pagamento(medicoes[1], campo, turma)
    assert manha == 350.0

    noite = _get_total_pagamento(medicoes[2], campo, turma)
    assert noite == "-"

    tarde = _get_total_pagamento(medicoes[3], campo, turma)
    assert tarde == 350.0

    campo = "total_sobremesas_pagamento"
    turma = "INFANTIL"
    programas_projetos = _get_total_pagamento(medicoes[4], campo, turma)
    assert programas_projetos == 350.0


def test_get_total_pagamento_infantil(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    campo = "total_refeicoes_pagamento"

    integral = _total_pagamento_infantil(medicoes[0], campo, 0)
    assert integral == 350.0

    manha = _total_pagamento_infantil(medicoes[1], campo, 0)
    assert manha == 350.0

    noite = _total_pagamento_infantil(medicoes[2], campo, "-")
    assert noite == "-"

    tarde = _total_pagamento_infantil(medicoes[3], campo, 0)
    assert tarde == 350.0

    campo = "total_sobremesas_pagamento"
    programas_projetos = _total_pagamento_infantil(medicoes[4], campo, 0)
    assert programas_projetos == 350.0


def test_get_total_pagamento_fundamental(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    campo = "total_refeicoes_pagamento"

    integral = _total_pagamento_fundamental(medicoes[0], campo)
    assert integral == 350.0

    manha = _total_pagamento_fundamental(medicoes[1], campo)
    assert manha == 350.0

    noite = _total_pagamento_fundamental(medicoes[2], campo)
    assert noite == 350.0

    tarde = _total_pagamento_fundamental(medicoes[3], campo)
    assert tarde == 350.0

    campo = "total_sobremesas_pagamento"
    programas_projetos = _total_pagamento_fundamental(medicoes[4], campo)
    assert programas_projetos == 350.0


def test_insere_tabela_periodos_na_planilha(
    relatorio_consolidado_xlsx_emebs, mock_colunas_emebs, mock_linhas_emebs
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_emebs.mes}-{ relatorio_consolidado_xlsx_emebs.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")

    df = insere_tabela_periodos_na_planilha(
        aba, mock_colunas_emebs, mock_linhas_emebs, writer
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 67

    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL") == 28
    assert sum(1 for tupla in colunas_df if tupla[0] == "FUNDAMENTAL") == 34

    assert sum(1 for tupla in colunas_df if tupla[1] == "MANHA") == 12
    assert sum(1 for tupla in colunas_df if tupla[1] == "TARDE") == 12
    assert sum(1 for tupla in colunas_df if tupla[1] == "INTEGRAL") == 12
    assert sum(1 for tupla in colunas_df if tupla[1] == "NOITE") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "PROGRAMAS E PROJETOS") == 10
    assert sum(1 for tupla in colunas_df if tupla[1] == "DIETA ESPECIAL - TIPO A") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "DIETA ESPECIAL - TIPO B") == 4

    assert sum(1 for tupla in colunas_df if tupla[2] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Kit Lanche") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Lanche Emerg.") == 1

    assert sum(1 for tupla in colunas_df if tupla[2] == "Lanche") == 13
    assert sum(1 for tupla in colunas_df if tupla[2] == "Lanche 4h") == 13
    assert sum(1 for tupla in colunas_df if tupla[2] == "Refeição") == 11
    assert sum(1 for tupla in colunas_df if tupla[2] == "Sobremesa") == 7
    assert sum(1 for tupla in colunas_df if tupla[2] == "Refeições p/ Pagamento") == 9
    assert sum(1 for tupla in colunas_df if tupla[2] == "Sobremesas p/ Pagamento") == 9

    assert df.iloc[0].tolist() == [
        "EMEBS",
        "000329",
        "EMEBS TESTE",
        5.0,
        5.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        40.0,
        40.0,
        20.0,
        20.0,
        20.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        50.0,
        50.0,
        25.0,
        25.0,
        25.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        329.0,
        0.0,
        5.0,
        5.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        40.0,
        40.0,
        20.0,
        20.0,
        20.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        50.0,
        50.0,
        25.0,
        25.0,
        25.0,
    ]


def test_ajusta_layout_tabela(informacoes_excel_writer_emebs):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_emebs
    ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 17
    esperados = {
        "A3:E3",
        "F3:AG3",
        "AH3:BO3",
        "A4:E4",
        "F4:K4",
        "X4:AB4",
        "AC4:AE4",
        "AF4:AG4",
        "AH4:AM4",
        "AN4:AS4",
        "AT4:AY4",
        "AZ4:BE4",
        "BF4:BJ4",
        "BK4:BM4",
        "BN4:BO4",
        "L4:Q4",
        "R4:W4",
    }
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["F3"].value == "INFANTIL (4 a 6 anos)"
    assert sheet["F3"].fill.fgColor.rgb == "FF4A9A74"

    assert sheet["F4"].value == "MANHA"
    assert sheet["F4"].fill.fgColor.rgb == "FF198459"

    assert sheet["L4"].value == "TARDE"
    assert sheet["L4"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["R4"].value == "INTEGRAL"
    assert sheet["R4"].fill.fgColor.rgb == "FF2F80ED"

    assert sheet["X4"].value == "PROGRAMAS E PROJETOS"
    assert sheet["X4"].fill.fgColor.rgb == "FF72BC17"

    assert sheet["AC4"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["AC4"].fill.fgColor.rgb == "FF198459"

    assert sheet["AF4"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["AF4"].fill.fgColor.rgb == "FF20AA73"

    assert sheet["AH3"].value == "FUNDAMENTAL (acima de 6 anos)"
    assert sheet["AH3"].fill.fgColor.rgb == "FF2E7453"

    assert sheet["AH4"].value == "MANHA"
    assert sheet["AH4"].fill.fgColor.rgb == "FF198459"

    assert sheet["AN4"].value == "TARDE"
    assert sheet["AN4"].fill.fgColor.rgb == "FFD06D12"

    assert sheet["AT4"].value == "INTEGRAL"
    assert sheet["AT4"].fill.fgColor.rgb == "FF2F80ED"

    assert sheet["AZ4"].value == "NOITE"
    assert sheet["AZ4"].fill.fgColor.rgb == "FFB40C02"

    assert sheet["BF4"].value == "PROGRAMAS E PROJETOS"
    assert sheet["BF4"].fill.fgColor.rgb == "FF72BC17"

    assert sheet["BK4"].value == "DIETA ESPECIAL - TIPO A"
    assert sheet["BK4"].fill.fgColor.rgb == "FF198459"

    assert sheet["BN4"].value == "DIETA ESPECIAL - TIPO B"
    assert sheet["BN4"].fill.fgColor.rgb == "FF20AA73"

    workbook_openpyxl.close()
