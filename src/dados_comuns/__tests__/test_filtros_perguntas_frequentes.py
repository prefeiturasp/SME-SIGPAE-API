import pytest
from model_bakery import baker
from rest_framework import status

from ..models import CategoriaPerguntaFrequente, PerguntaFrequente


UUID_CATEGORIA_ALIMENTACAO = "89ad7865-e0af-41f1-a8d9-ae31fb2948d8"
UUID_CATEGORIA_ABASTECIMENTO = "726e8649-dff5-4679-a0b0-47cbc37164d3"
UUID_PERFIL_QUALIDADE = "56ceac9a-b483-41b8-94ac-43ca3d7c5881"
UUID_PERFIL_FISCALIZADOR = "79ea106f-cb71-4db0-8c53-bf203520a92d"


@pytest.fixture
def dados_perguntas_frequentes():
    categoria_alimentacao = baker.make(
        CategoriaPerguntaFrequente,
        nome="Gestão de Alimentação",
        uuid=UUID_CATEGORIA_ALIMENTACAO,
    )
    categoria_abastecimento = baker.make(
        CategoriaPerguntaFrequente,
        nome="Abastecimento",
        uuid=UUID_CATEGORIA_ABASTECIMENTO,
    )
    perfil_qualidade = baker.make(
        "Perfil",
        nome="QUALIDADE",
        uuid=UUID_PERFIL_QUALIDADE,
        ativo=True,
    )
    perfil_fiscalizador = baker.make(
        "Perfil",
        nome="ORGAO_FISCALIZADOR",
        uuid=UUID_PERFIL_FISCALIZADOR,
        ativo=True,
    )
    pergunta_dieta = baker.make(
        PerguntaFrequente,
        categoria=categoria_alimentacao,
        pergunta="Como solicitar uma dieta especial?",
        todos_os_perfis=False,
    )
    pergunta_cardapio = baker.make(
        PerguntaFrequente,
        categoria=categoria_alimentacao,
        pergunta="Como consultar o cardápio?",
        todos_os_perfis=False,
    )
    pergunta_abastecimento = baker.make(
        PerguntaFrequente,
        categoria=categoria_abastecimento,
        pergunta="Como consultar uma entrega?",
        todos_os_perfis=True,
    )
    pergunta_dieta.perfis.add(perfil_qualidade)
    pergunta_cardapio.perfis.add(perfil_fiscalizador)

    return {
        "pergunta_abastecimento": pergunta_abastecimento,
        "pergunta_cardapio": pergunta_cardapio,
        "pergunta_dieta": pergunta_dieta,
    }


def obter_uuids(response):
    return {item["uuid"] for item in response.json()["results"]}


def test_filtra_perguntas_frequentes_por_parte_do_titulo(
    client_autenticado_coordenador_codae,
    dados_perguntas_frequentes,
):
    response = client_autenticado_coordenador_codae.get(
        "/perguntas-frequentes/",
        {"titulo": "DIETA ESPECIAL"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert obter_uuids(response) == {
        str(dados_perguntas_frequentes["pergunta_dieta"].uuid)
    }


def test_filtra_perguntas_frequentes_por_categoria(
    client_autenticado_coordenador_codae,
    dados_perguntas_frequentes,
):
    response = client_autenticado_coordenador_codae.get(
        "/perguntas-frequentes/",
        {"categoria": UUID_CATEGORIA_ALIMENTACAO},
    )

    assert response.status_code == status.HTTP_200_OK
    assert obter_uuids(response) == {
        str(dados_perguntas_frequentes["pergunta_dieta"].uuid),
        str(dados_perguntas_frequentes["pergunta_cardapio"].uuid),
    }


def test_filtra_perguntas_frequentes_por_um_perfil(
    client_autenticado_coordenador_codae,
    dados_perguntas_frequentes,
):
    response = client_autenticado_coordenador_codae.get(
        "/perguntas-frequentes/",
        {"perfil": UUID_PERFIL_QUALIDADE},
    )

    assert response.status_code == status.HTTP_200_OK
    assert obter_uuids(response) == {
        str(dados_perguntas_frequentes["pergunta_dieta"].uuid)
    }


def test_filtra_perguntas_frequentes_por_multiplos_perfis(
    client_autenticado_coordenador_codae,
    dados_perguntas_frequentes,
):
    response = client_autenticado_coordenador_codae.get(
        "/perguntas-frequentes/",
        {"perfil": f"{UUID_PERFIL_QUALIDADE},{UUID_PERFIL_FISCALIZADOR}"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert obter_uuids(response) == {
        str(dados_perguntas_frequentes["pergunta_dieta"].uuid),
        str(dados_perguntas_frequentes["pergunta_cardapio"].uuid),
    }


def test_filtra_perguntas_frequentes_disponiveis_para_todos_os_perfis(
    client_autenticado_coordenador_codae,
    dados_perguntas_frequentes,
):
    response = client_autenticado_coordenador_codae.get(
        "/perguntas-frequentes/",
        {"perfil": "todos"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert obter_uuids(response) == {
        str(dados_perguntas_frequentes["pergunta_abastecimento"].uuid)
    }


def test_combina_filtros_de_titulo_categoria_e_perfis(
    client_autenticado_coordenador_codae,
    dados_perguntas_frequentes,
):
    response = client_autenticado_coordenador_codae.get(
        "/perguntas-frequentes/",
        {
            "categoria": UUID_CATEGORIA_ALIMENTACAO,
            "perfil": f"{UUID_PERFIL_QUALIDADE},{UUID_PERFIL_FISCALIZADOR}",
            "titulo": "cardápio",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert obter_uuids(response) == {
        str(dados_perguntas_frequentes["pergunta_cardapio"].uuid)
    }


def test_retorna_lista_vazia_quando_filtros_nao_encontram_perguntas(
    client_autenticado_coordenador_codae,
    dados_perguntas_frequentes,
):
    response = client_autenticado_coordenador_codae.get(
        "/perguntas-frequentes/",
        {
            "categoria": UUID_CATEGORIA_ABASTECIMENTO,
            "titulo": "dieta",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0
    assert response.json()["results"] == []
