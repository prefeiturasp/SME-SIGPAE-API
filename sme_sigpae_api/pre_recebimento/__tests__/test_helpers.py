import pytest

from sme_sigpae_api.pre_recebimento.api.helpers import (
    formata_cnpj_ficha_tecnica,
    formata_telefone_ficha_tecnica,
)


@pytest.mark.parametrize(
    "cnpj, cnpj_formatado",
    [
        ("12345678000195", "12.345.678/0001-95"),
        ("12.345.678/0001-95", "12.345.678/0001-95"),
        ("1234567800019", "1234567800019"),
        ("", ""),
        (None, ""),
        ("00000000000000", "00.000.000/0000-00"),
        ("12.345.678/0001-9", "1234567800019"),
        ("12a345b678c0001d95", "12.345.678/0001-95"),
    ],
)
def test_formata_cnpj_ficha_tecnica(cnpj, cnpj_formatado):
    assert formata_cnpj_ficha_tecnica(cnpj) == cnpj_formatado


@pytest.mark.parametrize(
    "telefone, telefone_formatado",
    [
        ("11987654321", "11 98765 4321"),
        ("11 98765-4321", "11 98765 4321"),
        ("1198765432", "11 9876 5432"),
        ("(11) 98765-4321", "11 98765 4321"),
        ("(11)987654321", "11 98765 4321"),
        ("(11) 9876-5432", "11 9876 5432"),
        ("119876543", "119876543"),
        ("", ""),
        (None, ""),
        ("abc11987654321xyz", "11 98765 4321"),
        ("1234567890", "12 3456 7890"),
        ("12345678901", "12 34567 8901"),
        ("12345", "12345"),
    ],
)
def test_formata_telefone_ficha_tecnica(telefone, telefone_formatado):
    assert formata_telefone_ficha_tecnica(telefone) == telefone_formatado
