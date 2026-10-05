from unittest.mock import Mock

import httpx

from src.dados_comuns.http_client import executar_chamada


def test_executar_chamada_repassa_resposta_sem_erro():
    client = Mock()
    response = httpx.Response(200, request=httpx.Request("get", "https://api/recurso"))
    client.get.return_value = response

    result = executar_chamada(client, "get", "https://api/recurso")

    assert result is response


def test_executar_chamada_retorna_resposta_quando_http_status_error():
    client = Mock()
    response = httpx.Response(404, request=httpx.Request("get", "https://api/recurso"))
    client.get.side_effect = httpx.HTTPStatusError(
        "404", request=response.request, response=response
    )

    result = executar_chamada(client, "get", "https://api/recurso")

    assert result is response


def test_executar_chamada_retorna_404_sem_levantar_erro():
    client = Mock()
    response = httpx.Response(404, request=httpx.Request("get", "https://api/recurso"))
    client.get.return_value = response

    result = executar_chamada(client, "get", "https://api/recurso")

    assert result is response
