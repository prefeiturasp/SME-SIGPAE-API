import json
import uuid
from datetime import date, timedelta
from io import BytesIO

import pytest
from faker import Faker
from freezegun import freeze_time
from pypdf import PdfReader
from rest_framework import status

from sme_sigpae_api.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow
from sme_sigpae_api.recebimento.models import (
    FichaDeRecebimento,
    QuestaoConferencia,
    QuestoesPorProduto,
)

fake = Faker("pt_BR")

pytestmark = pytest.mark.django_db


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
    response_data = response_create.json()
    assert set(response_data.keys()) == {
        "uuid",
        "numero_cronograma",
        "nome_produto",
        "fornecedor",
        "pregao_chamada_publica",
        "data_recebimento",
        "status",
    }
    assert response_data["status"] == "Rascunho"

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

    nova_data_entrega = date.today() + timedelta(days=11)
    payload_ficha_recebimento_rascunho["data_entrega"] = str(nova_data_entrega)
    payload_ficha_recebimento_rascunho["veiculos"].pop()
    payload_ficha_recebimento_rascunho["documentos_recebimento"].pop()
    payload_ficha_recebimento_rascunho["arquivos"].pop()

    response_update = client_autenticado_qualidade.put(
        f"/rascunho-ficha-de-recebimento/{ficha.uuid}/",
        content_type="application/json",
        data=json.dumps(payload_ficha_recebimento_rascunho),
    )

    ficha.refresh_from_db()

    assert response_update.status_code == status.HTTP_200_OK
    update_data = response_update.json()
    assert set(update_data.keys()) == {
        "uuid",
        "numero_cronograma",
        "nome_produto",
        "fornecedor",
        "pregao_chamada_publica",
        "data_recebimento",
        "status",
    }
    assert update_data["status"] == "Rascunho"

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


def test_url_ficha_recebimento_assinada_create_update(
    client_autenticado_qualidade,
    payload_ficha_recebimento,
):
    """Testa a criação e atualização de uma ficha assinada via endpoint principal."""
    response_create = client_autenticado_qualidade.post(
        "/fichas-de-recebimento/",
        content_type="application/json",
        data=json.dumps(payload_ficha_recebimento),
    )

    ficha = FichaDeRecebimento.objects.last()

    assert response_create.status_code == status.HTTP_201_CREATED
    assert ficha is not None
    assert ficha.status == FichaDeRecebimentoWorkflow.ASSINADA
    assert ficha.veiculos.count() == len(payload_ficha_recebimento["veiculos"])
    assert ficha.documentos_recebimento.count() == len(
        payload_ficha_recebimento["documentos_recebimento"]
    )
    assert ficha.arquivos.count() == len(payload_ficha_recebimento["arquivos"])
    assert ficha.questoes_conferencia.count() == len(
        payload_ficha_recebimento["questoes"]
    )
    assert ficha.ocorrencias.count() == len(payload_ficha_recebimento["ocorrencias"])


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


def test_ficha_recebimento_list_filter_status(
    client_autenticado_qualidade, ficha_de_recebimento_factory
):
    """Testa o filtro de status na listagem de fichas de recebimento."""
    ficha_rascunho = ficha_de_recebimento_factory(
        status=FichaDeRecebimentoWorkflow.RASCUNHO
    )
    ficha_assinada = ficha_de_recebimento_factory(
        status=FichaDeRecebimentoWorkflow.ASSINADA
    )

    response = client_autenticado_qualidade.get(
        "/fichas-de-recebimento/", {"status": FichaDeRecebimentoWorkflow.RASCUNHO}
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["uuid"] == str(ficha_rascunho.uuid)
    assert results[0]["status"] == "Rascunho"

    response = client_autenticado_qualidade.get(
        "/fichas-de-recebimento/", {"status": FichaDeRecebimentoWorkflow.ASSINADA}
    )
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["uuid"] == str(ficha_assinada.uuid)
    assert results[0]["status"] == "Assinado CODAE"

    response = client_autenticado_qualidade.get("/fichas-de-recebimento/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 2


@freeze_time("2025-09-09")
def test_gerar_pdf_ficha_recebimento(
    client_autenticado_qualidade, ficha_de_recebimento_factory
):
    """Testa a geração de PDF para uma ficha de recebimento existente."""

    ficha_completa = ficha_de_recebimento_factory(
        status=FichaDeRecebimentoWorkflow.ASSINADA
    )

    response = client_autenticado_qualidade.get(
        f"/fichas-de-recebimento/{ficha_completa.uuid}/gerar-pdf-ficha/"
    )

    cronograma = ficha_completa.etapa.cronograma
    empresa = cronograma.empresa
    ficha_tecnica = cronograma.ficha_tecnica
    etapa = ficha_completa.etapa

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "application/pdf"
    assert (
        f'filename="ficha_recebimento_{cronograma.numero}.pdf"'
        in response["Content-Disposition"]
    )

    pdf_reader = PdfReader(BytesIO(response.content))
    page = pdf_reader.pages[0]
    pdf_text = page.extract_text()

    assert "FICHA DE RECEBIMENTO" in pdf_text

    assert cronograma.numero in pdf_text
    assert cronograma.contrato.numero in pdf_text
    assert cronograma.contrato.ata in pdf_text

    assert f"{empresa.nome_fantasia} - {empresa.razao_social}" in pdf_text

    assert ficha_tecnica.produto.nome in pdf_text
    assert ficha_tecnica.marca.nome in pdf_text

    assert ficha_tecnica.material_embalagem_primaria in pdf_text
    assert ficha_tecnica.sistema_vedacao_embalagem_secundaria in pdf_text


def test_gerar_pdf_ficha_nao_encontrada(client_autenticado_qualidade):
    """Testa a tentativa de gerar PDF para uma ficha que não existe."""
    response = client_autenticado_qualidade.get(
        "/api/v1/fichas-de-recebimento/00000000-0000-0000-0000-000000000000/gerar-pdf-ficha/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_criar_ficha_saldo_zero(
    client_autenticado_qualidade, payload_ficha_recebimento
):
    """Testa a criação de uma ficha com saldo zero."""
    payload_ficha_recebimento.update(
        {
            "lote_fabricante_de_acordo": True,
            "data_fabricacao_de_acordo": True,
            "data_validade_de_acordo": True,
            "numero_lote_armazenagem": "LOTE_ARMAZENAGEM123",
            "numero_paletes": 5,
            "peso_embalagem_primaria_1": "1.5",
            "peso_embalagem_primaria_2": "2.5",
            "peso_embalagem_primaria_3": "3.5",
            "peso_embalagem_primaria_4": "4.5",
            "sistema_vedacao_embalagem_secundaria": "Sistema de vedação",
        }
    )

    response = client_autenticado_qualidade.post(
        "/fichas-de-recebimento/cadastrar-saldo-zero/",
        content_type="application/json",
        data=json.dumps(payload_ficha_recebimento),
    )

    ficha = FichaDeRecebimento.objects.last()

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert set(response_data.keys()) == {
        "uuid",
        "numero_cronograma",
        "nome_produto",
        "fornecedor",
        "pregao_chamada_publica",
        "data_recebimento",
        "status",
    }
    assert response_data["status"] == "Assinado CODAE"

    assert ficha is not None
    assert ficha.lote_fabricante_de_acordo is None
    assert ficha.data_fabricacao_de_acordo is None
    assert ficha.data_validade_de_acordo is None
    assert ficha.numero_lote_armazenagem is None
    assert ficha.sistema_vedacao_embalagem_secundaria is None
    assert ficha.numero_paletes is None
    assert ficha.peso_embalagem_primaria_1 is None
    assert ficha.peso_embalagem_primaria_2 is None
    assert ficha.peso_embalagem_primaria_3 is None
    assert ficha.peso_embalagem_primaria_4 is None


def test_atualizar_ficha_saldo_zero(
    client_autenticado_qualidade,
    ficha_de_recebimento_factory,
    payload_ficha_recebimento,
):
    """Testa a atualização de uma ficha com saldo zero."""
    ficha = ficha_de_recebimento_factory()

    payload = {
        **payload_ficha_recebimento,
        "lote_fabricante_de_acordo": True,
        "data_fabricacao_de_acordo": True,
        "data_validade_de_acordo": True,
        "numero_lote_armazenagem": "LOTE_ARMAZENAGEM123",
        "numero_paletes": 5,
        "peso_embalagem_primaria_1": "1.5",
        "peso_embalagem_primaria_2": "2.5",
        "peso_embalagem_primaria_3": "3.5",
        "peso_embalagem_primaria_4": "4.5",
        "sistema_vedacao_embalagem_secundaria": "Sistema de vedação",
    }

    response = client_autenticado_qualidade.put(
        f"/fichas-de-recebimento/{ficha.uuid}/atualizar-saldo-zero/",
        content_type="application/json",
        data=json.dumps(payload),
    )

    ficha.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert set(response_data.keys()) == {
        "uuid",
        "numero_cronograma",
        "nome_produto",
        "fornecedor",
        "pregao_chamada_publica",
        "data_recebimento",
        "status",
    }
    assert response_data["status"] == "Assinado CODAE"

    assert ficha.lote_fabricante_de_acordo is None
    assert ficha.data_fabricacao_de_acordo is None
    assert ficha.data_validade_de_acordo is None
    assert ficha.numero_lote_armazenagem is None
    assert ficha.sistema_vedacao_embalagem_secundaria is None
    assert ficha.numero_paletes is None
    assert ficha.peso_embalagem_primaria_1 is None
    assert ficha.peso_embalagem_primaria_2 is None
    assert ficha.peso_embalagem_primaria_3 is None
    assert ficha.peso_embalagem_primaria_4 is None


def test_criar_ficha_saldo_zero_campos_opcionais(
    client_autenticado_qualidade, payload_ficha_recebimento
):
    """Testa a criação de uma ficha com saldo zero sem os campos opcionais."""
    campos_opcionais = [
        "lote_fabricante_de_acordo",
        "data_fabricacao_de_acordo",
        "data_validade_de_acordo",
        "numero_lote_armazenagem",
        "numero_paletes",
        "peso_embalagem_primaria_1",
        "peso_embalagem_primaria_2",
        "peso_embalagem_primaria_3",
        "peso_embalagem_primaria_4",
        "sistema_vedacao_embalagem_secundaria",
    ]

    for campo in campos_opcionais:
        if campo in payload_ficha_recebimento:
            payload_ficha_recebimento.pop(campo)

    response = client_autenticado_qualidade.post(
        "/fichas-de-recebimento/cadastrar-saldo-zero/",
        content_type="application/json",
        data=json.dumps(payload_ficha_recebimento),
    )

    ficha = FichaDeRecebimento.objects.last()

    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert set(response_data.keys()) == {
        "uuid",
        "numero_cronograma",
        "nome_produto",
        "fornecedor",
        "pregao_chamada_publica",
        "data_recebimento",
        "status",
    }
    assert response_data["status"] == "Assinado CODAE"

    assert ficha is not None
    assert ficha.uuid == uuid.UUID(response_data["uuid"])
    assert ficha.status == FichaDeRecebimentoWorkflow.ASSINADA
