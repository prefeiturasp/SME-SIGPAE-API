import pytest

from sme_sigpae_api.medicao_inicial.services.relatorio_consolidado_emebs import (
    _get_categorias_dietas,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _get_nome_periodo,
    _obter_dietas_especiais,
    _update_dietas_alimentacoes,
    _update_periodos_alimentacoes,
    get_alimentacoes_por_periodo,
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


def test_get_nome_periodo(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    assert medicoes.count() == 6

    integral = _get_nome_periodo(medicoes[0])
    assert isinstance(integral, str)
    assert integral == "INTEGRAL"

    manha = _get_nome_periodo(medicoes[1])
    assert isinstance(manha, str)
    assert manha == "MANHA"

    noite = _get_nome_periodo(medicoes[2])
    assert isinstance(noite, str)
    assert noite == "NOITE"

    tarde = _get_nome_periodo(medicoes[3])
    assert isinstance(tarde, str)
    assert tarde == "TARDE"

    programas_projetos = _get_nome_periodo(medicoes[4])
    assert isinstance(programas_projetos, str)
    assert programas_projetos == "Programas e Projetos"

    solicitacao = _get_nome_periodo(medicoes[5])
    assert isinstance(solicitacao, str)
    assert solicitacao == "Solicitações de Alimentação"


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
