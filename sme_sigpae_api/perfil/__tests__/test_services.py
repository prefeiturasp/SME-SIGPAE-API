from unittest.mock import MagicMock, Mock, patch

import pytest
from requests import Response
from requests.exceptions import ConnectTimeout, ReadTimeout
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import (
    DJANGO_ADMIN_PASSWORD,
    DJANGO_AUTENTICA_CORESSO_API_URL,
)
from sme_sigpae_api.eol_servico.utils import EOLException
from sme_sigpae_api.perfil.__tests__.conftest import (
    mocked_response_autentica_coresso_diretor,
    mocked_response_autentica_coresso_diretor_login_errado,
)
from sme_sigpae_api.perfil.services.autenticacao_service import AutenticacaoService
from sme_sigpae_api.perfil.services.usuario_coresso_service import EOLUsuarioCoreSSO
from utility.carga_dados.perfil.importa_dados import (
    ProcessaPlanilhaUsuarioServidorCoreSSOException,
)


@pytest.mark.django_db
def test_cria_ou_atualiza_usuario_core_sso_criar_usuario():
    usuario_core_sso = EOLUsuarioCoreSSO()

    dados_usuario = Mock(
        nome="Jose Testando", email="teste@teste.com", perfil="DIRETOR"
    )
    login = "123456"
    eh_servidor = "S"
    existe_core_sso = False

    with patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.cria_usuario_core_sso"
    ) as mock_cria_usuario, patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.usuario_core_sso_or_none",
        return_value=None,
    ), patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.atribuir_perfil_coresso"
    ) as mock_atribuir_perfil:
        usuario_core_sso.cria_ou_atualiza_usuario_core_sso(
            dados_usuario, login, eh_servidor, existe_core_sso
        )

        mock_cria_usuario.assert_called_once_with(
            login=login,
            nome=dados_usuario.nome,
            email=dados_usuario.email,
            e_servidor=True,
        )
        mock_atribuir_perfil.assert_called_once_with(
            login=login, perfil=dados_usuario.perfil
        )


@pytest.mark.django_db
def test_cria_ou_atualiza_usuario_core_sso_atualizar_email():
    usuario_core_sso = EOLUsuarioCoreSSO()

    dados_usuario = Mock(
        nome="Jose Testando", email="novoemail@teste.com", perfil="DIRETOR"
    )
    login = "123456"
    eh_servidor = "S"
    existe_core_sso = True

    info_user_core = {"email": "teste@teste.com"}

    with patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.usuario_core_sso_or_none",
        return_value=info_user_core,
    ), patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.redefine_email"
    ) as mock_redefine_email, patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.atribuir_perfil_coresso"
    ) as mock_atribuir_perfil:
        usuario_core_sso.cria_ou_atualiza_usuario_core_sso(
            dados_usuario, login, eh_servidor, existe_core_sso
        )

        mock_redefine_email.assert_called_once_with(login, dados_usuario.email)
        mock_atribuir_perfil.assert_called_once_with(
            login=login, perfil=dados_usuario.perfil
        )


@pytest.mark.django_db
def test_cria_ou_atualiza_usuario_core_sso_exceptions():
    usuario_core_sso = EOLUsuarioCoreSSO()

    dados_usuario = Mock(
        nome="Jose Testando", email="teste@teste.com", perfil="DIRETOR"
    )
    login = "123456"
    eh_servidor = "S"
    existe_core_sso = False

    with patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.cria_usuario_core_sso",
        side_effect=EOLException("Erro"),
    ):
        with pytest.raises(ProcessaPlanilhaUsuarioServidorCoreSSOException):
            usuario_core_sso.cria_ou_atualiza_usuario_core_sso(
                dados_usuario, login, eh_servidor, existe_core_sso
            )

    with patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.cria_usuario_core_sso",
        side_effect=ReadTimeout,
    ):
        with pytest.raises(ProcessaPlanilhaUsuarioServidorCoreSSOException):
            usuario_core_sso.cria_ou_atualiza_usuario_core_sso(
                dados_usuario, login, eh_servidor, existe_core_sso
            )

    with patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.cria_usuario_core_sso",
        side_effect=ConnectTimeout,
    ):
        with pytest.raises(ProcessaPlanilhaUsuarioServidorCoreSSOException):
            usuario_core_sso.cria_ou_atualiza_usuario_core_sso(
                dados_usuario, login, eh_servidor, existe_core_sso
            )


@pytest.mark.django_db
def test_autentica_sucesso():
    dados_usuario = mocked_response_autentica_coresso_diretor()
    login = dados_usuario["login"]
    senha = DJANGO_ADMIN_PASSWORD

    mock_response = Mock(spec=Response)
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = dados_usuario

    with patch("requests.post", return_value=mock_response) as mock_post:
        response = AutenticacaoService.autentica(login, senha)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == dados_usuario
        mock_post.assert_called_once_with(
            f"{DJANGO_AUTENTICA_CORESSO_API_URL}/autenticacao/",
            headers=AutenticacaoService.DEFAULT_HEADERS,
            timeout=AutenticacaoService.DEFAULT_TIMEOUT,
            json={"login": login, "senha": senha},
        )


@pytest.mark.django_db
def test_autentica_falha():
    dados_usuario = mocked_response_autentica_coresso_diretor_login_errado()
    login = dados_usuario["login"]
    senha = DJANGO_ADMIN_PASSWORD

    mock_response = Mock(spec=Response)
    mock_response.status_code = status.HTTP_401_UNAUTHORIZED
    mock_response.json.return_value = {"detail": "Usuário não encontrado."}

    with patch("requests.post", return_value=mock_response):
        response = AutenticacaoService.autentica(login, senha)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {"detail": "Usuário não encontrado."}


@pytest.mark.django_db
def test_get_perfis_do_sistema():
    resposta_corresso = [{"id": 1, "nome": "Diretor"}, {"id": 2, "nome": "Professor"}]
    mock_response = Mock(spec=Response)
    mock_response.status_code = status.HTTP_200_OK
    mock_response.json.return_value = resposta_corresso

    with patch("requests.get", return_value=mock_response) as mock_get:
        response = AutenticacaoService.get_perfis_do_sistema()

        assert response == resposta_corresso
        mock_get.assert_called_once_with(
            f"{DJANGO_AUTENTICA_CORESSO_API_URL}/perfis/",
            headers=AutenticacaoService.DEFAULT_HEADERS,
            timeout=AutenticacaoService.DEFAULT_TIMEOUT,
        )


@pytest.mark.django_db
def test_autentica_exception():
    dados_usuario = mocked_response_autentica_coresso_diretor_login_errado()
    login = dados_usuario["login"]
    senha = DJANGO_ADMIN_PASSWORD

    with patch("requests.post", side_effect=Exception("Erro de conexão")) as mock_post:
        with pytest.raises(Exception, match="Erro de conexão"):
            AutenticacaoService.autentica(login, senha)

        mock_post.assert_called_once_with(
            f"{DJANGO_AUTENTICA_CORESSO_API_URL}/autenticacao/",
            headers=AutenticacaoService.DEFAULT_HEADERS,
            timeout=AutenticacaoService.DEFAULT_TIMEOUT,
            json={"login": login, "senha": senha},
        )


@pytest.mark.django_db
def test_get_perfis_do_sistema_exception():
    with patch("requests.get", side_effect=Exception("Erro de conexão")) as mock_post:
        with pytest.raises(Exception, match="Erro de conexão"):
            AutenticacaoService.get_perfis_do_sistema()

        mock_post.assert_called_once_with(
            f"{DJANGO_AUTENTICA_CORESSO_API_URL}/perfis/",
            headers=AutenticacaoService.DEFAULT_HEADERS,
            timeout=AutenticacaoService.DEFAULT_TIMEOUT,
        )
