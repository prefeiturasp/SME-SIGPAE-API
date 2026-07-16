import pytest
from django.db import models

from src.pre_recebimento.layout_embalagem.models import ImagemDoTipoDeEmbalagem

pytestmark = pytest.mark.django_db


def test_campo_nome_max_length_500():
    """Verifica que o campo `nome` foi alterado para max_length=500."""
    field = ImagemDoTipoDeEmbalagem._meta.get_field("nome")
    assert field.max_length == 500, (
        f"Esperado max_length=500, obtido {field.max_length}"
    )
    assert isinstance(field, models.CharField)


def test_cria_imagem_com_nome_maior_que_100_caracteres(layout_de_embalagem):
    """
    Testa o cenário original do erro: criar ImagemDoTipoDeEmbalagem
    com nome > 100 caracteres deve funcionar após o fix.
    """
    long_name = "A" * 150  # 150 chars — maior que o antigo limite de 100
    tipo = layout_de_embalagem.tipos_de_embalagens.create(
        tipo_embalagem="PRIMARIA",
    )
    imagem = ImagemDoTipoDeEmbalagem.objects.create(
        tipo_de_embalagem=tipo,
        nome=long_name,
    )
    assert imagem.nome == long_name
    assert len(imagem.nome) == 150


def test_cria_imagem_com_nome_no_limite_de_500_caracteres(layout_de_embalagem):
    """Testa o boundary: nome com exatamente 500 caracteres."""
    long_name = "B" * 500
    tipo = layout_de_embalagem.tipos_de_embalagens.create(
        tipo_embalagem="SECUNDARIA",
    )
    imagem = ImagemDoTipoDeEmbalagem.objects.create(
        tipo_de_embalagem=tipo,
        nome=long_name,
    )
    assert imagem.nome == long_name
    assert len(imagem.nome) == 500


def test_cria_imagem_com_nome_vazio(layout_de_embalagem):
    """Testa que nome vazio é aceito (blank=True)."""
    tipo = layout_de_embalagem.tipos_de_embalagens.create(
        tipo_embalagem="TERCIARIA",
    )
    imagem = ImagemDoTipoDeEmbalagem.objects.create(
        tipo_de_embalagem=tipo,
        nome="",
    )
    assert imagem.nome == ""


def test_cria_imagem_com_nome_curto_regressao(layout_de_embalagem):
    """Teste de regressão: nomes curtos continuam funcionando."""
    tipo = layout_de_embalagem.tipos_de_embalagens.create(
        tipo_embalagem="PRIMARIA",
    )
    imagem = ImagemDoTipoDeEmbalagem.objects.create(
        tipo_de_embalagem=tipo,
        nome="foto_embalagem.jpg",
    )
    assert imagem.nome == "foto_embalagem.jpg"


