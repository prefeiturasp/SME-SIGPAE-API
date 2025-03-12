import pytest
from rest_framework.exceptions import ValidationError

from ..api.validators import (
    escola_quantidade_deve_ter_0_kit,
    escola_quantidade_deve_ter_1_ou_mais_kits,
    escola_quantidade_deve_ter_mesmo_tempo_passeio,
    nao_deve_ter_mais_solicitacoes_que_alunos,
    solicitacao_deve_ter_0_kit,
    solicitacao_deve_ter_1_ou_mais_kits,
    valida_quantidade_kits_tempo_passeio,
    valida_tempo_passeio_lista_igual,
    valida_tempo_passeio_lista_nao_igual,
)

pytestmark = pytest.mark.django_db


def test_valida_tempo_passeio_lista_nao_igual():
    assert valida_tempo_passeio_lista_nao_igual(None) is True


def test_valida_tempo_passeio_lista_nao_igual_exception():
    with pytest.raises(ValidationError, match="tempo de passeio deve ser null"):
        valida_tempo_passeio_lista_nao_igual(1)


def test_valida_tempo_passeio_lista_igual(horarios_passeio):
    tempo, esperado = horarios_passeio
    assert valida_tempo_passeio_lista_igual(tempo) is esperado


def test_horarios_passeio_invalido(horarios_passeio_invalido):
    tempo, esperado = horarios_passeio_invalido
    with pytest.raises(ValidationError, match=esperado):
        valida_tempo_passeio_lista_igual(tempo)


def test_escola_quantidade_deve_ter_mesmo_tempo_passeio():
    escola_quantidade_mock = {"tempo_passeio": 3}
    solicitacao_kit_lanche_mock = {"tempo_passeio": 3}
    assert (
        escola_quantidade_deve_ter_mesmo_tempo_passeio(
            escola_quantidade_mock, solicitacao_kit_lanche_mock, 3
        )
        is True
    )


def test_escola_quantidade_deve_ter_mesmo_tempo_passeio_exception():
    escola_quantidade_mock = {"tempo_passeio": 4}
    solicitacao_kit_lanche_mock = {"tempo_passeio": 3}
    esperado = "escola_quantidade indice #3 diverge do tempo_passeio de solicitacao_kit_lanche."
    with pytest.raises(ValidationError, match=esperado):
        escola_quantidade_deve_ter_mesmo_tempo_passeio(
            escola_quantidade=escola_quantidade_mock,
            solicitacao_kit_lanche=solicitacao_kit_lanche_mock,
            indice=3,
        )


def test_escola_quantidade_deve_ter_1_ou_mais_kits():
    assert escola_quantidade_deve_ter_1_ou_mais_kits(3, 2) is True


def test_escola_quantidade_deve_ter_1_ou_mais_kits_exception():
    esperado = "escola_quantidade indice # 2 deve ter 1 ou mais kits"
    with pytest.raises(ValidationError, match=esperado):
        escola_quantidade_deve_ter_1_ou_mais_kits(0, 2)


def test_escola_quantidade_deve_ter_0_kit():
    assert escola_quantidade_deve_ter_0_kit(0, 3) is True


def test_escola_quantidade_deve_ter_0_kit_exception():
    esperado = "escola_quantidade indice # 3 deve ter 0 kit"
    with pytest.raises(ValidationError, match=esperado):
        escola_quantidade_deve_ter_0_kit(1, 3)


def test_solicitacao_deve_ter_0_kit():
    assert solicitacao_deve_ter_0_kit(0) is True


def test_solicitacao_deve_ter_0_kit_exception():
    esperado = 'Em "solicitacao_kit_lanche", quando lista_kit_lanche NÃO é igual, deve ter 0 kit'
    with pytest.raises(ValidationError, match=esperado):
        solicitacao_deve_ter_0_kit(1)


def test_solicitacao_deve_ter_1_ou_mais_kits():
    assert solicitacao_deve_ter_1_ou_mais_kits(numero_kits=3) is True


def test_solicitacao_deve_ter_1_ou_mais_kits_exception():
    esperado = 'Quando lista_kit_lanche_igual é Verdadeiro, "solicitacao_kit_lanche", deve ter de 1 a 3 kits'
    with pytest.raises(ValidationError, match=esperado):
        solicitacao_deve_ter_1_ou_mais_kits(numero_kits=0)


def test_valida_quantidade_kits_tempo_passeio(tempo_kits):
    tempo, qtd_kits = tempo_kits
    assert valida_quantidade_kits_tempo_passeio(tempo, qtd_kits) is True


def test_nao_deve_ter_mais_solicitacoes_que_alunos(solicitacao_avulsa):
    assert nao_deve_ter_mais_solicitacoes_que_alunos(solicitacao_avulsa) is None


def test_nao_deve_ter_mais_solicitacoes_que_alunos_com_erro(solicitacao_na_mesma_data):
    esperado = "A quantidade de alunos informados para o evento excede a quantidade de alunos matriculados na escola. Na data 01-01-2000 já tem pedidos para 300 alunos"
    with pytest.raises(ValidationError, match=esperado):
        nao_deve_ter_mais_solicitacoes_que_alunos(solicitacao_na_mesma_data)


def test_nao_deve_ter_mais_solicitacoes_que_alunos_escola_cmct(solicitacao_cmct):
    assert nao_deve_ter_mais_solicitacoes_que_alunos(solicitacao_cmct) is None
