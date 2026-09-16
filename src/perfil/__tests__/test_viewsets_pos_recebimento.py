import datetime

import pytest
from model_bakery import baker
from rest_framework import status

from src.dados_comuns import constants

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario_fiscal(django_user_model):
    """Usuário com perfil DILOG_QUALIDADE vinculado à CODAE."""
    email = "fiscal@test.com"
    user = django_user_model.objects.create_user(
        username=email,
        password=constants.DJANGO_ADMIN_PASSWORD,
        email=email,
        registro_funcional="1234567",
        nome="Fiscal de Qualidade",
    )
    perfil = baker.make("Perfil", nome=constants.DILOG_QUALIDADE, ativo=True)
    codae = baker.make("Codae")
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    return user


def test_usuarios_fiscais_retorna_apenas_perfil_dilog_qualidade(
    client_autenticado_dilog_cronograma,
    usuario_fiscal,
    django_user_model,
):
    email = "outro@test.com"
    usuario_sem_perfil = django_user_model.objects.create_user(
        username=email,
        password=constants.DJANGO_ADMIN_PASSWORD,
        email=email,
        registro_funcional="9999999",
        nome="Outro Usuário",
    )
    perfil_cronograma = baker.make(
        "Perfil", nome=constants.DILOG_CRONOGRAMA, ativo=True
    )
    baker.make(
        "Vinculo",
        usuario=usuario_sem_perfil,
        instituicao=baker.make("Codae"),
        perfil=perfil_cronograma,
        ativo=True,
    )

    response = client_autenticado_dilog_cronograma.get("/usuarios/fiscais/")

    assert response.status_code == status.HTTP_200_OK
    resultados = response.json()["results"]
    uuids = [item["uuid"] for item in resultados]
    assert str(usuario_fiscal.uuid) in uuids
    assert str(usuario_sem_perfil.uuid) not in uuids
    assert all(item["nome"] for item in resultados)


def test_usuarios_fiscais_negado_para_perfil_sem_permissao(
    client_autenticado_qualidade,
):
    response = client_autenticado_qualidade.get("/usuarios/fiscais/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
