import json

import pytest
from rest_framework import status

from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
)

pytestmark = pytest.mark.django_db


def test_patch_analise_documentos_aprovar(
    client_autenticado_vinculo_dilog_qualidade,
    documento_de_recebimento_factory,
):
    client, _ = client_autenticado_vinculo_dilog_qualidade
    documento_de_recebimento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    )

    payload = {
        "laboratorio": f"{documento_de_recebimento.laboratorio.uuid}",
        "quantidade_laudo": "100",
        "unidade_medida": f"{documento_de_recebimento.unidade_medida.uuid}",
        "data_final_lote": "30/05/2024",
        "numero_lote_laudo": "123456",
        "datas_fabricacao_e_prazos": [
            {
                "data_fabricacao": "05/03/2024",
                "data_validade": "21/06/2024",
                "prazo_maximo_recebimento": "30",
                "justificativa": "",
            }
        ],
    }

    response = client.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/analise-documentos/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.json()["status"] == "Aprovado"
    assert response.status_code == status.HTTP_200_OK


def test_patch_analise_documentos_enviar_para_correcao(
    client_autenticado_vinculo_dilog_qualidade,
    documento_de_recebimento_factory,
):
    client, _ = client_autenticado_vinculo_dilog_qualidade
    documento_de_recebimento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    )

    payload = {
        "laboratorio": f"{documento_de_recebimento.laboratorio.uuid}",
        "quantidade_laudo": "100",
        "unidade_medida": f"{documento_de_recebimento.unidade_medida.uuid}",
        "data_final_lote": "30/05/2024",
        "numero_lote_laudo": "123456",
        "datas_fabricacao_e_prazos": [
            {
                "data_fabricacao": "05/03/2024",
                "data_validade": "21/06/2024",
                "prazo_maximo_recebimento": "30",
                "justificativa": "",
            }
        ],
        "correcao_solicitada": "Correções necessárias",
    }

    response = client.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/analise-documentos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.json()["status"] == "Enviado para Correção"
    assert response.status_code == status.HTTP_200_OK


def test_patch_analise_documentos_enviar_para_correcao_com_campos_vazios(
    client_autenticado_vinculo_dilog_qualidade,
    documento_de_recebimento_factory,
):
    client, _ = client_autenticado_vinculo_dilog_qualidade
    documento_de_recebimento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    )

    # Enviando apenas correcao_solicitada para validar o relaxamento da obrigatoriedade
    payload = {
        "correcao_solicitada": "Correções necessárias com campos omitidos",
    }

    response = client.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/analise-documentos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.json()["status"] == "Enviado para Correção"
    assert response.status_code == status.HTTP_200_OK


def test_patch_analise_documentos_aprovar_invalido_campos_vazios(
    client_autenticado_vinculo_dilog_qualidade,
    documento_de_recebimento_factory,
):
    client, _ = client_autenticado_vinculo_dilog_qualidade
    documento_de_recebimento = documento_de_recebimento_factory(
        status=DocumentoDeRecebimento.workflow_class.ENVIADO_PARA_ANALISE
    )

    # Payload vazio para aprovação (sem correcao_solicitada)
    payload = {}

    response = client.patch(
        f"/documentos-de-recebimento/{documento_de_recebimento.uuid}/analise-documentos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    # Deve retornar 400 Bad Request pois não é uma solicitação de correção e os campos são obrigatórios
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    errors = response.json()
    assert "laboratorio" in errors
    assert "quantidade_laudo" in errors
    assert "unidade_medida" in errors
