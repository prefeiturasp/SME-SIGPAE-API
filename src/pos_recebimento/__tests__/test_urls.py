import json

import pytest
from model_bakery import baker
from rest_framework import status

from src.dados_comuns import constants as const
from src.pos_recebimento.models import TermoRecebimentoDefinitivo
from src.pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


def _post_json(client, url, payload):
    return client.post(
        url,
        content_type="application/json",
        data=json.dumps(payload),
    )


def _usuario_com_perfil(django_user_model, email, nome_perfil, registro_funcional):
    """Cria usuário com perfil vinculado à CODAE e retorna o usuário."""
    user = django_user_model.objects.create_user(
        username=email,
        password=const.DJANGO_ADMIN_PASSWORD,
        email=email,
        registro_funcional=registro_funcional,
        nome=email.split("@")[0],
    )
    perfil = baker.make("Perfil", nome=nome_perfil, ativo=True)
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=baker.make("Codae"),
        perfil=perfil,
        ativo=True,
    )
    return user


def test_termo_create_retorna_201(
    client_autenticado_dilog_cronograma,
    payload_termo,
):
    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload_termo,
    )

    assert response.status_code == status.HTTP_201_CREATED
    termo = TermoRecebimentoDefinitivo.objects.get(uuid=response.json()["uuid"])
    assert termo.status == TermoRecebimentoDefinitivo.ENVIADO
    assert termo.criado_por is not None
    assert termo.alterado_por is not None
    assert termo.cronogramas_termo.count() == 1
    cronograma_termo = termo.cronogramas_termo.first()
    assert str(cronograma_termo.cronograma.uuid) in (
        response.json()["cronogramas"][0]["cronograma"]["uuid"]
    )
    assert response.json()["cronogramas"][0]["valor_contrato"] == "150000.00"
    assert response.json()["cronogramas"][0]["quantidade_total_recebida"] == "1234.56"


def test_termo_create_negado_para_perfil_sem_permissao(
    client_autenticado_qualidade,
    payload_termo,
):
    response = _post_json(
        client_autenticado_qualidade,
        "/pos-recebimento/termos/",
        payload_termo,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_termo_create_valida_campos_obrigatorios(
    client_autenticado_dilog_cronograma,
    payload_termo,
):
    payload = dict(payload_termo)
    payload.pop("texto_termo")
    payload["cronogramas"] = [{"cronograma": payload["cronogramas"][0]["cronograma"]}]

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "texto_termo" in response.data
    assert "cronogramas" in response.data


def test_termo_create_valida_empresa_sem_ficha_assinada(
    client_autenticado_dilog_cronograma,
    tres_fiscais,
):
    empresa_sem_ficha = EmpresaFactory()
    contrato = ContratoFactory(terceirizada=empresa_sem_ficha)
    cronograma_sem_ficha = CronogramaFactory(
        contrato=contrato, empresa=empresa_sem_ficha
    )

    payload = {
        "empresa": str(empresa_sem_ficha.uuid),
        "contrato": str(contrato.uuid),
        "cronogramas": [
            {
                "cronograma": str(cronograma_sem_ficha.uuid),
                "valor_contrato": "1000.00",
                "quantidade_total_recebida": "100.00",
            }
        ],
        "fiscal_1": str(tres_fiscais[0].uuid),
        "fiscal_2": str(tres_fiscais[1].uuid),
        "fiscal_3": str(tres_fiscais[2].uuid),
        "texto_termo": "<p>Termo</p>",
    }

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "ficha de recebimento" in str(response.data)


def test_termo_create_valida_fiscal_sem_perfil_dilog_qualidade(
    client_autenticado_dilog_cronograma,
    payload_termo,
    django_user_model,
):
    usuario_sem_perfil = _usuario_com_perfil(
        django_user_model,
        "semperfil@test.com",
        const.DILOG_CRONOGRAMA,
        "8888888",
    )

    payload = dict(payload_termo)
    payload["fiscal_1"] = str(usuario_sem_perfil.uuid)

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "DILOG_QUALIDADE" in str(response.data)


def test_termo_create_valida_cronograma_de_outro_contrato(
    client_autenticado_dilog_cronograma,
    ficha_assinada,
    tres_fiscais,
):
    cronograma = ficha_assinada.etapa.cronograma
    outro_contrato = ContratoFactory(terceirizada=cronograma.empresa)
    cronograma_outro_contrato = CronogramaFactory(
        contrato=outro_contrato, empresa=cronograma.empresa
    )

    payload = {
        "empresa": str(cronograma.empresa.uuid),
        "contrato": str(cronograma.contrato.uuid),
        "cronogramas": [
            {
                "cronograma": str(cronograma_outro_contrato.uuid),
                "valor_contrato": "1000.00",
                "quantidade_total_recebida": "100.00",
            }
        ],
        "fiscal_1": str(tres_fiscais[0].uuid),
        "fiscal_2": str(tres_fiscais[1].uuid),
        "fiscal_3": str(tres_fiscais[2].uuid),
        "texto_termo": "<p>Termo</p>",
    }

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "não pertence ao" in str(response.data)


def test_termo_create_valida_contrato_de_outra_empresa(
    client_autenticado_dilog_cronograma,
    ficha_assinada,
    tres_fiscais,
):
    cronograma = ficha_assinada.etapa.cronograma
    outra_empresa = EmpresaFactory()
    contrato_outra_empresa = ContratoFactory(terceirizada=outra_empresa)

    payload = {
        "empresa": str(cronograma.empresa.uuid),
        "contrato": str(contrato_outra_empresa.uuid),
        "cronogramas": [
            {
                "cronograma": str(cronograma.uuid),
                "valor_contrato": "1000.00",
                "quantidade_total_recebida": "100.00",
            }
        ],
        "fiscal_1": str(tres_fiscais[0].uuid),
        "fiscal_2": str(tres_fiscais[1].uuid),
        "fiscal_3": str(tres_fiscais[2].uuid),
        "texto_termo": "<p>Termo</p>",
    }

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "não pertence à empresa" in str(response.data)


def test_termo_create_valida_cronogramas_vazios(
    client_autenticado_dilog_cronograma,
    payload_termo,
):
    payload = dict(payload_termo)
    payload["cronogramas"] = []

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cronogramas" in response.data


def test_termo_create_valida_texto_termo_apenas_tags(
    client_autenticado_dilog_cronograma,
    payload_termo,
):
    payload = dict(payload_termo)
    payload["texto_termo"] = "<p></p>"

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "texto_termo" in response.data


def test_termo_create_valida_cronograma_duplicado(
    client_autenticado_dilog_cronograma,
    payload_termo,
):
    payload = dict(payload_termo)
    payload["cronogramas"].append(payload["cronogramas"][0])

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "mais de uma vez" in str(response.data)


def test_termo_create_valida_valores_maiores_que_zero(
    client_autenticado_dilog_cronograma,
    payload_termo,
):
    payload = dict(payload_termo)
    payload["cronogramas"][0]["valor_contrato"] = "-10.00"
    payload["cronogramas"][0]["quantidade_total_recebida"] = "0"

    response = _post_json(
        client_autenticado_dilog_cronograma,
        "/pos-recebimento/termos/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cronogramas[0].valor_contrato" in response.data
    assert "cronogramas[0].quantidade_total_recebida" in response.data
