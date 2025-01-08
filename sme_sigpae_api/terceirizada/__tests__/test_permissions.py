from unittest.mock import MagicMock

import pytest

from sme_sigpae_api.dados_comuns.constants import ADMINISTRADOR_EMPRESA
from sme_sigpae_api.terceirizada.api.permissions import (
    PodeAlterarTerceirizadasPermission,
    PodeCriarAdministradoresDaTerceirizada,
)


@pytest.mark.django_db
def test_pode_alterar_terceirizadas_permission(mock_request):
    obj = MagicMock()
    permission = PodeAlterarTerceirizadasPermission()
    assert permission.has_permission(mock_request, None) is True
    assert permission.has_object_permission(mock_request, None, obj) is True


@pytest.mark.django_db
def test_usuario_nao_autenticado(mock_request):
    permission = PodeCriarAdministradoresDaTerceirizada()
    mock_request.user.is_anonymous = True
    assert permission.has_permission(mock_request, None) is False


@pytest.mark.django_db
def test_usuario_com_perfil_valido(mock_request, mock_vinculo_atual):
    """Testa que um usuário com perfil válido tem permissão."""
    permission = PodeCriarAdministradoresDaTerceirizada()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual = mock_vinculo_atual
    mock_vinculo_atual.perfil.nome = ADMINISTRADOR_EMPRESA
    assert permission.has_permission(mock_request, None) is True


@pytest.mark.django_db
def test_usuario_com_perfil_invalido(mock_request, mock_vinculo_atual):
    """Testa que um usuário com perfil inválido não tem permissão."""
    permission = PodeCriarAdministradoresDaTerceirizada()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual = mock_vinculo_atual
    mock_vinculo_atual.perfil.nome = "Perfil Inválido"
    assert permission.has_permission(mock_request, None) is False


@pytest.mark.django_db
def test_has_object_permission_vinculo_valido(mock_request):
    """Testa que `has_object_permission` retorna True para vínculo válido."""
    permission = PodeCriarAdministradoresDaTerceirizada()
    mock_request.user.vinculo_atual.instituicao = "Instituicao_A"
    obj = "Instituicao_A"
    assert permission.has_object_permission(mock_request, None, obj) is True


@pytest.mark.django_db
def test_has_object_permission_vinculo_invalido(mock_request):
    """Testa que `has_object_permission` retorna False para vínculo inválido."""
    permission = PodeCriarAdministradoresDaTerceirizada()
    mock_request.user.vinculo_atual.instituicao = "Instituicao_A"
    obj = "Instituicao_B"
    assert permission.has_object_permission(mock_request, None, obj) is False
