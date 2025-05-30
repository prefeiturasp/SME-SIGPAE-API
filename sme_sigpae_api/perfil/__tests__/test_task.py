from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from sme_sigpae_api.eol_servico.utils import EOLException
from sme_sigpae_api.perfil.tasks import (
    busca_cargo_de_usuario,
    compara_e_atualiza_dados_do_eol,
    get_usuario,
    processa_planilha_usuario_externo_coresso_async,
    processa_planilha_usuario_servidor_coresso_async,
    processa_planilha_usuario_ue_parceira_coresso_async,
)

pytestmark = pytest.mark.django_db


def test_get_usuario(usuario_2):
    usuario = get_usuario(usuario_2.registro_funcional)
    assert usuario == usuario_2


def test_compara_e_atualiza_dados_do_eol(usuario_dilog_abastecimento):
    cargo = "DILOG SUPERVISOR"
    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = {
        "cargos": [
            {"descricaoCargo": cargo},
        ]
    }
    compara_e_atualiza_dados_do_eol(mock_response, usuario_dilog_abastecimento)
    assert usuario_dilog_abastecimento.cargo == cargo


def test_compara_e_atualiza_dados_do_eol_cargo_nao_encontrado(
    usuario_dilog_abastecimento,
):
    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = {"cargos": []}
    cargo = compara_e_atualiza_dados_do_eol(mock_response, usuario_dilog_abastecimento)
    assert cargo is None


@patch("sme_sigpae_api.perfil.tasks.compara_e_atualiza_dados_do_eol")
@patch("sme_sigpae_api.eol_servico.utils.EOLServicoSGP.get_dados_usuario")
@patch("sme_sigpae_api.perfil.tasks.get_usuario")
def test_busca_cargo_de_usuario_com_sucesso(
    mock_get_usuario,
    mock_get_dados_usuario,
    mock_compara_e_atualiza_dados_do_eol,
    usuario_dilog_abastecimento,
):
    mock_get_usuario.return_value = usuario_dilog_abastecimento

    mock_response = MagicMock()
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = {
        "cargos": [
            {"descricaoCargo": "cargo"},
        ]
    }
    mock_get_dados_usuario.return_value = mock_response

    busca_cargo_de_usuario(usuario_dilog_abastecimento.registro_funcional)

    mock_get_usuario.assert_called_once_with(
        usuario_dilog_abastecimento.registro_funcional
    )
    mock_get_dados_usuario.assert_called_once_with(
        usuario_dilog_abastecimento.registro_funcional
    )
    mock_compara_e_atualiza_dados_do_eol.assert_called_once_with(
        mock_response, usuario_dilog_abastecimento
    )


@patch("sme_sigpae_api.perfil.tasks.logger")
@patch("sme_sigpae_api.eol_servico.utils.EOLServicoSGP.get_dados_usuario")
@patch("sme_sigpae_api.perfil.tasks.get_usuario")
def test_busca_cargo_de_usuario_lanca_eol_exception(
    mock_get_usuario,
    mock_get_dados_usuario,
    mock_logger,
):
    registro_funcional = "123456"
    usuario = MagicMock()
    mock_get_usuario.return_value = usuario

    mock_get_dados_usuario.side_effect = EOLException("Erro de integração")

    busca_cargo_de_usuario(registro_funcional)

    mock_get_usuario.assert_called_once_with(registro_funcional)
    mock_get_dados_usuario.assert_called_once_with(registro_funcional)
    mock_logger.debug.assert_called_once_with(
        f"Usuario com rf {registro_funcional} não esta cadastro no EOL"
    )


def test_processa_planilha_usuario_externo_coresso_async(
    usuario_dilog_abastecimento, planilha_usuario_externo
):
    resposta = processa_planilha_usuario_externo_coresso_async(
        usuario_dilog_abastecimento, planilha_usuario_externo.uuid
    )
    assert resposta is None


def test_processa_planilha_usuario_servidor_coresso_async(
    usuario_dilog_abastecimento, planilha_usuario_externo
):
    resposta = processa_planilha_usuario_servidor_coresso_async(
        usuario_dilog_abastecimento, planilha_usuario_externo.uuid
    )
    assert resposta is None


def test_processa_planilha_usuario_ue_parceira_coresso_async(
    usuario_dilog_abastecimento, planilha_usuario_externo
):
    resposta = processa_planilha_usuario_ue_parceira_coresso_async(
        usuario_dilog_abastecimento, planilha_usuario_externo.uuid
    )
    assert resposta is None
