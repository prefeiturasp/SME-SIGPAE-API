import pytest
from rest_framework import status

from src.dados_comuns.constants import SOLICITACOES_DO_USUARIO
from src.perfil.models import Usuario

pytestmark = pytest.mark.django_db


def test_get_minhas_solicitacoes(
    client_autenticado_vinculo_escola_inclusao,
    inclusao_alimentacao_da_cei_factory,
    escola,
    periodo_escolar,
    eolservicosgp_get_lista_alunos,
):
    user = Usuario.objects.get(
        id=client_autenticado_vinculo_escola_inclusao.session["_auth_user_id"]
    )
    inclusao_alimentacao_da_cei = inclusao_alimentacao_da_cei_factory.create(
        criado_por=user, escola=escola
    )
    assert inclusao_alimentacao_da_cei.status == "RASCUNHO"

    response = client_autenticado_vinculo_escola_inclusao.get(
        f"/inclusoes-alimentacao-da-cei/{SOLICITACOES_DO_USUARIO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_destroy(
    client_autenticado_vinculo_escola_inclusao,
    inclusao_alimentacao_da_cei_factory,
    escola,
    periodo_escolar,
    eolservicosgp_get_lista_alunos,
):
    user = Usuario.objects.get(
        id=client_autenticado_vinculo_escola_inclusao.session["_auth_user_id"]
    )
    inclusao_alimentacao_da_cei = inclusao_alimentacao_da_cei_factory.create(
        criado_por=user, escola=escola
    )
    assert inclusao_alimentacao_da_cei.status == "RASCUNHO"

    response = client_autenticado_vinculo_escola_inclusao.delete(
        f"/inclusoes-alimentacao-da-cei/{inclusao_alimentacao_da_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_destroy_falha(
    client_autenticado_vinculo_escola_inclusao,
    inclusao_alimentacao_da_cei_factory,
    escola,
    periodo_escolar,
    eolservicosgp_get_lista_alunos,
):
    user = Usuario.objects.get(
        id=client_autenticado_vinculo_escola_inclusao.session["_auth_user_id"]
    )
    inclusao_alimentacao_da_cei = inclusao_alimentacao_da_cei_factory.create(
        criado_por=user, escola=escola, status="DRE_A_VALIDAR"
    )

    response = client_autenticado_vinculo_escola_inclusao.delete(
        f"/inclusoes-alimentacao-da-cei/{inclusao_alimentacao_da_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }
