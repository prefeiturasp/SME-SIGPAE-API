import math

import pytest

from src.medicao_inicial.services.relatorio_consolidado_recreio_cei import (
    _calcula_soma_medicao,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _processa_periodo_campo,
    _sort_and_merge,
    get_alimentacoes_por_periodo,
    get_valores_tabela,
    processa_dieta_especial,
    processa_grupos_recreio,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(solicitacao_recreio_cei, faixas_etarias_ativas):
    colunas = get_alimentacoes_por_periodo([solicitacao_recreio_cei])
    assert isinstance(colunas, list)
    assert len(colunas) == 22
    assert sum(1 for tupla in colunas if tupla[0] == "Recreio nas Férias") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "INTEGRAL") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "PARCIAL") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "TARDE") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "Colaboradores") == 6

    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[0].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[1].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[2].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[3].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[4].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[5].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[6].id) == 2
    assert sum(1 for tupla in colunas if tupla[1] == faixas_etarias_ativas[7].id) == 2

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 1
    print(colunas)


def test_get_lista_alimentacoes(solicitacao_recreio_cei, faixas_etarias_ativas):
    medicoes = solicitacao_recreio_cei.medicoes.all().order_by("grupo__nome")
    assert medicoes.count() == 2
    medicao_colaboradores = medicoes[0]
    medicao_recreio = medicoes[1]

    alimentacoes_colaboradores = _get_lista_alimentacoes(
        medicao_colaboradores, medicao_colaboradores.grupo.nome
    )
    assert isinstance(alimentacoes_colaboradores, list)
    assert len(alimentacoes_colaboradores) == 6
    assert alimentacoes_colaboradores == [
        "refeicao",
        "repeticao_refeicao",
        "repeticao_sobremesa",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    faixas_recreio = _get_lista_alimentacoes(
        medicao_recreio, medicao_recreio.grupo.nome
    )
    assert isinstance(faixas_recreio, list)
    assert len(faixas_recreio) == 8
    assert faixas_recreio == [faixa.id for faixa in faixas_etarias_ativas]


def test_get_lista_alimentacoes_dietas(solicitacao_recreio_cei, faixas_etarias_ativas):
    medicoes = solicitacao_recreio_cei.medicoes.all().order_by("grupo__nome")
    assert medicoes.count() == 2
    medicao_colaboradores = medicoes[0]
    medicao_recreio = medicoes[1]

    dieta = "DIETA ESPECIAL - TIPO A"

    dietas_colaboradores = _get_lista_alimentacoes_dietas(medicao_colaboradores, dieta)
    assert isinstance(dietas_colaboradores, list)
    assert len(dietas_colaboradores) == 0

    dietas_recreio = _get_lista_alimentacoes_dietas(medicao_recreio, dieta)
    assert isinstance(dietas_recreio, list)
    assert len(dietas_recreio) == 8
    assert dietas_recreio == [faixa.id for faixa in faixas_etarias_ativas]


def test_sort_and_merge(faixas_etarias_ativas):
    faixas = [faixa.id for faixa in faixas_etarias_ativas]

    periodos_alimentacoes = {
        "Recreio nas Férias": faixas,
        "Colaboradores": [
            "lanche",
            "lanche_4h",
            "total_refeicoes_pagamento",
            "total_sobremesas_pagamento",
        ],
    }

    dietas_alimentacoes = {
        "DIETA ESPECIAL - TIPO A": [faixas[0]],
        "DIETA ESPECIAL - TIPO B": [faixas[1], faixas[2]],
    }
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    assert isinstance(dict_periodos_dietas, dict)

    assert "Recreio nas Férias" in dict_periodos_dietas
    assert len(dict_periodos_dietas["Recreio nas Férias"]) == 8
    assert dict_periodos_dietas["Recreio nas Férias"] == faixas

    assert "Colaboradores" in dict_periodos_dietas
    assert len(dict_periodos_dietas["Colaboradores"]) == 4
    assert dict_periodos_dietas["Colaboradores"] == [
        "lanche",
        "lanche_4h",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    assert "DIETA ESPECIAL - TIPO A" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO A"]) == 1
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO A"] == [faixas[0]]

    assert "DIETA ESPECIAL - TIPO B" in dict_periodos_dietas
    assert len(dict_periodos_dietas["DIETA ESPECIAL - TIPO B"]) == 2
    assert dict_periodos_dietas["DIETA ESPECIAL - TIPO B"] == [faixas[1], faixas[2]]


def test_get_valores_tabela(solicitacao_recreio_cei, mock_colunas_recreio_cei):
    tipos_unidade = ["CEI"]
    linhas = get_valores_tabela(
        [solicitacao_recreio_cei], mock_colunas_recreio_cei, tipos_unidade
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 25
    assert linhas[0] == [
        "CEI DIRET",
        "765432",
        "CEI DIRET TESTE",
        168.0,
        168.0,
        168.0,
        168.0,
        168.0,
        168.0,
        168.0,
        168.0,
        28.0,
        28.0,
        28.0,
        28.0,
        28.0,
        28.0,
        28.0,
        28.0,
        280.0,
        280.0,
        560.0,
        280.0,
        280.0,
        560.0,
    ]


def test_processa_periodo_campo(solicitacao_recreio_cei, faixas_etarias_ativas):
    valores_iniciais = [
        solicitacao_recreio_cei.escola.tipo_unidade.iniciais,
        solicitacao_recreio_cei.escola.codigo_eol,
        solicitacao_recreio_cei.escola.nome,
    ]

    recreio = _processa_periodo_campo(
        solicitacao_recreio_cei,
        "Recreio nas Férias",
        faixas_etarias_ativas[0].id,
        valores_iniciais,
    )
    assert isinstance(recreio, list)
    assert len(recreio) == 4
    assert recreio == ["CEI DIRET", "765432", "CEI DIRET TESTE", 168.0]

    colaboradores = _processa_periodo_campo(
        solicitacao_recreio_cei,
        "Colaboradores",
        "refeicao",
        valores_iniciais,
    )
    assert isinstance(colaboradores, list)
    assert len(colaboradores) == 5
    assert colaboradores == ["CEI DIRET", "765432", "CEI DIRET TESTE", 168.0, 280.0]


def test_processa_dieta_especial(solicitacao_recreio_cei, faixas_etarias_ativas):
    filtros = {"grupo__nome": "Recreio nas Férias"}
    periodo = "DIETA ESPECIAL - TIPO A"
    faixa_etaria = faixas_etarias_ativas[2].id
    total = processa_dieta_especial(
        solicitacao_recreio_cei, filtros, faixa_etaria, periodo
    )
    assert math.isclose(total, 28.0, rel_tol=1e-9)

    filtros = {"grupo__nome": "Colaboradores"}
    periodo = "DIETA ESPECIAL - TIPO A"
    faixa_etaria = faixas_etarias_ativas[2].id
    total = processa_dieta_especial(
        solicitacao_recreio_cei, filtros, faixa_etaria, periodo
    )
    assert total == "-"


def test_processa_grupos_recreio(solicitacao_recreio_cei, faixas_etarias_ativas):
    periodo = "Recreio nas Férias"
    filtros = {"grupo__nome": "Recreio nas Férias"}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = processa_grupos_recreio(
        solicitacao_recreio_cei, filtros, faixa_etaria, periodo
    )
    assert math.isclose(total, 168.0, rel_tol=1e-9)

    periodo = "Colaboradores"
    filtros = {"grupo__nome": "Colaboradores"}
    faixa_etaria = faixas_etarias_ativas[0].id
    total = processa_grupos_recreio(
        solicitacao_recreio_cei, filtros, "total_refeicoes_pagamento", periodo
    )
    assert math.isclose(total, 560.0, rel_tol=1e-9)


def test_calcula_soma_medicao_alimentacao(
    solicitacao_recreio_cei, faixas_etarias_ativas
):
    medicoes = solicitacao_recreio_cei.medicoes.all().order_by("grupo__nome")
    medicao_colaboradores = medicoes[0]
    colaboradores = _calcula_soma_medicao(
        medicao_colaboradores, "sobremesa", None, "ALIMENTAÇÃO"
    )
    assert math.isclose(colaboradores, 280.0, rel_tol=1e-9)

    medicao_recreio = medicoes[1]
    recreio = _calcula_soma_medicao(
        medicao_recreio, "frequencia", faixas_etarias_ativas[0].id, "ALIMENTAÇÃO"
    )
    assert math.isclose(recreio, 168.0, rel_tol=1e-9)


def test_calcula_soma_medicao_dieta_especial(
    solicitacao_recreio_cei, faixas_etarias_ativas
):
    medicoes = solicitacao_recreio_cei.medicoes.all().order_by("grupo__nome")
    medicao_colaboradores = medicoes[0]
    colaboradores = _calcula_soma_medicao(
        medicao_colaboradores, "refeicao", None, "DIETA ESPECIAL - TIPO A"
    )
    assert colaboradores is None

    medicao_recreio = medicoes[1]
    recreio = _calcula_soma_medicao(
        medicao_recreio,
        "frequencia",
        faixas_etarias_ativas[0].id,
        "DIETA ESPECIAL - TIPO A",
    )
    assert math.isclose(recreio, 28.0, rel_tol=1e-9)
