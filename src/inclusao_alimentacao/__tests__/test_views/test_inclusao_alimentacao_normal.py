import pytest
from rest_framework import status

from src.dados_comuns.constants import SOLICITACOES_DO_USUARIO
from src.perfil.models import Usuario

pytestmark = pytest.mark.django_db


def test_get_minhas_solicitacoes(
    client_autenticado_vinculo_escola_inclusao,
    grupo_inclusao_alimentacao_normal_factory,
    escola,
):
    user = Usuario.objects.get(
        id=client_autenticado_vinculo_escola_inclusao.session["_auth_user_id"]
    )
    grupo_inclusao_normal = grupo_inclusao_alimentacao_normal_factory.create(
        criado_por=user, escola=escola
    )
    assert grupo_inclusao_normal.status == "RASCUNHO"

    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/grupos-inclusao-alimentacao-normal/{SOLICITACOES_DO_USUARIO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_get_solicitacoes_diretoria_regional(
    client_autenticado_vinculo_dre_inclusao,
    grupo_inclusao_alimentacao_normal_factory,
    escola,
):
    grupo_inclusao_alimentacao_normal_factory.create(
        escola=escola, rastro_lote=escola.lote, status="DRE_A_VALIDAR"
    )
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/grupos-inclusao-alimentacao-normal/pedidos-diretoria-regional/sem_filtro/?lote={escola.lote.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_get_solicitacoes_codae_gestao_alimentacao(
    client_autenticado_vinculo_codae_inclusao,
    grupo_inclusao_alimentacao_normal_factory,
    escola,
):
    grupo_inclusao_alimentacao_normal_factory.create(
        escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        status="DRE_VALIDADO",
    )

    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/grupos-inclusao-alimentacao-normal/pedidos-codae/sem_filtro/"
        f"?lote={escola.lote.uuid}&diretoria_regional={escola.diretoria_regional.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
