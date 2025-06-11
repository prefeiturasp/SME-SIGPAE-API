import pytest

from sme_sigpae_api.medicao_inicial.services.utils import (
    get_nome_periodo,
    update_periodos_alimentacoes,
)

pytestmark = pytest.mark.django_db


def test_get_nome_periodo_emei_emef(
    medicao_grupo_solicitacao_alimentacao, medicao_grupo_alimentacao
):
    periodo = get_nome_periodo(medicao_grupo_solicitacao_alimentacao[0])
    assert isinstance(periodo, str)
    assert periodo == "Solicitações de Alimentação"

    periodo_manha = get_nome_periodo(medicao_grupo_alimentacao[0])
    assert isinstance(periodo_manha, str)
    assert periodo_manha == "MANHA"


def test_get_nome_periodo_cei(relatorio_consolidado_xlsx_cei):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    integral = get_nome_periodo(medicoes[0])
    assert isinstance(integral, str)
    assert integral == "INTEGRAL"

    manha = get_nome_periodo(medicoes[1])
    assert isinstance(manha, str)
    assert manha == "MANHA"

    parcial = get_nome_periodo(medicoes[2])
    assert isinstance(parcial, str)
    assert parcial == "PARCIAL"

    tarde = get_nome_periodo(medicoes[3])
    assert isinstance(tarde, str)
    assert tarde == "TARDE"


def test_get_nome_periodo_cemei(relatorio_consolidado_xlsx_cemei):
    medicoes = relatorio_consolidado_xlsx_cemei.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    assert medicoes.count() == 6

    integral_cei = get_nome_periodo(medicoes[0])
    assert isinstance(integral_cei, str)
    assert integral_cei == "INTEGRAL"

    parcial = get_nome_periodo(medicoes[1])
    assert isinstance(parcial, str)
    assert parcial == "PARCIAL"

    integral = get_nome_periodo(medicoes[2])
    assert isinstance(integral, str)
    assert integral == "Infantil INTEGRAL"

    manha = get_nome_periodo(medicoes[3])
    assert isinstance(manha, str)
    assert manha == "Infantil MANHA"

    tarde = get_nome_periodo(medicoes[4])
    assert isinstance(tarde, str)
    assert tarde == "Infantil TARDE"

    solicitacao = get_nome_periodo(medicoes[5])
    assert isinstance(solicitacao, str)
    assert solicitacao == "Solicitações de Alimentação"


def test_get_nome_periodo_emebs(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    assert medicoes.count() == 6

    integral = get_nome_periodo(medicoes[0])
    assert isinstance(integral, str)
    assert integral == "INTEGRAL"

    manha = get_nome_periodo(medicoes[1])
    assert isinstance(manha, str)
    assert manha == "MANHA"

    noite = get_nome_periodo(medicoes[2])
    assert isinstance(noite, str)
    assert noite == "NOITE"

    tarde = get_nome_periodo(medicoes[3])
    assert isinstance(tarde, str)
    assert tarde == "TARDE"

    programas_projetos = get_nome_periodo(medicoes[4])
    assert isinstance(programas_projetos, str)
    assert programas_projetos == "Programas e Projetos"

    solicitacao = get_nome_periodo(medicoes[5])
    assert isinstance(solicitacao, str)
    assert solicitacao == "Solicitações de Alimentação"


def test_update_periodos_alimentacoes(faixas_etarias_ativas):
    lista_faixas = [faixa.id for faixa in faixas_etarias_ativas]
    lista_alimentacoes = [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]
    lista_alimentacoes_solicitacao = ["kit_lanche", "lanche_emergencial"]
    periodos_alimentacoes = {}

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "INTEGRAL", lista_faixas
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "INTEGRAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["INTEGRAL"] == lista_faixas

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "PARCIAL", lista_faixas
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "PARCIAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["PARCIAL"] == lista_faixas

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "Infantil INTEGRAL", lista_alimentacoes
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Infantil INTEGRAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["Infantil INTEGRAL"] == lista_alimentacoes

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "Infantil MANHA", lista_alimentacoes
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Infantil MANHA" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["Infantil MANHA"] == lista_alimentacoes

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "Infantil TARDE", lista_alimentacoes
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Infantil TARDE" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["Infantil TARDE"] == lista_alimentacoes

    periodos_alimentacoes = update_periodos_alimentacoes(
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
    assert set(
        [
            "INTEGRAL",
            "PARCIAL",
            "Infantil INTEGRAL",
            "Infantil MANHA",
            "Infantil TARDE",
            "Solicitações de Alimentação",
        ]
    ).issubset(periodos_alimentacoes.keys())
