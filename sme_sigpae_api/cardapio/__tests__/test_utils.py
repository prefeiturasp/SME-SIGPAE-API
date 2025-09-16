import pytest

from sme_sigpae_api.cardapio.utils import converter_data, ordem_periodos

pytestmark = pytest.mark.django_db


def test_converter_data_valida():
    formato = "2025-01-13"
    resultado_esperado = "13/01/2025"
    assert converter_data(formato) == resultado_esperado


def test_converter_data_invalida():
    formato = "13-01-2025"
    with pytest.raises(
        ValueError, match=f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD."
    ):
        converter_data(formato)


def test_converter_data_vazia():
    formato = ""
    with pytest.raises(
        ValueError, match=f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD."
    ):
        converter_data(formato)


def test_converter_data_caracteres_invalidos():
    formato = "abcd-ef-gh"
    with pytest.raises(
        ValueError, match=f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD."
    ):
        converter_data(formato)


def test_ordem_periodos_emef(escola):
    esperado = {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3, "NOITE": 4}
    periodos = ordem_periodos(escola)
    assert periodos == esperado


def test_ordem_periodos_emei(escola_emei):
    esperado = {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3}
    periodos = ordem_periodos(escola_emei)
    assert periodos == esperado


def test_ordem_periodos_ceu_gestao(escola_ceu_gestao):
    esperado = {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3, "NOITE": 4}
    periodos = ordem_periodos(escola_ceu_gestao)
    assert periodos == esperado


def test_ordem_periodos_cemei(escola_cemei):
    esperado = {
        "CEI DIRET": {"INTEGRAL": 1, "PARCIAL": 2},
        "EMEI": {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3},
    }
    periodos = ordem_periodos(escola_cemei)
    assert periodos == esperado


def test_ordem_periodos_cei(escola_cei):
    esperado = {"INTEGRAL": 1, "PARCIAL": 2, "MANHA": 3, "TARDE": 4}
    periodos = ordem_periodos(escola_cei)
    assert periodos == esperado


def test_ordem_periodos_cieja(escola_cieja):
    esperado = {
        "MANHA": 1,
        "INTERMEDIARIO": 2,
        "TARDE": 3,
        "VESPERTINO": 4,
        "NOITE": 5,
    }
    periodos = ordem_periodos(escola_cieja)
    assert periodos == esperado


def test_ordem_periodos_emebs(escola_emebs):
    esperado = {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3, "VESPERTINO": 4, "NOITE": 5}
    periodos = ordem_periodos(escola_emebs)
    assert periodos == esperado


def test_ordem_periodos_cca(escola_cca):
    esperado = {
        "MANHA": 1,
        "INTERMEDIARIO": 2,
        "TARDE": 3,
        "VESPERTINO": 4,
        "INTEGRAL": 5,
        "NOITE": 6,
    }
    periodos = ordem_periodos(escola_cca)
    assert periodos == esperado
