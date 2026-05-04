import json
import uuid

import pytest
from rest_framework import status

from src.imr.models import FormularioOcorrenciasBase, TipoOcorrencia

pytestmark = pytest.mark.django_db


def test_create_formulario_diretor(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(escola=escola)

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
        "datas": ["07/06/2024", "08/06/2024"],
        "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
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

    response = client_autenticado_diretor_escola["client"].post(
        f"/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["solicitacao_medicao_inicial"] == str(solicitacao_medicao_inicial.uuid)

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

    instance = FormularioOcorrenciasBase.objects.get(data="2024-06-08")
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


def test_create_formulario_diretor_erro_parametrizacao_uuid(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(escola=escola)

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
        "datas": ["07/06/2024", "08/06/2024"],
        "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
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

    response = client_autenticado_diretor_escola["client"].post(
        f"/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": f"ParametrizacaoOcorrencia com o UUID {str(uuid_incorreto)} não foi encontrada"
    }


def test_formulario_diretor_get_tipos_ocorrencias(
    client_autenticado_diretor_escola,
    edital_factory,
    categoria_ocorrencia_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    edital = edital_factory.create(numero="78/SME/2016")

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

    categoria = categoria_ocorrencia_factory.create(
        posicao=1,
        nome="FUNCIONÁRIOS",
        perfis=[TipoOcorrencia.DIRETOR],
    )
    categoria_2 = categoria_ocorrencia_factory.create(
        posicao=2,
        nome="RECEBIMENTO DE ALIMENTOS",
        perfis=[TipoOcorrencia.SUPERVISAO],
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create(
        posicao=1,
        titulo="UNIFORME DOS MANIPULADORES",
        descricao="Funcionários utilizavam uniforme completo? Se NÃO, detalhar qual item do uniforme faltou, o que "
        "estava utilizando em substituição aos itens previstos e nome completo do(s) funcionário(s).",
        penalidade__edital=edital,
        penalidade__numero_clausula="10.42",
        perfis=[TipoOcorrencia.DIRETOR],
        categoria=categoria,
        edital=edital,
    )
    parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_texto_simples,
        titulo="Qual uniforme faltou?",
    )
    parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta_parametrizacao_ocorrencia_campo_numerico,
        titulo="Quantos uniformes faltaram?",
    )

    response = client_autenticado_diretor_escola["client"].get(
        f"/imr/formulario-diretor/tipos-ocorrencias/?edital_uuid={edital.uuid}",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK

    tipos_ocorrencia = response.json()

    assert len(tipos_ocorrencia) == 1
    assert (
        any(
            tipo_ocorrencia
            for tipo_ocorrencia in tipos_ocorrencia
            if tipo_ocorrencia["categoria"]["nome"] == categoria.nome
        )
        is True
    )
    tipo_ocorrencia = next(
        tipo_ocorrencia
        for tipo_ocorrencia in tipos_ocorrencia
        if tipo_ocorrencia["categoria"]["nome"] == categoria.nome
    )
    assert len(tipo_ocorrencia["parametrizacoes"]) == 2

    assert (
        any(
            tipo_ocorrencia
            for tipo_ocorrencia in tipos_ocorrencia
            if tipo_ocorrencia["categoria"]["nome"] == categoria_2.nome
        )
        is False
    )


def test_formulario_diretor_get_tipos_ocorrencias_edital_does_not_exist_error(
    client_autenticado_diretor_escola,
):
    uuid_invalido = uuid.uuid4()
    response = client_autenticado_diretor_escola["client"].get(
        f"/imr/formulario-diretor/tipos-ocorrencias/?edital_uuid={uuid_invalido}",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Edital do tipo IMR com o UUID informado não foi encontrado."
    }


def test_formulario_diretor_get_tipos_ocorrencias_validation_error(
    client_autenticado_diretor_escola,
):
    response = client_autenticado_diretor_escola["client"].get(
        f"/imr/formulario-diretor/tipos-ocorrencias/?edital_uuid=",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": ["O valor “” não é um UUID válido"]}
