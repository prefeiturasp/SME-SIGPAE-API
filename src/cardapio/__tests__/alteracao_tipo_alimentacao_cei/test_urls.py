import datetime
import json

import pytest
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from src.dados_comuns import constants
from src.dados_comuns.constants import (
    PEDIDOS_CODAE,
    PEDIDOS_DRE,
    SEM_FILTRO,
)
from src.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from src.escola.dias_letivos.models import DiaLetivoSIGPAE

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


def test_url_alteracoes_cardapio_cei_codae(client_autenticado_vinculo_codae_inclusao):
    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_alteracoes_cardapio_cei_dre(client_autenticado_vinculo_dre_inclusao):
    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def _payload_rpl_cei(
    escola_cei,
    motivo_rpl,
    periodo_escolar,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche,
):
    return {
        "escola": str(escola_cei.uuid),
        "motivo": str(motivo_rpl.uuid),
        "data": "18/11/2023",
        "substituicoes": [
            {
                "periodo_escolar": str(periodo_escolar.uuid),
                "tipos_alimentacao_de": [str(tipo_alimentacao_refeicao.uuid)],
                "tipo_alimentacao_para": str(tipo_alimentacao_lanche.uuid),
                "faixas_etarias": [],
            }
        ],
    }


@freeze_time("2023-11-09")
def test_alteracao_cei_rpl_sem_dia_letivo_ou_inclusao_deve_bloquear(
    client_autenticado_vinculo_escola_cei_cardapio,
    escola_cei,
    motivo_alteracao_cardapio_rpl,
    periodo_escolar,
    tipo_alimentacao,
    tipo_alimentacao_lanche,
):
    data = _payload_rpl_cei(
        escola_cei,
        motivo_alteracao_cardapio_rpl,
        periodo_escolar,
        tipo_alimentacao,
        tipo_alimentacao_lanche,
    )
    response = client_autenticado_vinculo_escola_cei_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["data"] == [
        "Dia 18/11 não é um dia letivo ou não existe uma inclusão de "
        "alimentação para a data"
    ]


@freeze_time("2023-11-09")
def test_alteracao_cei_rpl_com_dia_letivo_sigpae(
    client_autenticado_vinculo_escola_cei_cardapio,
    escola_cei,
    motivo_alteracao_cardapio_rpl,
    periodo_escolar,
    tipo_alimentacao,
    tipo_alimentacao_lanche,
):
    dia_letivo = baker.make(DiaLetivoSIGPAE, data=datetime.date(2023, 11, 18))
    dia_letivo.escolas.add(escola_cei)
    data = _payload_rpl_cei(
        escola_cei,
        motivo_alteracao_cardapio_rpl,
        periodo_escolar,
        tipo_alimentacao,
        tipo_alimentacao_lanche,
    )
    response = client_autenticado_vinculo_escola_cei_cardapio.post(
        f"/{ENDPOINT_ALTERACAO_CARD_CEI}/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
