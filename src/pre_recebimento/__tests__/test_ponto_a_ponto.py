from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
    FichaTecnicaSimplesSerializer,
)
from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto


def test_ficha_tecnica_ponto_a_ponto_independente_da_categoria():
    categorias = (
        FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
        FichaTecnicaDoProduto.CATEGORIA_FLV,
    )

    for categoria in categorias:
        ficha_tecnica = FichaTecnicaDoProduto(
            categoria=categoria,
            tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
        )

        assert ficha_tecnica.ponto_a_ponto is True


def test_cronograma_identifica_ponto_a_ponto_pela_ficha_tecnica():
    ficha_ponto_a_ponto = FichaTecnicaDoProduto(
        categoria=FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
    )
    ficha_armazenavel = FichaTecnicaDoProduto(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.ARMAZEM,
    )

    cronograma_ponto_a_ponto = Cronograma(
        ficha_tecnica=ficha_ponto_a_ponto,
    )
    cronograma_armazenavel = Cronograma(
        ficha_tecnica=ficha_armazenavel,
    )
    cronograma_sem_ficha = Cronograma(
        ficha_tecnica=None,
    )

    assert cronograma_ponto_a_ponto.ponto_a_ponto is True
    assert cronograma_armazenavel.ponto_a_ponto is False
    assert cronograma_sem_ficha.ponto_a_ponto is False


def test_ficha_tecnica_simples_serializer_expoe_ponto_a_ponto():
    ficha_tecnica = FichaTecnicaDoProduto(
        categoria=FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
    )

    dados = FichaTecnicaSimplesSerializer(ficha_tecnica).data

    assert dados["ponto_a_ponto"] is True
    assert "flv_ponto_a_ponto" not in dados