import json

import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import (
    ADMINISTRADOR_UE,
    DIRETOR_UE,
    DJANGO_ADMIN_PASSWORD,
)
from sme_sigpae_api.eol_servico.utils import EOLServicoSGP
from sme_sigpae_api.escola.__tests__.conftest import mocked_response
from sme_sigpae_api.escola.services import NovoSGPServicoLogado
from sme_sigpae_api.perfil.__tests__.conftest import (
    mocked_response_autentica_coresso_adm_ue,
    mocked_response_autentica_coresso_cogestor,
    mocked_response_autentica_coresso_diretor,
    mocked_response_autentica_coresso_diretor_login_errado,
    mocked_response_get_dados_usuario_coresso,
    mocked_response_get_dados_usuario_coresso_adm_escola,
    mocked_response_get_dados_usuario_coresso_cieja_assist_coord_geral,
    mocked_response_get_dados_usuario_coresso_cieja_coordenador_geral,
    mocked_response_get_dados_usuario_coresso_cogestor,
    mocked_response_get_dados_usuario_coresso_coordenador,
    mocked_response_get_dados_usuario_coresso_gestor,
    mocked_response_get_dados_usuario_coresso_sem_acesso_automatico,
    mocked_response_get_dados_usuario_coresso_sem_email,
)
from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.perfil.services.autenticacao_service import AutenticacaoService
from utility.carga_dados.perfil.importa_dados import (
    ProcessaPlanilhaUsuarioServidorCoreSSO,
)

pytestmark = pytest.mark.django_db


def test_login_coresso_diretor_sucesso(client_autenticado_da_escola, monkeypatch):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(mocked_response_get_dados_usuario_coresso(), 200),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK


def test_login_coresso_diretor_sucesso_coordenador(
    client_autenticado_da_escola, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_gestor(), 200
        ),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == DIRETOR_UE


def test_login_coresso_diretor_sucesso_gestor(
    client_autenticado_da_escola, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_coordenador(), 200
        ),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == DIRETOR_UE


def test_login_coresso_erro_usuario_nao_existe(
    client_autenticado_da_escola, monkeypatch
):
    data = {"login": "1234568", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor_login_errado(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(mocked_response_get_dados_usuario_coresso(), 200),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Usuário não encontrado."}


def test_login_coresso_erro_usuario_sem_email(
    client_autenticado_da_escola_email_invalido, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}
    monkeypatch.setattr(
        AutenticacaoService, "autentica", lambda p1, p2: mocked_response({}, 200)
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response({"token": "#ABC123"}, 200),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_sem_email(), 200
        ),
    )
    response = client_autenticado_da_escola_email_invalido.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Usuário sem e-mail cadastrado. E-mail é obrigatório."
    }


def test_login_coresso_diretor_era_adm_escola(
    client_autenticado_da_escola_adm, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(mocked_response_get_dados_usuario_coresso(), 200),
    )
    response = client_autenticado_da_escola_adm.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == DIRETOR_UE


def test_login_coresso_diretor_sem_acesso_ao_coresso(
    client_autenticado_da_escola, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService, "autentica", lambda p1, p2: mocked_response({}, 200)
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(mocked_response_get_dados_usuario_coresso(), 200),
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response({"token": "#ABC123"}, 200),
    )
    monkeypatch.setattr(
        ProcessaPlanilhaUsuarioServidorCoreSSO,
        "cria_usuario_servidor",
        lambda p1, p2, p3: None,
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == DIRETOR_UE


def test_login_usuario_com_acesso_automatico_adm_escola(
    client_autenticado_da_escola_adm, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService, "autentica", lambda p1, p2: mocked_response({}, 200)
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_adm_escola(), 200
        ),
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response({"token": "#ABC123"}, 200),
    )
    monkeypatch.setattr(
        ProcessaPlanilhaUsuarioServidorCoreSSO,
        "cria_usuario_servidor",
        lambda p1, p2, p3: None,
    )
    response = client_autenticado_da_escola_adm.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == ADMINISTRADOR_UE


def test_login_coresso_diretor_sem_vinculo_no_sigpae(
    client_autenticado_da_escola_sem_vinculo, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(mocked_response_get_dados_usuario_coresso(), 200),
    )
    response = client_autenticado_da_escola_sem_vinculo.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == DIRETOR_UE


def test_login_coresso_adm_escola_sem_vinculo_no_sigpae(
    client_autenticado_da_escola_sem_vinculo, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_adm_escola(), 200
        ),
    )
    response = client_autenticado_da_escola_sem_vinculo.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == ADMINISTRADOR_UE


def test_login_coresso_cargo_sem_acesso_automatico_sem_vinculo_no_sigpae(
    client_autenticado_da_escola_sem_vinculo, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_sem_acesso_automatico(), 200
        ),
    )
    response = client_autenticado_da_escola_sem_vinculo.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Usuário não possui permissão de acesso ao SIGPAE"
    }


def test_login_coresso_login_cpf_erro(client_autenticado_da_escola_adm, monkeypatch):
    data = {"login": "123456789012", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService, "autentica", lambda p1, p2: mocked_response({}, 200)
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response({"token": "#ABC123"}, 200),
    )
    response = client_autenticado_da_escola_adm.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Usuário não encontrado"}


def test_login_coresso_dados_usuario_erro(
    client_autenticado_da_escola_sem_vinculo, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP, "get_dados_usuario", lambda p1: mocked_response({}, 400)
    )
    response = client_autenticado_da_escola_sem_vinculo.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Usuário não encontrado"}


def test_login_coresso_cogestor_dre(client_autenticado_da_dre, monkeypatch):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_cogestor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_cogestor(), 200
        ),
    )
    response = client_autenticado_da_dre.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK


def test_login_usuario_adm_escola_trocou_unidade_sucesso(
    client_autenticado_da_escola_adm, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(mocked_response_autentica_coresso_adm_ue(), 200),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_adm_escola(), 200
        ),
    )
    response = client_autenticado_da_escola_adm.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == ADMINISTRADOR_UE
    assert usuario.vinculo_atual.instituicao.codigo_eol == "400158"


def test_login_usuario_adm_escola_trocou_unidade_erro(
    client_autenticado_da_escola_adm, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(mocked_response_autentica_coresso_adm_ue(), 200),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_sem_acesso_automatico(), 200
        ),
    )
    response = client_autenticado_da_escola_adm.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Você está sem autorização de acesso à aplicação no momento. "
        "Entre em contato com o administrador do SIGPAE."
    }


def test_login_coresso_cargo_sem_acesso_automatico_no_sigpae(
    client_autenticado_da_escola, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService, "autentica", lambda p1, p2: mocked_response({}, 200)
    )
    monkeypatch.setattr(
        NovoSGPServicoLogado,
        "pegar_token_acesso",
        lambda p1, p2, p3: mocked_response({"token": "#ABC123"}, 200),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_sem_acesso_automatico(), 200
        ),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Usuário não possui permissão de acesso ao SIGPAE"
    }


def test_login_coresso_diretor_que_vira_adm_ue(
    client_autenticado_da_escola, monkeypatch
):
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_adm_escola(), 200
        ),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == ADMINISTRADOR_UE


def test_login_coresso_cieja_coordenador_geral_tem_vinculo_diretor_ue(
    client_autenticado_da_escola, monkeypatch
):
    """Usuário com descricaoCargo 'CIEJA COORDENADOR GERAL' deve ter vínculo DIRETOR_UE."""
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_cieja_coordenador_geral(), 200
        ),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == DIRETOR_UE


def test_login_coresso_cieja_assist_coord_geral_tem_vinculo_diretor_ue(
    client_autenticado_da_escola, monkeypatch
):
    """Usuário com descricaoCargo 'CIEJA ASSIST COORD GERAL' deve ter vínculo DIRETOR_UE."""
    data = {"login": "1234567", "password": DJANGO_ADMIN_PASSWORD}

    monkeypatch.setattr(
        AutenticacaoService,
        "autentica",
        lambda p1, p2: mocked_response(
            mocked_response_autentica_coresso_diretor(), 200
        ),
    )
    monkeypatch.setattr(
        EOLServicoSGP,
        "get_dados_usuario",
        lambda p1: mocked_response(
            mocked_response_get_dados_usuario_coresso_cieja_assist_coord_geral(), 200
        ),
    )
    response = client_autenticado_da_escola.post(
        "/login/", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    usuario = Usuario.objects.get(username=data["login"])
    assert usuario.vinculo_atual.perfil.nome == DIRETOR_UE
