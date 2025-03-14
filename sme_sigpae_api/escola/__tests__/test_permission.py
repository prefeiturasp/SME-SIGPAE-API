import pytest

from sme_sigpae_api.dados_comuns.constants import (
    COGESTOR_DRE,
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    DIRETOR_UE,
)
from sme_sigpae_api.escola.api.permissions import (
    PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada,
    PodeCriarAdministradoresDaCODAEGestaoDietaEspecial,
    PodeCriarAdministradoresDaCODAEGestaoProdutos,
    PodeCriarAdministradoresDaCODAESupervisaoNutricao,
    PodeCriarAdministradoresDaDiretoriaRegional,
    PodeCriarAdministradoresDaEscola,
    PodeVerEditarFotoAlunoNoSGP,
)

pytestmark = pytest.mark.django_db


# PodeCriarAdministradoresDaEscola
def test_pode_criar_administradores_escola_has_permission_retorna_true(
    mock_request, usuario_diretor_escola
):
    permission = PodeCriarAdministradoresDaEscola()
    mock_request.user = usuario_diretor_escola[0]
    assert permission.has_permission(mock_request, None) is True


def test_pode_criar_administradores_escola_has_permission_retorna_false(
    mock_request, usuario_coordenador_codae
):
    permission = PodeCriarAdministradoresDaEscola()
    mock_request.user = usuario_coordenador_codae[0]
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_escola_has_permission_retorna_false_usuario_anonimo(
    mock_request,
):
    permission = PodeCriarAdministradoresDaEscola()
    mock_request.user.is_anonymous = True
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_escola_has_object_permission_retorna_true(
    mock_request, usuario_diretor_escola, escola
):
    permission = PodeCriarAdministradoresDaEscola()
    mock_request.user = usuario_diretor_escola[0]
    assert permission.has_object_permission(mock_request, None, escola) is True


def test_pode_criar_administradores_escola_has_object_permission_retorna_false(
    mock_request, usuario_diretor_escola, diretoria_regional
):
    permission = PodeCriarAdministradoresDaEscola()
    mock_request.user = usuario_diretor_escola[0]
    assert (
        permission.has_object_permission(mock_request, None, diretoria_regional)
        is False
    )


# PodeCriarAdministradoresDaDiretoriaRegional
def test_pode_criar_administradores_diretoria_regional_has_permission_retorna_true(
    mock_request,
):
    permission = PodeCriarAdministradoresDaDiretoriaRegional()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = COGESTOR_DRE
    assert permission.has_permission(mock_request, None) is True


def test_pode_criar_administradores_diretoria_regional_has_permission_retorna_false(
    mock_request,
):
    permission = PodeCriarAdministradoresDaDiretoriaRegional()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = DIRETOR_UE
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_diretoria_regional_has_permission_retorna_false_usuario_anonimo(
    mock_request,
):
    permission = PodeCriarAdministradoresDaDiretoriaRegional()
    mock_request.user.is_anonymous = True
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_diretoria_regional_has_object_permission_retorna_true(
    mock_request, usuario_diretor_escola, escola
):
    permission = PodeCriarAdministradoresDaDiretoriaRegional()
    mock_request.user = usuario_diretor_escola[0]
    assert permission.has_object_permission(mock_request, None, escola) is True


def test_pode_criar_administradores_diretoria_regional_has_object_permission_retorna_false(
    mock_request, usuario_diretor_escola, diretoria_regional
):
    permission = PodeCriarAdministradoresDaDiretoriaRegional()
    mock_request.user = usuario_diretor_escola[0]
    assert (
        permission.has_object_permission(mock_request, None, diretoria_regional)
        is False
    )


# PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada
def test_pode_criar_administradores_codae_tercerizadas_has_permission_retorna_true(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = (
        COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA
    )
    assert permission.has_permission(mock_request, None) is True


def test_pode_criar_administradores_codae_tercerizadas_has_permission_retorna_false(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = DIRETOR_UE
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_codae_tercerizadas_has_permission_retorna_false_usuario_anonimo(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoAlimentacaoTerceirizada()
    mock_request.user.is_anonymous = True
    assert permission.has_permission(mock_request, None) is False


# PodeCriarAdministradoresDaCODAEGestaoDietaEspecial
def test_pode_criar_administradores_codae_dieta_especial_has_permission_retorna_true(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoDietaEspecial()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = COORDENADOR_DIETA_ESPECIAL
    assert permission.has_permission(mock_request, None) is True


def test_pode_criar_administradores_codae_dieta_especial_has_permission_retorna_false(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoDietaEspecial()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = DIRETOR_UE
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_codae_dieta_especial_has_permission_retorna_false_usuario_anonimo(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoDietaEspecial()
    mock_request.user.is_anonymous = True
    assert permission.has_permission(mock_request, None) is False


# PodeCriarAdministradoresDaCODAEGestaoProdutos
def test_pode_criar_administradores_codae_produtos_has_permission_retorna_true(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoProdutos()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = COORDENADOR_GESTAO_PRODUTO
    assert permission.has_permission(mock_request, None) is True


def test_pode_criar_administradores_codae_produtos_has_permission_retorna_false(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoProdutos()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = DIRETOR_UE
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_codae_produtos_has_permission_retorna_false_usuario_anonimo(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAEGestaoProdutos()
    mock_request.user.is_anonymous = True
    assert permission.has_permission(mock_request, None) is False


# PodeCriarAdministradoresDaCODAESupervisaoNutricao
def test_pode_criar_administradores_codae_nutricao_has_permission_retorna_true(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAESupervisaoNutricao()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = COORDENADOR_SUPERVISAO_NUTRICAO
    assert permission.has_permission(mock_request, None) is True


def test_pode_criar_administradores_codae_nutricao_has_permission_retorna_false(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAESupervisaoNutricao()
    mock_request.user.is_anonymous = False
    mock_request.user.vinculo_atual.perfil.nome = DIRETOR_UE
    assert permission.has_permission(mock_request, None) is False


def test_pode_criar_administradores_codae_nutricao_has_permission_retorna_false_usuario_anonimo(
    mock_request,
):
    permission = PodeCriarAdministradoresDaCODAESupervisaoNutricao()
    mock_request.user.is_anonymous = True
    assert permission.has_permission(mock_request, None) is False


# PodeVerEditarFotoAlunoNoSGP
def test_pode_ver_editar_foto_has_object_permission_retorna_true(
    mock_request, usuario_diretor_escola, dia_calendario_letivo
):
    permission = PodeVerEditarFotoAlunoNoSGP()
    mock_request.user = usuario_diretor_escola[0]
    assert (
        permission.has_object_permission(mock_request, None, dia_calendario_letivo)
        is True
    )


def test_pode_ver_editar_foto_has_object_permission_retorna_true_model_codae(
    mock_request, dia_calendario_letivo
):
    permission = PodeVerEditarFotoAlunoNoSGP()
    mock_request.user.vinculo_atual.content_type.model = "codae"
    assert (
        permission.has_object_permission(mock_request, None, dia_calendario_letivo)
        is True
    )
