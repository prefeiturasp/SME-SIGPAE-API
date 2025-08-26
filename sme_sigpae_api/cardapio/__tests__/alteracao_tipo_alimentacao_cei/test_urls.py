import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns import constants
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from sme_sigpae_api.dados_comuns.constants import (
    PEDIDOS_CODAE,
    PEDIDOS_DRE,
    SEM_FILTRO,
)

pytestmark = pytest.mark.django_db


ENDPOINT_ALTERACAO_CARD_CEI = "alteracoes-cardapio-cei"


def test_url_endpoint_alt_card_cei_inicio(
    client_autenticado_vinculo_escola_cardapio, alteracao_cardapio_cei
):
    assert str(alteracao_cardapio_cei.status) == PedidoAPartirDaEscolaWorkflow.RASCUNHO
    response = client_autenticado_vinculo_escola_cardapio.patch(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{alteracao_cardapio_cei.uuid}/{constants.ESCOLA_INICIO_PEDIDO}/"
    )

    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert json["status"] == PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    assert str(json["uuid"]) == str(alteracao_cardapio_cei.uuid)


def test_url_endpoint_alt_card_cei_relatorio(
    client_autenticado, alteracao_cardapio_cei
):
    response = client_autenticado.get(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{alteracao_cardapio_cei.uuid}/{constants.RELATORIO}/"
    )
    id_externo = alteracao_cardapio_cei.id_externo
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'filename="alteracao_cardapio_{id_externo}.pdf"'
    )
    assert "PDF-1." in str(response.content)
    assert isinstance(response.content, bytes)


def test_motivos_alteracao_cardapio_escola_cei_queryset(
    client_autenticado_vinculo_escola_cei_cardapio,
    motivo_alteracao_cardapio,
    motivo_alteracao_cardapio_lanche_emergencial,
    motivo_alteracao_cardapio_inativo,
):
    response = client_autenticado_vinculo_escola_cei_cardapio.get(
        "/motivos-alteracao-cardapio/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1

def test_url_alteracoes_cardapio_cei_codae(
    client_autenticado_vinculo_codae_inclusao
):
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)

def test_url_alteracoes_cardapio_cei_dre(
    client_autenticado_vinculo_dre_inclusao
):
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)   
