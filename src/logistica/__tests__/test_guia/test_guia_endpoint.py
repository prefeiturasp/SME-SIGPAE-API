import datetime
import json

import pytest
from rest_framework import status

from src.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from src.dados_comuns.fluxo_status import NotificacaoOcorrenciaWorkflow
from src.logistica.models import ConferenciaGuia, Guia
from src.logistica.models.guia import (
    ConferenciaIndividualPorAlimento,
    InsucessoEntregaGuia,
)

pytestmark = pytest.mark.django_db


def test_url_authorized_numeros(client_autenticado_dilog, guia):
    response = client_autenticado_dilog.get("/guias-da-requisicao/lista-numeros/")
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_inconsistencias(client_autenticado_codae_dilog, guia):
    response = client_autenticado_codae_dilog.get(
        "/guias-da-requisicao/inconsistencias/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_insucesso(client_autenticado_distribuidor, guia):
    response = client_autenticado_distribuidor.get(
        "/guias-da-requisicao/lista-guias-para-insucesso/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_guias_escola(client_autenticado_escola_abastecimento, guia):
    response = client_autenticado_escola_abastecimento.get(
        "/guias-da-requisicao/guias-escola/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_get_guia_conferencia_escola_invalida(
    client_autenticado_escola_abastecimento, guia
):
    response = client_autenticado_escola_abastecimento.get(
        "/guias-da-requisicao/guia-para-conferencia/?uuid=" + str(guia.uuid)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_get_guia_conferencia_uuid_invalido(
    client_autenticado_escola_abastecimento, guia
):
    # Sem UUID
    response = client_autenticado_escola_abastecimento.get(
        "/guias-da-requisicao/guia-para-conferencia/"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # UUID inválido
    response = client_autenticado_escola_abastecimento.get(
        "/guias-da-requisicao/guia-para-conferencia/?uuid=123"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # UUID válido, porem sem guia
    response = client_autenticado_escola_abastecimento.get(
        "/guias-da-requisicao/guia-para-conferencia/?uuid=77316319-2645-493d-887d-55e40c3e74bb"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_url_get_guia_conferencia(
    client_autenticado_escola_abastecimento, guia_com_escola_client_autenticado, escola
):
    response = client_autenticado_escola_abastecimento.get(
        "/guias-da-requisicao/guia-para-conferencia/?uuid="
        + str(guia_com_escola_client_autenticado.uuid)
    )
    assert Guia.objects.exists()
    assert Guia.objects.get(uuid=str(guia_com_escola_client_autenticado.uuid))
    assert response.status_code == status.HTTP_200_OK


def test_url_conferir_guia_recebida(
    client_autenticado_escola_abastecimento, guia_com_escola_client_autenticado
):
    payload = {
        "guia": str(guia_com_escola_client_autenticado.uuid),
        "nome_motorista": "José",
        "placa_veiculo": "AAABV44",
        "data_recebimento": "04/04/2021",
        "hora_recebimento": "03:04",
    }

    response = client_autenticado_escola_abastecimento.post(
        "/conferencia-da-guia/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    conferencia = ConferenciaGuia.objects.first()

    assert response.status_code == status.HTTP_201_CREATED
    assert conferencia.uuid
    assert conferencia.criado_por


def test_url_authorized_insucesso_entrega_list(client_autenticado_distribuidor, guia):
    response = client_autenticado_distribuidor.get("/insucesso-de-entrega/")
    assert response.status_code == status.HTTP_200_OK


def test_url_registrar_insucesso_entrega(
    client_autenticado_distribuidor, guia_pendente_de_conferencia
):
    payload = {
        "guia": str(guia_pendente_de_conferencia.uuid),
        "nome_motorista": "José",
        "placa_veiculo": "AAABV44",
        "hora_tentativa": "03:04",
        "motivo": "OUTROS",
        "justificativa": "Unidade estava fechada.",
        "outro_motivo": "Incendio na escola",
    }

    response = client_autenticado_distribuidor.post(
        "/insucesso-de-entrega/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    insucesso_entrega = InsucessoEntregaGuia.objects.first()

    assert response.status_code == status.HTTP_201_CREATED
    assert insucesso_entrega.uuid
    assert insucesso_entrega.criado_por


def test_url_get_guia_para_registro_de_insucesso(
    client_autenticado_distribuidor, guia_pendente_de_conferencia
):
    response = client_autenticado_distribuidor.get(
        "/guias-da-requisicao/guia-para-insucesso/?uuid="
        + str(guia_pendente_de_conferencia.uuid)
    )
    assert Guia.objects.exists()
    assert Guia.objects.get(uuid=str(guia_pendente_de_conferencia.uuid))
    assert response.status_code == status.HTTP_200_OK


def test_url_get_ultima_conferencia(
    client_autenticado_escola_abastecimento, conferencia_guia
):
    response = client_autenticado_escola_abastecimento.get(
        "/conferencia-da-guia-com-ocorrencia/get-ultima-conferencia/?uuid="
        + str(conferencia_guia.guia.uuid)
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_get_ultima_reposicao(
    client_autenticado_escola_abastecimento, reposicao_guia
):
    response = client_autenticado_escola_abastecimento.get(
        "/conferencia-da-guia-com-ocorrencia/get-ultima-reposicao/?uuid="
        + str(reposicao_guia.guia.uuid)
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_conferir_guia_com_ocorrencia(
    client_autenticado_escola_abastecimento,
    guia_com_escola_client_autenticado,
    alimento,
    embalagem,
):
    payload = {
        "guia": str(guia_com_escola_client_autenticado.uuid),
        "nome_motorista": "José",
        "placa_veiculo": "AAABV44",
        "data_recebimento": "04/04/2021",
        "hora_recebimento": "03:04",
        "conferencia_dos_alimentos": [
            {
                "tipo_embalagem": ConferenciaIndividualPorAlimento.FECHADA,
                "nome_alimento": "PATINHO",
                "qtd_recebido": 20,
                "status_alimento": ConferenciaIndividualPorAlimento.STATUS_ALIMENTO_PARCIAL,
                "ocorrencia": [ConferenciaIndividualPorAlimento.OCORRENCIA_QTD_MENOR],
            }
        ],
    }

    response = client_autenticado_escola_abastecimento.post(
        "/conferencia-da-guia-com-ocorrencia/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    conferencia = ConferenciaGuia.objects.first()

    assert response.status_code == status.HTTP_201_CREATED
    assert conferencia.uuid
    assert conferencia.criado_por
    assert conferencia.conferencia_dos_alimentos


def test_url_editar_conferencia_com_ocorrencia(
    client_autenticado_escola_abastecimento, conferencia_guia, alimento, embalagem
):
    payload = {
        "guia": str(conferencia_guia.guia.uuid),
        "nome_motorista": "Fabio",
        "placa_veiculo": "AAABV44",
        "data_recebimento": "04/04/2021",
        "hora_recebimento": "03:04",
        "conferencia_dos_alimentos": [
            {
                "tipo_embalagem": ConferenciaIndividualPorAlimento.FECHADA,
                "nome_alimento": "PATINHO",
                "qtd_recebido": 20,
                "status_alimento": ConferenciaIndividualPorAlimento.STATUS_ALIMENTO_PARCIAL,
                "ocorrencia": [ConferenciaIndividualPorAlimento.OCORRENCIA_QTD_MENOR],
            }
        ],
    }

    response = client_autenticado_escola_abastecimento.put(
        f"/conferencia-da-guia-com-ocorrencia/{conferencia_guia.uuid}/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    conferencia = ConferenciaGuia.objects.first()

    assert response.status_code == status.HTTP_200_OK
    assert conferencia.uuid
    assert conferencia.criado_por
    assert conferencia.nome_motorista == "Fabio"
    assert conferencia.placa_veiculo == "AAABV44"
    assert (
        datetime.date.strftime(conferencia.data_recebimento, "%d/%m/%Y") == "04/04/2021"
    )
    assert datetime.time.strftime(conferencia.hora_recebimento, "%H:%M") == "03:04"


def test_url_relatorio_guia_remessa_authorized_dilog(client_autenticado_dilog, guia):
    response = client_autenticado_dilog.get(
        f"/guias-da-requisicao/{str(guia.uuid)}/relatorio-guia-remessa/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_relatorio_guia_remessa_authorized_distribuidor(
    client_autenticado_distribuidor, guia
):
    response = client_autenticado_distribuidor.get(
        f"/guias-da-requisicao/{str(guia.uuid)}/relatorio-guia-remessa/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_relatorio_guia_remessa_authorized_escola(
    client_autenticado_escola_abastecimento, guia_com_escola_client_autenticado
):
    response = client_autenticado_escola_abastecimento.get(
        f"/guias-da-requisicao/{str(guia_com_escola_client_autenticado.uuid)}/relatorio-guia-remessa/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_notificacao_ocorrencia_listar(
    client_autenticado_codae_dilog, notificacoes_ocorrencia
):
    client = client_autenticado_codae_dilog

    response = client.get("/notificacao-guias-com-ocorrencias/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 20


def test_url_notificacao_ocorrencia_action_solicitar_alteracao(
    client_autenticado_codae_dilog, notificacao_ocorrencia
):
    client = client_autenticado_codae_dilog

    notificacao_ocorrencia.status = (
        NotificacaoOcorrenciaWorkflow.NOTIFICACAO_ENVIADA_FISCAL
    )
    notificacao_ocorrencia.save()

    uuid = notificacao_ocorrencia.uuid
    payload = {
        "previsoes": [
            {
                "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
                "justificativa_alteracao": "Justificativa previsao teste 1",
                "aprovado": False,
            },
            {
                "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_DANIFICADA,
                "justificativa_alteracao": "",
                "aprovado": True,
            },
        ]
    }

    response = client.patch(
        f"/notificacao-guias-com-ocorrencias/{uuid}/solicitar-alteracao/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK

    notificacao_ocorrencia.refresh_from_db()
    assert (
        notificacao_ocorrencia.status
        == NotificacaoOcorrenciaWorkflow.NOTIFICACAO_SOLICITADA_ALTERACAO
    )
    assert notificacao_ocorrencia.previsoes_contratuais.count() == 2


def test_url_notificacao_ocorrencia_action_assinar(
    client_autenticado_codae_dilog, notificacao_ocorrencia
):
    client = client_autenticado_codae_dilog

    notificacao_ocorrencia.status = (
        NotificacaoOcorrenciaWorkflow.NOTIFICACAO_ENVIADA_FISCAL
    )
    notificacao_ocorrencia.save()

    uuid = notificacao_ocorrencia.uuid
    payload = {
        "password": DJANGO_ADMIN_PASSWORD,
        "previsoes": [
            {
                "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA,
                "justificativa_alteracao": "Aprovado em 01/01/2023 - 10:30",
                "aprovado": True,
            },
            {
                "motivo_ocorrencia": ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_DANIFICADA,
                "justificativa_alteracao": "Aprovado em 02/01/2023 - 11:00",
                "aprovado": True,
            },
        ],
    }

    response = client.patch(
        f"/notificacao-guias-com-ocorrencias/{uuid}/assinar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK

    notificacao_ocorrencia.refresh_from_db()
    assert (
        notificacao_ocorrencia.status
        == NotificacaoOcorrenciaWorkflow.NOTIFICACAO_ASSINADA_FISCAL
    )
    assert notificacao_ocorrencia.previsoes_contratuais.count() == 2
