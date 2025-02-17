from unittest.mock import MagicMock

import pytest

from sme_sigpae_api.dados_comuns.permissions import (
    PermissaoParaCriarUsuarioComCoresso,
    UsuarioAdministradorContratos,
)

pytestmark = pytest.mark.django_db


def test_usuario_dicae_criar_usuario(user_admin_dicae):
    request = MagicMock()
    request.user = user_admin_dicae
    permissao = PermissaoParaCriarUsuarioComCoresso()
    assert permissao.has_permission(request, None)


def test_usuario_com_permissao_administrador_contrato(user_admin_dicae):
    request = MagicMock()
    request.user = user_admin_dicae
    permissao = UsuarioAdministradorContratos()
    assert permissao.has_permission(request, None)


def test_usuario_sem_permissao_administrador_contrato(
    usuario_teste_notificacao_autenticado,
):
    usuario, _ = usuario_teste_notificacao_autenticado
    request = MagicMock()
    request.user = usuario
    permissao = UsuarioAdministradorContratos()
    assert not permissao.has_permission(request, None)
