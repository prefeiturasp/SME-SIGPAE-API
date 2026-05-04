import json
import uuid

import pytest
from rest_framework import status

from src.imr.models import FormularioOcorrenciasBase, FormularioSupervisao

pytestmark = pytest.mark.django_db


def test_create_formulario_supervisao(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    escola,
    tipo_ocorrencia_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create()
    tipo_ocorrencia_2 = tipo_ocorrencia_factory.create()

    payload = {
        "data": "2024-05-15",
        "escola": str(escola.uuid),
        "maior_frequencia_no_periodo": 6,
        "ocorrencias_nao_se_aplica": [
            {
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "descricao": "Não se aplica",
            },
            {
                "tipo_ocorrencia": str(tipo_ocorrencia_2.uuid),
                "descricao": "Não se aplica v2",
            },
        ],
    }

    response = client.post(
        f"/imr/rascunho-formulario-supervisao/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    data = response.json()

    instance = FormularioOcorrenciasBase.objects.get(uuid=data["formulario_base"])
    assert response.status_code == status.HTTP_201_CREATED
    assert data["escola"] == str(escola.uuid)
    assert data["maior_frequencia_no_periodo"] == 6
    assert instance.respostas_nao_se_aplica.count() == 2


def test_formulario_supervisao_tipo_ocorrencia_nao_existe(
    client_autenticado_vinculo_coordenador_supervisao_nutricao, escola
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    payload = {
        "data": "2024-05-15",
        "escola": str(escola.uuid),
        "ocorrencias_nao_se_aplica": [
            {
                "tipo_ocorrencia": "2b7a2217-1743-4bcd-8879-cf8e16e34fa6",
                "descricao": "",
            },
        ],
    }
    response = client.post(
        f"/imr/rascunho-formulario-supervisao/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "ocorrencias_nao_se_aplica": {
            "tipo_ocorrencia": [
                "Objeto com uuid=2b7a2217-1743-4bcd-8879-cf8e16e34fa6 não existe."
            ]
        }
    }


def test_formulario_supervisao_respostas_nao(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    escola,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    tipo_resposta_campo_simples = tipo_resposta_modelo_factory(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta_parametrizacao_ocorrencia_texto_simples = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
        )
    )

    tipo_resposta_campo_numerico = tipo_resposta_modelo_factory(
        nome="RespostaCampoNumerico"
    )
    tipo_pergunta_parametrizacao_ocorrencia_campo_numerico = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo Numérico", tipo_resposta=tipo_resposta_campo_numerico
        )
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create()
    parametrizacao_ocorrencia_1 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual uniforme faltou?",
    )
    parametrizacao_ocorrencia_2 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_campo_numerico,
        titulo="Quantos uniformes faltaram?",
    )

    payload = {
        "data": "07/06/2024",
        "escola": str(escola.uuid),
        "ocorrencias": [
            {
                "grupo": 1,
                "parametrizacao": str(parametrizacao_ocorrencia_1.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": "calça",
            },
            {
                "grupo": 2,
                "parametrizacao": str(parametrizacao_ocorrencia_1.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": "camisa",
            },
            {
                "grupo": 2,
                "parametrizacao": str(parametrizacao_ocorrencia_2.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": 10,
            },
        ],
    }

    response = client.post(
        f"/imr/rascunho-formulario-supervisao/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    instance = FormularioOcorrenciasBase.objects.get(data="2024-06-07")
    assert instance.respostas_campo_texto_simples.count() == 2
    assert (
        instance.respostas_campo_texto_simples.filter(resposta="calça").exists() is True
    )
    assert (
        instance.respostas_campo_texto_simples.filter(
            resposta="camisa", grupo=2
        ).exists()
        is True
    )
    assert instance.respostas_campo_numerico.count() == 1
    assert instance.respostas_campo_numerico.filter(resposta=10).exists() is True


def test_update_formulario_supervisao(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    escola,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    tipo_resposta_campo_simples = tipo_resposta_modelo_factory(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta_parametrizacao_ocorrencia_texto_simples = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
        )
    )

    tipo_resposta_campo_numerico = tipo_resposta_modelo_factory(
        nome="RespostaCampoNumerico"
    )
    tipo_pergunta_parametrizacao_ocorrencia_campo_numerico = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo Numérico", tipo_resposta=tipo_resposta_campo_numerico
        )
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create()
    tipo_ocorrencia_2 = tipo_ocorrencia_factory.create()
    tipo_ocorrencia_3 = tipo_ocorrencia_factory.create()
    parametrizacao_ocorrencia_1 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual uniforme faltou?",
    )
    parametrizacao_ocorrencia_2 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_campo_numerico,
        titulo="Quantos uniformes faltaram?",
    )
    parametrizacao_ocorrencia_3 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_2,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="O que houve?",
    )
    parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_3,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="O que houve?",
    )

    payload = {
        "data": "07/06/2024",
        "escola": str(escola.uuid),
        "ocorrencias": [
            {
                "grupo": 1,
                "parametrizacao": str(parametrizacao_ocorrencia_1.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": "calça",
            },
            {
                "grupo": 2,
                "parametrizacao": str(parametrizacao_ocorrencia_1.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": "camisa",
            },
            {
                "grupo": 2,
                "parametrizacao": str(parametrizacao_ocorrencia_2.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": 10,
            },
        ],
        "ocorrencias_nao_se_aplica": [
            {
                "tipo_ocorrencia": str(tipo_ocorrencia_2.uuid),
                "descricao": "",
            },
        ],
    }

    response = client.post(
        f"/imr/rascunho-formulario-supervisao/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    instance = FormularioOcorrenciasBase.objects.get(data="2024-06-07")
    assert instance.respostas_campo_texto_simples.count() == 2
    assert (
        instance.respostas_campo_texto_simples.filter(resposta="calça").exists() is True
    )
    assert (
        instance.respostas_campo_texto_simples.filter(
            resposta="camisa", grupo=2
        ).exists()
        is True
    )
    assert instance.respostas_campo_numerico.count() == 1
    assert instance.respostas_campo_numerico.filter(resposta=10).exists() is True
    assert instance.respostas_nao_se_aplica.count() == 1

    # ================= TESTANDO UPDATE ==========================

    payload = {
        "uuid": str(instance.formulariosupervisao.uuid),
        "data": "08/06/2024",
        "escola": str(escola.uuid),
        "ocorrencias": [
            {
                "grupo": 1,
                "parametrizacao": str(parametrizacao_ocorrencia_3.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_2.uuid),
                "resposta": "houve algo",
            },
        ],
        "ocorrencias_sim": [str(tipo_ocorrencia_3.uuid)],
        "ocorrencias_nao_se_aplica": [
            {
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "descricao": "não se aplica!!!",
            },
        ],
    }

    response = client.put(
        f"/imr/rascunho-formulario-supervisao/{str(instance.formulariosupervisao.uuid)}/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK

    instance.refresh_from_db()

    assert instance.respostas_campo_texto_simples.count() == 1
    assert (
        instance.respostas_campo_texto_simples.get().parametrizacao
        == parametrizacao_ocorrencia_3
    )

    assert instance.respostas_nao_se_aplica.count() == 1
    assert instance.respostas_nao_se_aplica.get().tipo_ocorrencia == tipo_ocorrencia_1


def test_update_formulario_supervisao_status_erro(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR,
    )

    payload = {"uuid": str(formulario_supervisao.uuid)}

    response = client.put(
        f"/imr/rascunho-formulario-supervisao/{str(formulario_supervisao.uuid)}/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Rascunho já foi enviado e não pode mais ser alterado."
    }


def test_formulario_supervisao_erro_parametrizacao_uuid(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    escola,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao
    tipo_resposta_campo_simples = tipo_resposta_modelo_factory(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta_parametrizacao_ocorrencia_texto_simples = (
        tipo_pergunta_parametrizacao_ocorrencia_factory(
            nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
        )
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create()
    parametrizacao_ocorrencia_1 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual uniforme faltou?",
    )

    uuid_incorreto = uuid.uuid4()

    payload = {
        "data": "07/06/2024",
        "escola": str(escola.uuid),
        "ocorrencias": [
            {
                "grupo": 1,
                "parametrizacao": str(parametrizacao_ocorrencia_1.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": "calça",
            },
            {
                "grupo": 2,
                "parametrizacao": str(parametrizacao_ocorrencia_1.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": "camisa",
            },
            {
                "grupo": 2,
                "parametrizacao": str(uuid_incorreto),
                "tipo_ocorrencia": str(tipo_ocorrencia_1.uuid),
                "resposta": 10,
            },
        ],
    }

    response = client.post(
        f"/imr/rascunho-formulario-supervisao/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": f"ParametrizacaoOcorrencia com o UUID {str(uuid_incorreto)} não foi encontrada"
    }


def test_delete_formulario_supervisao(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario
    )

    response = client.delete(
        f"/imr/rascunho-formulario-supervisao/{formulario_supervisao.uuid}/",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert FormularioSupervisao.objects.count() == 0


def test_delete_formulario_supervisao_403_status_nutrimanifestacao_a_validar(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao = formulario_supervisao_factory.create(
        formulario_base__usuario=usuario,
        status=FormularioSupervisao.workflow_class.NUTRIMANIFESTACAO_A_VALIDAR,
    )

    response = client.delete(
        f"/imr/rascunho-formulario-supervisao/{formulario_supervisao.uuid}/",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você só pode excluir quando o status for EM PREENCHIMENTO."
    }


def test_delete_formulario_supervisao_403_object_permission(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao = formulario_supervisao_factory.create()

    response = client.delete(
        f"/imr/rascunho-formulario-supervisao/{formulario_supervisao.uuid}/",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Você não tem permissão para executar essa ação."
    }
