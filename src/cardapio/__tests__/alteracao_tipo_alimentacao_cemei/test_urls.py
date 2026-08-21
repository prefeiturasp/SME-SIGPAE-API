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
from src.escola.dias_letivos.models import DiaLetivoSIGPAE

pytestmark = pytest.mark.django_db


@freeze_time("2023-07-14")
def test_alteracao_cemei_solicitacoes_dre(
    client_autenticado_vinculo_dre_escola_cemei, alteracao_cemei_dre_a_validar
):
    response = client_autenticado_vinculo_dre_escola_cemei.get(
        f"/alteracoes-cardapio-cemei/{constants.PEDIDOS_DRE}/{constants.DAQUI_A_TRINTA_DIAS}/"
        f"?lote={alteracao_cemei_dre_a_validar.rastro_lote.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 1
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


@freeze_time("2023-07-14")
def test_alteracao_cemei_solicitacoes_codae(
    client_autenticado_vinculo_codae_cardapio, alteracao_cemei_dre_validado
):
    response = client_autenticado_vinculo_codae_cardapio.get(
        f"/alteracoes-cardapio-cemei/{constants.PEDIDOS_CODAE}/{constants.DAQUI_A_TRINTA_DIAS}/"
        f"?lote={alteracao_cemei_dre_validado.rastro_lote.uuid}"
        f"&diretoria_regional={alteracao_cemei_dre_validado.rastro_dre.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 1
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


@freeze_time("2023-07-14")
def test_create_alteracao_cemei_cei(
    client_autenticado_vinculo_escola_cemei,
    escola_cemei,
    motivo_alteracao_cardapio,
    periodo_escolar,
    tipo_alimentacao,
    faixas_etarias_ativas,
):
    data = {
        "escola": str(escola_cemei.uuid),
        "motivo": str(motivo_alteracao_cardapio.uuid),
        "alunos_cei_e_ou_emei": "CEI",
        "alterar_dia": "30/07/2023",
        "substituicoes_cemei_cei_periodo_escolar": [
            {
                "periodo_escolar": str(periodo_escolar.uuid),
                "tipos_alimentacao_de": [str(tipo_alimentacao.uuid)],
                "tipos_alimentacao_para": [str(tipo_alimentacao.uuid)],
                "faixas_etarias": [
                    {
                        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
                        "quantidade": "12",
                        "matriculados_quando_criado": 33,
                    }
                ],
            }
        ],
        "substituicoes_cemei_emei_periodo_escolar": [],
        "observacao": "<p>adsasdasd</p>",
    }
    response = client_autenticado_vinculo_escola_cemei.post(
        "/alteracoes-cardapio-cemei/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["escola"] == str(escola_cemei.uuid)
    assert response.json()["alunos_cei_e_ou_emei"] == "CEI"
    assert len(response.json()["substituicoes_cemei_cei_periodo_escolar"]) == 1
    assert len(response.json()["substituicoes_cemei_emei_periodo_escolar"]) == 0
    assert response.json()["alterar_dia"] == "30/07/2023"
    assert response.json()["status"] == "RASCUNHO"


@freeze_time("2023-07-14")
def test_create_alteracao_cemei_emei(
    client_autenticado_vinculo_escola_cemei,
    escola_cemei,
    motivo_alteracao_cardapio,
    periodo_escolar,
    tipo_alimentacao,
):
    data = {
        "escola": str(escola_cemei.uuid),
        "motivo": str(motivo_alteracao_cardapio.uuid),
        "alunos_cei_e_ou_emei": "EMEI",
        "alterar_dia": "30/07/2023",
        "substituicoes_cemei_cei_periodo_escolar": [],
        "substituicoes_cemei_emei_periodo_escolar": [
            {
                "qtd_alunos": "30",
                "matriculados_quando_criado": 75,
                "periodo_escolar": str(periodo_escolar.uuid),
                "tipos_alimentacao_de": [str(tipo_alimentacao.uuid)],
                "tipos_alimentacao_para": [str(tipo_alimentacao.uuid)],
            }
        ],
        "observacao": "<p>adsasdasd</p>",
    }
    response = client_autenticado_vinculo_escola_cemei.post(
        "/alteracoes-cardapio-cemei/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["escola"] == str(escola_cemei.uuid)
    assert response.json()["alunos_cei_e_ou_emei"] == "EMEI"
    assert len(response.json()["substituicoes_cemei_cei_periodo_escolar"]) == 0
    assert len(response.json()["substituicoes_cemei_emei_periodo_escolar"]) == 1
    assert response.json()["alterar_dia"] == "30/07/2023"
    assert response.json()["status"] == "RASCUNHO"


def test_url_alteracoes_cardapio_cemei_codae(client_autenticado_vinculo_codae_cardapio):
    response = client_autenticado_vinculo_codae_cardapio.get(
        f"/alteracoes-cardapio-cemei/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_alteracoes_cardapio_cemei_dre(client_autenticado_vinculo_dre_escola_cemei):
    response = client_autenticado_vinculo_dre_escola_cemei.get(
        f"/alteracoes-cardapio-cemei/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def _payload_rpl_cemei(
    escola_cemei,
    motivo_rpl,
    periodo_escolar,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche,
    faixas_etarias_ativas,
):
    return {
        "escola": str(escola_cemei.uuid),
        "motivo": str(motivo_rpl.uuid),
        "alunos_cei_e_ou_emei": "CEI",
        "alterar_dia": "30/07/2023",
        "substituicoes_cemei_cei_periodo_escolar": [
            {
                "periodo_escolar": str(periodo_escolar.uuid),
                "tipos_alimentacao_de": [str(tipo_alimentacao_refeicao.uuid)],
                "tipos_alimentacao_para": [str(tipo_alimentacao_lanche.uuid)],
                "faixas_etarias": [
                    {
                        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
                        "quantidade": "12",
                        "matriculados_quando_criado": 33,
                    }
                ],
            }
        ],
        "substituicoes_cemei_emei_periodo_escolar": [],
        "observacao": "<p>teste</p>",
    }


@freeze_time("2023-07-14")
def test_create_alteracao_cemei_rpl_sem_dia_letivo_ou_inclusao_deve_bloquear(
    client_autenticado_vinculo_escola_cemei,
    escola_cemei,
    motivo_alteracao_cardapio_rpl,
    periodo_escolar,
    tipo_alimentacao,
    tipo_alimentacao_lanche,
    faixas_etarias_ativas,
):
    data = _payload_rpl_cemei(
        escola_cemei,
        motivo_alteracao_cardapio_rpl,
        periodo_escolar,
        tipo_alimentacao,
        tipo_alimentacao_lanche,
        faixas_etarias_ativas,
    )
    response = client_autenticado_vinculo_escola_cemei.post(
        "/alteracoes-cardapio-cemei/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == [
        "Dia 30/07 não é um dia letivo ou não existe uma inclusão de "
        "alimentação para a data"
    ]


@freeze_time("2023-07-14")
def test_create_alteracao_cemei_rpl_com_dia_letivo_sigpae(
    client_autenticado_vinculo_escola_cemei,
    escola_cemei,
    motivo_alteracao_cardapio_rpl,
    periodo_escolar,
    tipo_alimentacao,
    tipo_alimentacao_lanche,
    faixas_etarias_ativas,
):
    dia_letivo = baker.make(DiaLetivoSIGPAE, data=datetime.date(2023, 7, 30))
    dia_letivo.escolas.add(escola_cemei)
    data = _payload_rpl_cemei(
        escola_cemei,
        motivo_alteracao_cardapio_rpl,
        periodo_escolar,
        tipo_alimentacao,
        tipo_alimentacao_lanche,
        faixas_etarias_ativas,
    )
    response = client_autenticado_vinculo_escola_cemei.post(
        "/alteracoes-cardapio-cemei/",
        content_type="application/json",
        data=json.dumps(data),
    )
    assert response.status_code == status.HTTP_201_CREATED
