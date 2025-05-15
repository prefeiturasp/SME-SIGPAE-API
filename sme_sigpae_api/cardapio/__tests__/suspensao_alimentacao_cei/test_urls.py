import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.fluxo_status import (
    InformativoPartindoDaEscolaWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)

pytestmark = pytest.mark.django_db

ENDPOINT_SUSPENSOES_DE_CEI = "suspensao-alimentacao-de-cei"
ESCOLA_INFORMA_SUSPENSAO = "informa-suspensao"


def test_permissoes_suspensao_alimentacao_cei_viewset(
    client_autenticado_vinculo_escola_cardapio, suspensao_alimentacao_de_cei
):
    response = client_autenticado_vinculo_escola_cardapio.get(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_200_OK

    suspensao_alimentacao_de_cei.status = InformativoPartindoDaEscolaWorkflow.INFORMADO
    suspensao_alimentacao_de_cei.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for RASCUNHO."
    }

    suspensao_alimentacao_de_cei.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    suspensao_alimentacao_de_cei.save()

    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/{ESCOLA_INFORMA_SUSPENSAO}/"
    )
    assert response.status_code == status.HTTP_200_OK

    suspensao_alimentacao_de_cei.status = PedidoAPartirDaEscolaWorkflow.RASCUNHO
    suspensao_alimentacao_de_cei.save()
    response = client_autenticado_vinculo_escola_cardapio.delete(
        f"/{ENDPOINT_SUSPENSOES_DE_CEI}/{suspensao_alimentacao_de_cei.uuid}/"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
