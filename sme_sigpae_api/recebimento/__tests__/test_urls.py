import json
from datetime import date, timedelta

from faker import Faker
from rest_framework import status

from sme_sigpae_api.recebimento.models import (
    FichaDeRecebimento,
    QuestaoConferencia,
    QuestoesPorProduto,
)
from sme_sigpae_api.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow

fake = Faker("pt_BR")


def test_url_questoes_conferencia_list(
    client_autenticado_qualidade,
    questao_conferencia_factory,
):
    questoes_criadas = questao_conferencia_factory.create_batch(
        size=10,
        tipo_questao=[
            QuestaoConferencia.TIPO_QUESTAO_PRIMARIA,
            QuestaoConferencia.TIPO_QUESTAO_SECUNDARIA,
        ],
        pergunta_obrigatoria=True,
    ) + questao_conferencia_factory.create_batch(
        size=10,
        tipo_questao=[
            QuestaoConferencia.TIPO_QUESTAO_PRIMARIA,
            QuestaoConferencia.TIPO_QUESTAO_SECUNDARIA,
        ],
        posicao=None,
    )

    response = client_autenticado_qualidade.get("/questoes-conferencia/")
    questoes_primarias = response.json()["results"]["primarias"]
    questoes_secundarias = response.json()["results"]["secundarias"]
    total_questoes = QuestaoConferencia.objects.count()

    assert response.status_code == status.HTTP_200_OK
    assert total_questoes == len(questoes_criadas)
    for questoes in [questoes_primarias, questoes_secundarias]:
        assert _questoes_ordenadas(questoes)


def _questoes_ordenadas(questoes):
    return all(
        questoes[i].get("posicao") <= questoes[i + 1].get("posicao")
        for i in range(len(questoes) - 1)
        if questoes[i].get("posicao") and questoes[i + 1].get("posicao")
    )


def test_url_questoes_conferencia_lista_simples(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get(
        "/questoes-conferencia/lista-simples-questoes/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_questoes_por_produto_create(
    client_autenticado_qualidade,
    payload_create_questoes_por_produto,
):
    response = client_autenticado_qualidade.post(
        "/questoes-por-produto/",
        content_type="application/json",
        data=json.dumps(payload_create_questoes_por_produto),
    )

    questoes_por_produto = QuestoesPorProduto.objects.first()

    assert response.status_code == status.HTTP_201_CREATED
    assert questoes_por_produto is not None
    assert questoes_por_produto.questoes_primarias.count() == len(
        payload_create_questoes_por_produto["questoes_primarias"]
    )
    assert questoes_por_produto.questoes_secundarias.count() == len(
        payload_create_questoes_por_produto["questoes_secundarias"]
    )


def test_url_questoes_por_produto_list(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get("/questoes-por-produto/")
    assert response.status_code == status.HTTP_200_OK
    json = response.json()
    assert "count" in json
    assert "next" in json
    assert "previous" in json


def test_url_questoes_por_produto_retrieve(
    client_autenticado_qualidade,
    questoes_por_produto_factory,
):
    questoes_por_produto = questoes_por_produto_factory()

    response = client_autenticado_qualidade.get(
        f"/questoes-por-produto/{questoes_por_produto.uuid}/"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["ficha_tecnica"]["uuid"] == str(
        questoes_por_produto.ficha_tecnica.uuid
    )
    assert (
        len(response.json()["questoes_primarias"])
        == questoes_por_produto.questoes_primarias.count()
    )
    assert (
        len(response.json()["questoes_secundarias"])
        == questoes_por_produto.questoes_secundarias.count()
    )


def test_url_questoes_por_produto_update(
    client_autenticado_qualidade,
    questoes_por_produto_factory,
    payload_update_questoes_por_produto,
):
    questoes_por_produto = questoes_por_produto_factory()

    response = client_autenticado_qualidade.patch(
        f"/questoes-por-produto/{questoes_por_produto.uuid}/",
        content_type="application/json",
        data=json.dumps(payload_update_questoes_por_produto),
    )

    questoes_por_produto.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert (
        len(payload_update_questoes_por_produto["questoes_primarias"])
        == questoes_por_produto.questoes_primarias.count()
    )
    assert (
        len(payload_update_questoes_por_produto["questoes_secundarias"])
        == questoes_por_produto.questoes_secundarias.count()
    )


def test_url_ficha_recebimento_rascunho_create_update(
    client_autenticado_qualidade,
    payload_ficha_recebimento_rascunho,
):
    response_create = client_autenticado_qualidade.post(
        "/rascunho-ficha-de-recebimento/",
        content_type="application/json",
        data=json.dumps(payload_ficha_recebimento_rascunho),
    )

    ficha = FichaDeRecebimento.objects.last()

    assert response_create.status_code == status.HTTP_201_CREATED
    assert ficha is not None
    assert ficha.veiculos.count() == len(payload_ficha_recebimento_rascunho["veiculos"])
    assert ficha.documentos_recebimento.count() == len(
        payload_ficha_recebimento_rascunho["documentos_recebimento"]
    )
    assert ficha.arquivos.count() == len(payload_ficha_recebimento_rascunho["arquivos"])
    assert ficha.questoes_conferencia.count() == len(
        payload_ficha_recebimento_rascunho["questoes"]
    )
    assert ficha.ocorrencias.count() == len(
        payload_ficha_recebimento_rascunho["ocorrencias"]
    )
    response_data = response_create.json()
    assert len(response_data["questoes_conferencia"]) == 1
    assert "ocorrencias" in response_data
    assert len(response_data["ocorrencias"]) == 2

    nova_data_entrega = date.today() + timedelta(days=11)
    payload_ficha_recebimento_rascunho["data_entrega"] = str(nova_data_entrega)
    payload_ficha_recebimento_rascunho["veiculos"].pop()
    payload_ficha_recebimento_rascunho["documentos_recebimento"].pop()
    payload_ficha_recebimento_rascunho["arquivos"].pop()

    response_update = client_autenticado_qualidade.put(
        f'/rascunho-ficha-de-recebimento/{response_create.json()["uuid"]}/',
        content_type="application/json",
        data=json.dumps(payload_ficha_recebimento_rascunho),
    )
    ficha.refresh_from_db()

    assert response_update.status_code == status.HTTP_200_OK
    assert response_update.json()["data_entrega"] == nova_data_entrega.strftime(
        "%d/%m/%Y"
    )
    assert ficha.veiculos.count() == len(payload_ficha_recebimento_rascunho["veiculos"])
    assert ficha.documentos_recebimento.count() == len(
        payload_ficha_recebimento_rascunho["documentos_recebimento"]
    )
    assert ficha.arquivos.count() == len(payload_ficha_recebimento_rascunho["arquivos"])
    assert ficha.questoes_conferencia.count() == len(
        payload_ficha_recebimento_rascunho["questoes"]
    )
    assert ficha.ocorrencias.count() == len(
        payload_ficha_recebimento_rascunho["ocorrencias"]
    )
    response_data = response_update.json()
    assert len(response_data["questoes_conferencia"]) == 1
    assert "ocorrencias" in response_data
    assert len(response_data["ocorrencias"]) == 2


def test_url_busca_questoes_cronograma(
    client_autenticado_qualidade, cronograma_completo
):
    response = client_autenticado_qualidade.get(
        f"/questoes-por-produto/busca-questoes-cronograma/?cronograma_uuid={cronograma_completo.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    resposta = response.json()
    assert "uuid" in resposta
    assert "questoes_primarias" in resposta
    assert "questoes_secundarias" in resposta
    assert "ficha_tecnica" not in resposta


def test_url_busca_questoes_cronograma_nao_encontrado(
    client_autenticado_qualidade,
):
    response = client_autenticado_qualidade.get(
        "/questoes-por-produto/busca-questoes-cronograma/?cronograma_uuid=7c200bb9-032a-4ffe-be6d-b687d06cee2b"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Cronograma não encontrado."


def test_url_busca_questoes_cronograma_uuid_invalido(
    client_autenticado_qualidade,
):
    response = client_autenticado_qualidade.get(
        "/questoes-por-produto/busca-questoes-cronograma/?cronograma_uuid=7c200bb9-032a-4ffe-be6d-b687d06cee2bAa"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "UUID inválido."


def test_url_busca_questoes_cronograma_sem_questoes_por_produto(
    client_autenticado_qualidade, cronograma
):
    response = client_autenticado_qualidade.get(
        f"/questoes-por-produto/busca-questoes-cronograma/?cronograma_uuid={cronograma.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data is None


def test_ficha_recebimento_create_created(
    client_autenticado_qualidade, payload_ficha_recebimento
):
    """Testa a criação de uma ficha de recebimento via POST."""
    response = client_autenticado_qualidade.post(
        "/fichas-de-recebimento/",
        content_type="application/json",
        data=json.dumps(payload_ficha_recebimento),
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert FichaDeRecebimento.objects.count() == 1
    assert "uuid" in response.data

    ficha = FichaDeRecebimento.objects.first()
    assert ficha.veiculos.count() > 0
    assert ficha.arquivos.count() > 0
    assert ficha.questoes_conferencia.count() > 0


def test_ficha_recebimento_create_bad_request(
    client_autenticado_qualidade, payload_ficha_recebimento
):
    """Testa a tentativa de criar uma ficha sem campos obrigatórios."""
    payload = payload_ficha_recebimento.copy()
    del payload["data_entrega"]

    response = client_autenticado_qualidade.post(
        "/fichas-de-recebimento/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "data_entrega" in response.data


def test_ficha_recebimento_list_filter_status(client_autenticado_qualidade, ficha_de_recebimento_factory):
    """Testa o filtro de status na listagem de fichas de recebimento."""
    ficha_rascunho = ficha_de_recebimento_factory(status=FichaDeRecebimentoWorkflow.RASCUNHO)
    ficha_assinada = ficha_de_recebimento_factory(status=FichaDeRecebimentoWorkflow.ASSINADA)
    
    response = client_autenticado_qualidade.get(
        "/fichas-de-recebimento/",
        {"status": FichaDeRecebimentoWorkflow.RASCUNHO}
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["uuid"] == str(ficha_rascunho.uuid)
    assert results[0]["status"] == "Rascunho"
    
    response = client_autenticado_qualidade.get(
        "/fichas-de-recebimento/",
        {"status": FichaDeRecebimentoWorkflow.ASSINADA}
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["uuid"] == str(ficha_assinada.uuid)
    assert results[0]["status"] == "Assinada"
    
    response = client_autenticado_qualidade.get("/fichas-de-recebimento/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 2
