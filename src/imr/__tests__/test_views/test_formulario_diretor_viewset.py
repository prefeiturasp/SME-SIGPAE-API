import json
import uuid
from datetime import date
from types import SimpleNamespace

import pytest
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from src.dados_comuns.constants import StringsValidationErrors
from src.imr.models import FormularioDiretor, FormularioOcorrenciasBase, TipoOcorrencia

pytestmark = pytest.mark.django_db

URL_LISTAGEM = "/imr/formulario-diretor/"


@freeze_time("2024-06-10")
def test_create_formulario_diretor(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )

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
        "/imr/formulario-diretor/",
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

    solicitacao_medicao_inicial.refresh_from_db()
    assert solicitacao_medicao_inicial.com_ocorrencias is True


@freeze_time("2024-06-10")
def test_create_formulario_diretor_sem_ocorrencias_mantem_com_ocorrencias_false(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )
    payload = {
        "datas": ["07/06/2024"],
        "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
        "ocorrencias": [],
    }

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    solicitacao_medicao_inicial.refresh_from_db()
    assert solicitacao_medicao_inicial.com_ocorrencias is False


@freeze_time("2024-06-10")
def test_create_formulario_diretor_erro_parametrizacao_uuid(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )

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
        "/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": f"ParametrizacaoOcorrencia com o UUID {str(uuid_incorreto)} não foi encontrada"
    }


@freeze_time("2024-06-10")
def test_create_formulario_diretor_data_fora_da_competencia(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )

    tipo_resposta_campo_simples = tipo_resposta_modelo_factory(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta = tipo_pergunta_parametrizacao_ocorrencia_factory(
        nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
    )
    tipo_ocorrencia = tipo_ocorrencia_factory.create()
    parametrizacao_ocorrencia = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia,
        tipo_pergunta=tipo_pergunta,
        titulo="Qual uniforme faltou?",
    )

    payload = {
        "datas": ["07/05/2024", "08/06/2024"],
        "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
        "ocorrencias": [
            {
                "grupo": 1,
                "parametrizacao": str(parametrizacao_ocorrencia.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia.uuid),
                "resposta": "calça",
            },
        ],
    }

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "datas": [StringsValidationErrors.DATA_FORA_DA_COMPETENCIA_DA_MEDICAO.value]
    }
    assert FormularioOcorrenciasBase.objects.count() == 0


@freeze_time("2024-06-10")
def test_create_formulario_diretor_data_formato_invalido(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )

    payload = {
        "datas": ["2024-06-07"],
        "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
        "ocorrencias": [],
    }

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "datas": [StringsValidationErrors.DATA_EM_FORMATO_INVALIDO.value]
    }


@pytest.mark.parametrize("data_futura", ["10/06/2024", "20/06/2024"])
@freeze_time("2024-06-10")
def test_create_formulario_diretor_data_de_hoje_ou_futura(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    data_futura,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )

    payload = {
        "datas": [data_futura],
        "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
        "ocorrencias": [],
    }

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "datas": [StringsValidationErrors.DATA_DE_OCORRENCIA_FUTURA.value]
    }
    assert FormularioOcorrenciasBase.objects.count() == 0


@freeze_time("2024-06-10")
def test_create_formulario_diretor_data_duplicada(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )

    tipo_resposta_campo_simples = tipo_resposta_modelo_factory(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta = tipo_pergunta_parametrizacao_ocorrencia_factory(
        nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
    )
    tipo_ocorrencia = tipo_ocorrencia_factory.create()
    parametrizacao = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia,
        tipo_pergunta=tipo_pergunta,
        titulo="Qual uniforme faltou?",
    )

    payload = {
        "datas": ["07/06/2024"],
        "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
        "ocorrencias": [
            {
                "grupo": 1,
                "parametrizacao": str(parametrizacao.uuid),
                "tipo_ocorrencia": str(tipo_ocorrencia.uuid),
                "resposta": "calça",
            },
        ],
    }

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "datas": [StringsValidationErrors.DATA_DE_OCORRENCIA_DUPLICADA.value]
    }
    assert FormularioOcorrenciasBase.objects.count() == 1


@freeze_time("2024-06-10")
def test_create_formulario_diretor_data_igual_tipo_diferente_permitida(
    client_autenticado_diretor_escola,
    escola,
    solicitacao_medicao_inicial_factory,
    tipo_resposta_modelo_factory,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    solicitacao_medicao_inicial = solicitacao_medicao_inicial_factory(
        escola=escola, mes="06", ano="2024"
    )

    tipo_resposta_campo_simples = tipo_resposta_modelo_factory(
        nome="RespostaCampoTextoSimples"
    )
    tipo_pergunta = tipo_pergunta_parametrizacao_ocorrencia_factory(
        nome="Campo de Texto Simples", tipo_resposta=tipo_resposta_campo_simples
    )

    tipo_ocorrencia_1 = tipo_ocorrencia_factory.create()
    parametrizacao_1 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_1,
        tipo_pergunta=tipo_pergunta,
        titulo="Qual uniforme faltou?",
    )
    tipo_ocorrencia_2 = tipo_ocorrencia_factory.create()
    parametrizacao_2 = parametrizacao_ocorrencia_factory(
        tipo_ocorrencia=tipo_ocorrencia_2,
        tipo_pergunta=tipo_pergunta,
        titulo="Qual uniforme faltou?",
    )

    def montar_payload(tipo_ocorrencia, parametrizacao):
        return {
            "datas": ["07/06/2024"],
            "solicitacao_medicao_inicial": str(solicitacao_medicao_inicial.uuid),
            "ocorrencias": [
                {
                    "grupo": 1,
                    "parametrizacao": str(parametrizacao.uuid),
                    "tipo_ocorrencia": str(tipo_ocorrencia.uuid),
                    "resposta": "calça",
                },
            ],
        }

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(montar_payload(tipo_ocorrencia_1, parametrizacao_1)),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client_autenticado_diretor_escola["client"].post(
        "/imr/formulario-diretor/",
        data=json.dumps(montar_payload(tipo_ocorrencia_2, parametrizacao_2)),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert FormularioOcorrenciasBase.objects.count() == 2


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
        "/imr/formulario-diretor/tipos-ocorrencias/?edital_uuid=",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": ["O valor “” não é um UUID válido"]}


def test_listagem_retorna_dados_da_ocorrencia_e_ordena_respostas(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    resposta_campo_numerico_factory,
):
    contexto = contexto_listagem_diretor
    contexto.parametrizacao.posicao = 2
    contexto.parametrizacao.save(update_fields=["posicao"])
    formulario = criar_ocorrencia_diretor()
    resposta_texto = formulario.formulario_base.respostas_campo_texto_simples.get()
    pergunta = tipo_pergunta_parametrizacao_ocorrencia_factory.create(
        nome="Campo Numérico",
        tipo_resposta__nome="RespostaCampoNumerico",
    )
    parametrizacao = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=contexto.tipo,
        tipo_pergunta=pergunta,
        titulo="Quantos itens faltaram?",
        posicao=1,
    )
    resposta_numerica = resposta_campo_numerico_factory.create(
        formulario_base=formulario.formulario_base,
        parametrizacao=parametrizacao,
        grupo=1,
        resposta=2.0,
    )

    resposta = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)},
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "uuid": str(formulario.uuid),
                "data": "10/09/2026",
                "categoria": {
                    "uuid": str(contexto.tipo.categoria.uuid),
                    "nome": "FUNCIONÁRIOS",
                    "posicao": 1,
                    "gera_notificacao": False,
                },
                "tipo_ocorrencia": str(contexto.tipo.uuid),
                "titulo": "UNIFORME DOS MANIPULADORES",
                "descricao": "Funcionários utilizavam uniforme completo?",
                "grupo": 1,
                "respostas": [
                    {
                        "uuid": str(resposta_numerica.uuid),
                        "parametrizacao": str(parametrizacao.uuid),
                        "titulo": "Quantos itens faltaram?",
                        "posicao": 1,
                        "resposta": "2.0",
                    },
                    {
                        "uuid": str(resposta_texto.uuid),
                        "parametrizacao": str(contexto.parametrizacao.uuid),
                        "titulo": "Qual item do uniforme faltou?",
                        "posicao": 2,
                        "resposta": "Touca",
                    },
                ],
            }
        ],
    }


@pytest.mark.parametrize("data", [date(2026, 10, 10), date(2025, 9, 10)])
def test_listagem_nao_inclui_ocorrencias_de_outra_medicao(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    solicitacao_medicao_inicial_factory,
    data,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    outra_medicao = solicitacao_medicao_inicial_factory.create(
        escola=contexto.escola,
        mes=f"{data.month:02d}",
        ano=str(data.year),
    )
    criar_ocorrencia_diretor(data=data, medicao=outra_medicao)

    resposta = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)},
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["count"] == 1
    assert [linha["uuid"] for linha in resposta.json()["results"]] == [
        str(formulario.uuid)
    ]


@pytest.mark.parametrize("data", [date(2026, 10, 10), date(2025, 9, 10)])
def test_listagem_ignora_data_fora_do_periodo_da_medicao(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    data,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    criar_ocorrencia_diretor(data=data)

    resposta = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)},
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["count"] == 1
    assert resposta.json()["results"][0]["uuid"] == str(formulario.uuid)


def test_listagem_nao_inclui_ocorrencias_de_outra_escola(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    escola_factory,
    solicitacao_medicao_inicial_factory,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    outra_medicao = solicitacao_medicao_inicial_factory.create(
        escola=escola_factory.create(), mes="09", ano="2026"
    )
    criar_ocorrencia_diretor(medicao=outra_medicao)

    resposta = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)},
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["count"] == 1
    assert resposta.json()["results"][0]["uuid"] == str(formulario.uuid)


def test_listagem_retorna_vazio_para_medicao_sem_ocorrencias(
    contexto_listagem_diretor,
):
    contexto = contexto_listagem_diretor

    resposta = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)},
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


def test_listagem_retorna_404_para_medicao_inexistente(
    client_autenticado_diretor_escola,
):
    resposta = client_autenticado_diretor_escola["client"].get(
        URL_LISTAGEM, {"solicitacao_medicao_inicial": str(uuid.uuid4())}
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_listagem_retorna_404_para_medicao_de_outra_escola(
    contexto_listagem_diretor,
    escola_factory,
    solicitacao_medicao_inicial_factory,
):
    contexto = contexto_listagem_diretor
    outra_medicao = solicitacao_medicao_inicial_factory.create(
        escola=escola_factory.create(), mes="09", ano="2026"
    )

    resposta = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(outra_medicao.uuid)},
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    assert "results" not in resposta.json()


def test_listagem_exige_autenticacao(client):
    resposta = client.get(
        URL_LISTAGEM, {"solicitacao_medicao_inicial": str(uuid.uuid4())}
    )

    assert resposta.status_code == status.HTTP_401_UNAUTHORIZED


def test_listagem_rejeita_perfil_sem_permissao(client_autenticado_cogestor_dre):
    cliente, _ = client_autenticado_cogestor_dre

    resposta = cliente.get(
        URL_LISTAGEM, {"solicitacao_medicao_inicial": str(uuid.uuid4())}
    )

    assert resposta.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("tamanho_pagina", [None, 6], ids=["padrao", "personalizado"])
def test_listagem_pagina_grupos_sem_perder_ou_repetir_resultados(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    resposta_campo_texto_simples_factory,
    tamanho_pagina,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    for grupo in range(2, 12):
        resposta_campo_texto_simples_factory.create(
            formulario_base=formulario.formulario_base,
            parametrizacao=contexto.parametrizacao,
            grupo=grupo,
            resposta=f"Item do grupo {grupo}",
        )
    parametros = {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)}
    if tamanho_pagina is not None:
        parametros["page_size"] = tamanho_pagina

    resposta = contexto.cliente.get(URL_LISTAGEM, parametros)

    assert resposta.status_code == status.HTTP_200_OK
    primeira_pagina = resposta.json()
    assert primeira_pagina["count"] == 11
    assert len(primeira_pagina["results"]) == (tamanho_pagina or 10)
    assert primeira_pagina["next"] is not None
    assert primeira_pagina["previous"] is None

    resposta = contexto.cliente.get(primeira_pagina["next"])

    assert resposta.status_code == status.HTTP_200_OK
    segunda_pagina = resposta.json()
    assert segunda_pagina["count"] == 11
    assert len(segunda_pagina["results"]) == 11 - (tamanho_pagina or 10)
    assert segunda_pagina["next"] is None
    assert segunda_pagina["previous"] is not None
    grupos_primeira_pagina = {linha["grupo"] for linha in primeira_pagina["results"]}
    grupos_segunda_pagina = {linha["grupo"] for linha in segunda_pagina["results"]}
    assert grupos_primeira_pagina.isdisjoint(grupos_segunda_pagina)
    assert grupos_primeira_pagina | grupos_segunda_pagina == set(range(1, 12))


@freeze_time("2026-10-19")
def test_listagem_inclui_nova_ocorrencia_junto_das_anteriores(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    criar_ocorrencia_diretor()
    dados = {
        "datas": ["11/09/2026"],
        "solicitacao_medicao_inicial": str(contexto.medicao.uuid),
        "tipo_ocorrencia": str(contexto.tipo.uuid),
        "ocorrencias": [
            {
                "parametrizacao": str(contexto.parametrizacao.uuid),
                "grupo": 1,
                "resposta": "Avental",
            }
        ],
    }

    resposta_cadastro = contexto.cliente.post(
        URL_LISTAGEM,
        data=json.dumps(dados),
        content_type="application/json",
    )

    assert resposta_cadastro.status_code == status.HTTP_201_CREATED

    resposta = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)},
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["count"] == 2
    assert [linha["data"] for linha in resposta.json()["results"]] == [
        "11/09/2026",
        "10/09/2026",
    ]
    assert [
        linha["respostas"][0]["resposta"] for linha in resposta.json()["results"]
    ] == ["Avental", "Touca"]


def test_listagem_rejeita_consulta_sem_medicao(
    client_autenticado_diretor_escola,
):
    resposta = client_autenticado_diretor_escola["client"].get(URL_LISTAGEM)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "solicitacao_medicao_inicial" in resposta.json()


def montar_url_ocorrencia(formulario, tipo_ocorrencia, grupo=1):
    return (
        f"{URL_LISTAGEM}{formulario.uuid}/"
        f"?tipo_ocorrencia={tipo_ocorrencia.uuid}&grupo={grupo}"
    )


def test_retrieve_ocorrencia_diretor_retorna_dados_para_edicao(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    resposta_texto = formulario.formulario_base.respostas_campo_texto_simples.get()

    resposta = contexto.cliente.get(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json() == {
        "uuid": str(formulario.uuid),
        "solicitacao_medicao_inicial": str(contexto.medicao.uuid),
        "data": "10/09/2026",
        "categoria": {
            "uuid": str(contexto.tipo.categoria.uuid),
            "nome": "FUNCIONÁRIOS",
            "posicao": 1,
            "gera_notificacao": False,
        },
        "tipo_ocorrencia": str(contexto.tipo.uuid),
        "titulo": "UNIFORME DOS MANIPULADORES",
        "descricao": "Funcionários utilizavam uniforme completo?",
        "grupo": 1,
        "respostas": [
            {
                "uuid": str(resposta_texto.uuid),
                "parametrizacao": str(contexto.parametrizacao.uuid),
                "titulo": "Qual item do uniforme faltou?",
                "posicao": 1,
                "resposta": "Touca",
            }
        ],
    }


def test_retrieve_ocorrencia_diretor_retorna_uuid_dos_seletores(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    tipo_pergunta_parametrizacao_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
    utensilio_cozinha_factory,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    utensilio = utensilio_cozinha_factory.create()
    pergunta = tipo_pergunta_parametrizacao_ocorrencia_factory.create(
        nome="Seletor de Utensílios de Cozinha",
        tipo_resposta__nome="RespostaUtensilioCozinha",
    )
    parametrizacao = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=contexto.tipo,
        tipo_pergunta=pergunta,
        titulo="Qual utensílio?",
        posicao=2,
    )
    resposta_utensilio = baker.make(
        "imr.RespostaUtensilioCozinha",
        formulario_base=formulario.formulario_base,
        parametrizacao=parametrizacao,
        grupo=1,
        resposta=utensilio,
    )

    resposta = contexto.cliente.get(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["respostas"][1] == {
        "uuid": str(resposta_utensilio.uuid),
        "parametrizacao": str(parametrizacao.uuid),
        "titulo": "Qual utensílio?",
        "posicao": 2,
        "resposta": str(utensilio.uuid),
    }


def test_retrieve_ocorrencia_retorna_403_para_escola_de_outra_escola(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    escola_factory,
    solicitacao_medicao_inicial_factory,
):
    contexto = contexto_listagem_diretor
    outra_medicao = solicitacao_medicao_inicial_factory.create(
        escola=escola_factory.create(), mes="09", ano="2026"
    )
    formulario = criar_ocorrencia_diretor(medicao=outra_medicao)

    resposta = contexto.cliente.get(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.json() == {"detail": StringsValidationErrors.PERMISSAO_NEGADA.value}


def test_retrieve_ocorrencia_retorna_404_para_grupo_inexistente(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()

    resposta = contexto.cliente.get(
        montar_url_ocorrencia(formulario, contexto.tipo, grupo=2)
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_ocorrencia_retorna_404_para_formulario_inexistente(
    contexto_listagem_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = SimpleNamespace(uuid=uuid.uuid4())

    resposta = contexto.cliente.get(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_ocorrencia_exige_parametros_obrigatorios(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()

    resposta = contexto.cliente.get(f"{URL_LISTAGEM}{formulario.uuid}/")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "tipo_ocorrencia" in resposta.json()
    assert "grupo" in resposta.json()


def test_retrieve_ocorrencia_rejeita_perfil_sem_permissao(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    client_autenticado_cogestor_dre,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    cliente, _ = client_autenticado_cogestor_dre

    resposta = cliente.get(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_403_FORBIDDEN


def montar_corpo_atualizacao(
    contexto,
    data="10/09/2026",
    resposta="Avental",
    grupo=1,
    parametrizacao=None,
):
    return {
        "tipo_ocorrencia": str(contexto.tipo.uuid),
        "grupo": grupo,
        "data": data,
        "ocorrencias": [
            {
                "parametrizacao": str((parametrizacao or contexto.parametrizacao).uuid),
                "grupo": grupo,
                "resposta": resposta,
            }
        ],
    }


@freeze_time("2026-10-19")
def test_update_ocorrencia_diretor_atualiza_data_e_resposta(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(
            montar_corpo_atualizacao(contexto, data="11/09/2026", resposta="Avental")
        ),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["data"] == "11/09/2026"
    assert resposta.json()["respostas"] == [
        {
            "uuid": resposta.json()["respostas"][0]["uuid"],
            "parametrizacao": str(contexto.parametrizacao.uuid),
            "titulo": "Qual item do uniforme faltou?",
            "posicao": 1,
            "resposta": "Avental",
        }
    ]

    formulario.formulario_base.refresh_from_db()
    assert formulario.formulario_base.data == date(2026, 9, 11)

    respostas = formulario.formulario_base.respostas_campo_texto_simples.all()
    assert respostas.count() == 1
    assert respostas.first().resposta == "Avental"


@freeze_time("2026-10-19")
def test_update_ocorrencia_diretor_preserva_outros_grupos(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    resposta_campo_texto_simples_factory,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    resposta_campo_texto_simples_factory.create(
        formulario_base=formulario.formulario_base,
        parametrizacao=contexto.parametrizacao,
        grupo=2,
        resposta="Camisa",
    )

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto, resposta="Avental")),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_200_OK

    respostas = formulario.formulario_base.respostas_campo_texto_simples.all()
    assert respostas.count() == 2
    assert respostas.filter(grupo=1, resposta="Avental").exists()
    assert respostas.filter(grupo=2, resposta="Camisa").exists()


@freeze_time("2026-10-19")
def test_update_ocorrencia_diretor_mantem_data_original_sem_duplicidade(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto)),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.json()["data"] == "10/09/2026"


@freeze_time("2026-10-19")
def test_update_ocorrencia_diretor_rejeita_data_de_outra_competencia(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto, data="10/08/2026")),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.json() == {
        "data": [StringsValidationErrors.DATA_FORA_DA_COMPETENCIA_DA_MEDICAO.value]
    }


@freeze_time("2026-10-19")
def test_update_ocorrencia_diretor_rejeita_data_de_ocorrencia_duplicada(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    criar_ocorrencia_diretor(data=date(2026, 9, 11))

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto, data="11/09/2026")),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.json() == {
        "data": [StringsValidationErrors.DATA_DE_OCORRENCIA_DUPLICADA.value]
    }


@freeze_time("2026-10-19")
def test_update_ocorrencia_diretor_rejeita_parametrizacao_de_outro_tipo(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    tipo_ocorrencia_factory,
    parametrizacao_ocorrencia_factory,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    outro_tipo = tipo_ocorrencia_factory.create(
        edital=contexto.tipo.edital,
        categoria=contexto.tipo.categoria,
        perfis=["DIRETOR"],
        status=True,
    )
    outra_parametrizacao = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia=outro_tipo
    )

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(
            montar_corpo_atualizacao(contexto, parametrizacao=outra_parametrizacao)
        ),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "ocorrencias" in resposta.json()


def test_update_ocorrencia_diretor_retorna_403_para_escola_de_outra_escola(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    escola_factory,
    solicitacao_medicao_inicial_factory,
):
    contexto = contexto_listagem_diretor
    outra_medicao = solicitacao_medicao_inicial_factory.create(
        escola=escola_factory.create(), mes="09", ano="2026"
    )
    formulario = criar_ocorrencia_diretor(medicao=outra_medicao)

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto)),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.json() == {"detail": StringsValidationErrors.PERMISSAO_NEGADA.value}


def test_update_ocorrencia_diretor_retorna_404_para_grupo_inexistente(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto, grupo=2)),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_update_ocorrencia_diretor_retorna_404_para_formulario_inexistente(
    contexto_listagem_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = SimpleNamespace(uuid=uuid.uuid4())

    resposta = contexto.cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto)),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_update_ocorrencia_diretor_rejeita_perfil_sem_permissao(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    client_autenticado_cogestor_dre,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    cliente, _ = client_autenticado_cogestor_dre

    resposta = cliente.put(
        f"{URL_LISTAGEM}{formulario.uuid}/",
        data=json.dumps(montar_corpo_atualizacao(contexto)),
        content_type="application/json",
    )

    assert resposta.status_code == status.HTTP_403_FORBIDDEN


def test_delete_ocorrencia_diretor_remove_formulario_sem_outras_respostas(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    formulario_base_id = formulario.formulario_base_id
    contexto.medicao.com_ocorrencias = True
    contexto.medicao.save(update_fields=["com_ocorrencias"])

    resposta = contexto.cliente.delete(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_204_NO_CONTENT
    assert FormularioDiretor.objects.filter(pk=formulario.pk).exists() is False
    assert (
        FormularioOcorrenciasBase.objects.filter(pk=formulario_base_id).exists()
        is False
    )

    contexto.medicao.refresh_from_db()
    assert contexto.medicao.com_ocorrencias is False

    resposta_listagem = contexto.cliente.get(
        URL_LISTAGEM,
        {"solicitacao_medicao_inicial": str(contexto.medicao.uuid)},
    )
    assert resposta_listagem.status_code == status.HTTP_200_OK
    assert resposta_listagem.json()["count"] == 0


def test_delete_ocorrencia_diretor_preserva_outros_grupos(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    resposta_campo_texto_simples_factory,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    contexto.medicao.com_ocorrencias = True
    contexto.medicao.save(update_fields=["com_ocorrencias"])
    resposta_campo_texto_simples_factory.create(
        formulario_base=formulario.formulario_base,
        parametrizacao=contexto.parametrizacao,
        grupo=2,
        resposta="Camisa",
    )

    resposta = contexto.cliente.delete(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_204_NO_CONTENT

    formulario.refresh_from_db()
    respostas = formulario.formulario_base.respostas_campo_texto_simples.all()
    assert respostas.count() == 1
    assert respostas.first().grupo == 2
    assert respostas.first().resposta == "Camisa"

    contexto.medicao.refresh_from_db()
    assert contexto.medicao.com_ocorrencias is True


def test_delete_ocorrencia_diretor_mantem_com_ocorrencias_com_outra_ocorrencia(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    contexto.medicao.com_ocorrencias = True
    contexto.medicao.save(update_fields=["com_ocorrencias"])
    criar_ocorrencia_diretor(data=date(2026, 9, 11))

    resposta = contexto.cliente.delete(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_204_NO_CONTENT

    contexto.medicao.refresh_from_db()
    assert contexto.medicao.com_ocorrencias is True


def test_delete_ocorrencia_diretor_retorna_403_para_escola_de_outra_escola(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    escola_factory,
    solicitacao_medicao_inicial_factory,
):
    contexto = contexto_listagem_diretor
    outra_medicao = solicitacao_medicao_inicial_factory.create(
        escola=escola_factory.create(), mes="09", ano="2026"
    )
    formulario = criar_ocorrencia_diretor(medicao=outra_medicao)

    resposta = contexto.cliente.delete(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
    assert resposta.json() == {"detail": StringsValidationErrors.PERMISSAO_NEGADA.value}


def test_delete_ocorrencia_diretor_retorna_404_para_grupo_inexistente(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()

    resposta = contexto.cliente.delete(
        montar_url_ocorrencia(formulario, contexto.tipo, grupo=2)
    )

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_delete_ocorrencia_diretor_retorna_404_para_formulario_inexistente(
    contexto_listagem_diretor,
):
    contexto = contexto_listagem_diretor
    formulario = SimpleNamespace(uuid=uuid.uuid4())

    resposta = contexto.cliente.delete(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_delete_ocorrencia_diretor_rejeita_perfil_sem_permissao(
    contexto_listagem_diretor,
    criar_ocorrencia_diretor,
    client_autenticado_cogestor_dre,
):
    contexto = contexto_listagem_diretor
    formulario = criar_ocorrencia_diretor()
    cliente, _ = client_autenticado_cogestor_dre

    resposta = cliente.delete(montar_url_ocorrencia(formulario, contexto.tipo))

    assert resposta.status_code == status.HTTP_403_FORBIDDEN
