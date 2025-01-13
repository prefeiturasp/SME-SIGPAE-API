import pytest
from sme_sigpae_api.cardapio.utils import converter_data

def test_converter_data_valida():
    formato = "2025-01-13"
    resultado_esperado = "13/01/2025"
    assert converter_data(formato) == resultado_esperado

def test_converter_data_invalida():
    formato = "13-01-2025"
    with pytest.raises(ValueError, match=f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD."):
        converter_data(formato)

def test_converter_data_vazia():
    formato = ""
    with pytest.raises(ValueError, match=f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD."):
        converter_data(formato)

def test_converter_data_caracteres_invalidos():
    formato = "abcd-ef-gh"
    with pytest.raises(ValueError, match=f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD."):
        converter_data(formato)
