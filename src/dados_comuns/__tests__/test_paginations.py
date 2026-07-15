from unittest.mock import Mock

from rest_framework.response import Response


def test_tamanho_pagina_padrao(paginacao_historico_dietas):
    paginacao, mock_requisicao = paginacao_historico_dietas
    requisicao = mock_requisicao.get("/")
    requisicao.query_params = {}
    assert paginacao.get_page_size(requisicao) == paginacao.max_page_size


def test_tamanho_pagina_personalizado(paginacao_historico_dietas):
    paginacao, mock_requisicao = paginacao_historico_dietas
    requisicao = mock_requisicao.get("/", {"page_size": "1"})
    requisicao.query_params = {"page_size": "1"}
    assert paginacao.get_page_size(requisicao) == 1


def test_tamanho_pagina_invalido(paginacao_historico_dietas):
    paginacao, mock_requisicao = paginacao_historico_dietas
    requisicao = mock_requisicao.get("/", {"page_size": "invalido"})
    requisicao.query_params = {"page_size": "invalido"}
    assert paginacao.get_page_size(requisicao) == paginacao.max_page_size


def test_resposta_paginada(paginacao_historico_dietas):
    paginacao, _ = paginacao_historico_dietas
    paginacao.request = Mock()
    paginacao.request.GET = {"page_size": "1"}

    paginacao.get_next_link = Mock(return_value="url_proxima_pagina")
    paginacao.get_previous_link = Mock(return_value="url_pagina_anterior")

    paginacao.page = Mock()
    paginacao.page.paginator.count = 10

    dados = [{"id": 1, "nome": "Dieta Teste"}]
    total_dietas = 5
    dados_log = "26/03/2025"

    resposta = paginacao.get_paginated_response(dados, total_dietas, dados_log)

    assert isinstance(resposta, Response)
    assert resposta.data["next"] == "url_proxima_pagina"
    assert resposta.data["previous"] == "url_pagina_anterior"
    assert resposta.data["count"] == 10
    assert resposta.data["page_size"] == 1
    assert resposta.data["total_dietas"] == 5
    assert resposta.data["data"] == dados_log
    assert resposta.data["results"] == dados


def test_tamanho_pagina_padrao_ao_nao_enviar_page_size(paginacao_historico_dietas):
    paginacao, mock_requisicao = paginacao_historico_dietas
    requisicao = mock_requisicao.get("/")
    requisicao.query_params = {}
    assert paginacao.get_page_size(requisicao) == 10


def test_tamanho_pagina_none_ao_enviar_page_size_none(paginacao_historico_dietas):
    paginacao, mock_requisicao = paginacao_historico_dietas
    requisicao = mock_requisicao.get("/")
    requisicao.query_params = {"page_size": None}

    assert paginacao.get_page_size(requisicao) == 10


def test_resposta_paginada_com_page_size_padrao(paginacao_historico_dietas):
    paginacao, _ = paginacao_historico_dietas
    paginacao.request = Mock()
    paginacao.request.GET = {}

    paginacao.get_next_link = Mock(return_value="url_proxima_pagina")
    paginacao.get_previous_link = Mock(return_value="url_pagina_anterior")

    paginacao.page = Mock()
    paginacao.page.paginator.count = 10

    dados = [{"id": 1, "nome": "Dieta Teste"}]
    total_dietas = 5
    dados_log = "26/03/2025"

    resposta = paginacao.get_paginated_response(dados, total_dietas, dados_log)

    assert isinstance(resposta, Response)
    assert resposta.data["next"] == "url_proxima_pagina"
    assert resposta.data["previous"] == "url_pagina_anterior"
    assert resposta.data["count"] == 10
    assert resposta.data["page_size"] == 10
    assert resposta.data["total_dietas"] == 5
    assert resposta.data["data"] == dados_log
    assert resposta.data["results"] == dados
