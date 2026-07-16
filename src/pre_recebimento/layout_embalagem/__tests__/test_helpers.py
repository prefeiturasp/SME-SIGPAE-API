import base64
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from src.pre_recebimento.layout_embalagem.api.helpers import (
    cria_tipos_de_embalagens,
)
from src.pre_recebimento.layout_embalagem.models import (
    ImagemDoTipoDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)

pytestmark = pytest.mark.django_db

# Um pixel PNG branco, em base64
_PIXEL_BASE64 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def _make_imagem_dict(nome):
    """Retorna um dict representando uma imagem no formato usado pelo serializer."""
    return {
        "nome": nome,
        "arquivo": _PIXEL_BASE64,
    }


def test_cria_tipos_com_nome_longo(layout_de_embalagem):
    """
    Testa o helper com nome de imagem maior que 100 caracteres,
    cenário que causava o erro 'value too long for type character varying(100)'.
    """
    long_name = "x" * 200
    dados = [
        {
            "tipo_embalagem": "PRIMARIA",
            "imagens_do_tipo_de_embalagem": [
                _make_imagem_dict(long_name),
            ],
        }
    ]
    cria_tipos_de_embalagens(dados, layout_de_embalagem)

    tipo = TipoDeEmbalagemDeLayout.objects.get(layout_de_embalagem=layout_de_embalagem)
    imagem = tipo.imagens.first()
    assert imagem is not None
    assert imagem.nome == long_name
    assert len(imagem.nome) == 200


def test_cria_tipos_com_nomes_variados(layout_de_embalagem):
    """
    Testa o helper com múltiplas imagens com nomes de tamanhos diferentes,
    incluindo nomes longos (regressão + novos limites).
    """
    dados = [
        {
            "tipo_embalagem": "PRIMARIA",
            "imagens_do_tipo_de_embalagem": [
                _make_imagem_dict("foto_normal.jpg"),
                _make_imagem_dict("a" * 150),   # > 100 chars
                _make_imagem_dict("b" * 400),   # > 100 e < 500
            ],
        }
    ]
    cria_tipos_de_embalagens(dados, layout_de_embalagem)

    tipo = TipoDeEmbalagemDeLayout.objects.get(layout_de_embalagem=layout_de_embalagem)
    imagens = tipo.imagens.all().order_by("nome")
    assert imagens.count() == 3
    assert imagens[0].nome == "a" * 150
    assert imagens[1].nome == "b" * 400
    assert imagens[2].nome == "foto_normal.jpg"


def test_cria_tipos_sem_imagens(layout_de_embalagem):
    """
    Testa o helper sem passar imagens — não deve quebrar.
    """
    dados = [
        {
            "tipo_embalagem": "SECUNDARIA",
        }
    ]
    cria_tipos_de_embalagens(dados, layout_de_embalagem)

    tipo = TipoDeEmbalagemDeLayout.objects.get(layout_de_embalagem=layout_de_embalagem)
    assert tipo.imagens.count() == 0


def test_cria_tipos_com_imagens_sem_nome(layout_de_embalagem):
    """
    Testa o helper com imagem sem 'nome' — deve usar '' por padrão.
    """
    dados = [
        {
            "tipo_embalagem": "TERCIARIA",
            "imagens_do_tipo_de_embalagem": [
                {"arquivo": _PIXEL_BASE64},  # sem 'nome'
            ],
        }
    ]
    cria_tipos_de_embalagens(dados, layout_de_embalagem)

    tipo = TipoDeEmbalagemDeLayout.objects.get(layout_de_embalagem=layout_de_embalagem)
    imagem = tipo.imagens.first()
    assert imagem is not None
    assert imagem.nome == ""


def test_cria_tipos_com_imagens_com_nome_vazio(layout_de_embalagem):
    """
    Testa o helper com 'nome': '' — também deve funcionar.
    """
    dados = [
        {
            "tipo_embalagem": "PRIMARIA",
            "imagens_do_tipo_de_embalagem": [
                _make_imagem_dict(""),
            ],
        }
    ]
    cria_tipos_de_embalagens(dados, layout_de_embalagem)

    tipo = TipoDeEmbalagemDeLayout.objects.get(layout_de_embalagem=layout_de_embalagem)
    imagem = tipo.imagens.first()
    assert imagem is not None
    assert imagem.nome == ""


def test_cria_tipos_com_nome_no_limite_exato(layout_de_embalagem):
    """
    Testa o helper com nome de exatamente 500 caracteres (limite máximo do campo).
    """
    long_name = "z" * 500
    dados = [
        {
            "tipo_embalagem": "PRIMARIA",
            "imagens_do_tipo_de_embalagem": [
                _make_imagem_dict(long_name),
            ],
        }
    ]
    cria_tipos_de_embalagens(dados, layout_de_embalagem)

    tipo = TipoDeEmbalagemDeLayout.objects.get(layout_de_embalagem=layout_de_embalagem)
    imagem = tipo.imagens.first()
    assert imagem is not None
    assert imagem.nome == long_name
    assert len(imagem.nome) == 500


def test_cria_multiplos_tipos_com_nomes_longo(layout_de_embalagem):
    """
    Testa o helper com múltiplos tipos de embalagem, cada um com imagens
    de nomes longos — verifica que todos são criados corretamente.
    """
    dados = [
        {
            "tipo_embalagem": "PRIMARIA",
            "imagens_do_tipo_de_embalagem": [
                _make_imagem_dict("m" * 200),
            ],
        },
        {
            "tipo_embalagem": "SECUNDARIA",
            "imagens_do_tipo_de_embalagem": [
                _make_imagem_dict("n" * 300),
            ],
        },
        {
            "tipo_embalagem": "TERCIARIA",
            "imagens_do_tipo_de_embalagem": [
                _make_imagem_dict("o" * 450),
            ],
        },
    ]
    cria_tipos_de_embalagens(dados, layout_de_embalagem)

    tipos = TipoDeEmbalagemDeLayout.objects.filter(
        layout_de_embalagem=layout_de_embalagem
    ).order_by("tipo_embalagem")
    assert tipos.count() == 3

    assert tipos[0].imagens.first().nome == "m" * 200
    assert tipos[1].imagens.first().nome == "n" * 300
    assert tipos[2].imagens.first().nome == "o" * 450
