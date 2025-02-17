from unittest.mock import MagicMock, patch

import pytest
from rest_framework import exceptions
from rest_framework.authtoken.models import Token

from sme_sigpae_api.logistica.api.soup.token_auth import TokenAuthentication

pytestmark = pytest.mark.django_db


def test_get_model(token_valido):
    usuario, token, model = token_valido
    token_auth = TokenAuthentication()
    token_auth.model = model
    token_auth.keyword = "Auth"
    assert token_auth.get_model() == model
    assert token_auth.keyword == "Auth"


def test_get_model_default():
    token_auth = TokenAuthentication()
    assert token_auth.get_model() == Token
    assert token_auth.keyword == "Token"


def test_authenticate_token_valido(token_valido):
    usuario, token, model = token_valido
    token_auth = TokenAuthentication()
    user, token_ok = token_auth.authenticate(model)
    assert user == usuario
    assert token_ok == token


def test_authenticate_falha_sem_modelo():
    with pytest.raises(
        exceptions.AuthenticationFailed,
        match="Token inválido. Não foi enviado informações de credenciais.",
    ):
        TokenAuthentication().authenticate(None)


def test_authenticate_falha_no_strtoken(token_valido):
    usuario, token, model = token_valido
    with pytest.raises(
        exceptions.AuthenticationFailed,
        match="Falha na autenticação. StrToken não foi informado.",
    ):
        TokenAuthentication().authenticate(usuario)


def test_authenticate_credentials(token_valido):
    usuario, token, model = token_valido
    token_auth = TokenAuthentication()
    user, token_ok = token_auth.authenticate_credentials(model.StrToken)
    assert user == usuario
    assert token_ok == token


def test_authenticate_credentials_invalida():
    with pytest.raises(exceptions.AuthenticationFailed, match="Token inválido."):
        TokenAuthentication().authenticate_credentials(122)


def test_authenticate_credentials_usuario_inativo(token_valido):
    usuario, token, model = token_valido
    usuario.is_active = False
    usuario.save()

    with pytest.raises(
        exceptions.AuthenticationFailed, match="Usuário inativo ou deletado."
    ):
        TokenAuthentication().authenticate_credentials(model.StrToken)
