from unittest.mock import MagicMock

from rest_framework import status

from sme_sigpae_api.perfil.utils import get_cargo_eol


def test_get_cargo_eol():
    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = {
        "cargos": [
            {"descricaoCargo": "Professor da Rede Municipal"},
            {"descricaoCargo": "Nutricionista da Rede Municipal"},
        ]
    }
    cargo = get_cargo_eol(mock_response)
    assert cargo == "Professor da Rede Municipal"


def test_get_cargo_eol_sem_cargos():
    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = {"cargos": []}
    cargo = get_cargo_eol(mock_response)
    assert cargo is None


def test_get_cargo_eol_invalid_status():
    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_400_BAD_REQUEST
    mock_response.json.return_value = {"message": "Erro"}
    cargo = get_cargo_eol(mock_response)
    assert cargo is None
