import pytest

pytestmark = pytest.mark.django_db


def test_motivo_alteracao_cardapio(motivo_alteracao_cardapio):
    assert motivo_alteracao_cardapio.nome is not None
    assert motivo_alteracao_cardapio.__str__() == "Aniversariantes do mês"


def test_alteracao_cardapio(alteracao_cardapio):
    assert alteracao_cardapio.data_inicial is not None
    assert alteracao_cardapio.data_final is not None
    assert alteracao_cardapio.observacao == "teste"
    assert alteracao_cardapio.status is not None
    assert (
        alteracao_cardapio.__str__()
        == "Alteração de cardápio de: 2019-10-04 para 2019-12-31"
    )


def test_substituicoes_alimentacao_periodo(substituicoes_alimentacao_periodo):
    assert substituicoes_alimentacao_periodo.alteracao_cardapio is not None
    assert (
        substituicoes_alimentacao_periodo.alteracao_cardapio.substituicoes is not None
    )
