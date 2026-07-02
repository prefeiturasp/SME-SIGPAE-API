import pytest

from src.medicao_inicial.services.relatorio_consolidado_recreio_cei import (
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _sort_and_merge,
    get_alimentacoes_por_periodo,
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
