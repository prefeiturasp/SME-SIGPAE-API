import pytest
from model_bakery import baker

from src.recebimento.ajuste_saldo_laudo.api.serializers.serializers import (
    AjusteSaldoListagemSerializer,
)

pytestmark = pytest.mark.django_db


class TestAjusteSaldoListagemSerializer:
    def test_serializer_campos(self, ajuste_saldo):
        serializer = AjusteSaldoListagemSerializer(ajuste_saldo)
        data = serializer.data

        assert "uuid" in data
        assert "produto" in data
        assert "fornecedor" in data
        assert "numero_laudo" in data
        assert "quantidade_descontada" in data
        assert "unidade_medida" in data

    def test_serializer_valores(self, ajuste_saldo):
        serializer = AjusteSaldoListagemSerializer(ajuste_saldo)
        data = serializer.data

        assert data["uuid"] == str(ajuste_saldo.uuid)
        assert (
            data["produto"]
            == ajuste_saldo.documento_recebimento.cronograma.ficha_tecnica.produto.nome
        )
        assert (
            data["fornecedor"]
            == ajuste_saldo.documento_recebimento.cronograma.empresa.nome_fantasia
        )
        assert data["numero_laudo"] == ajuste_saldo.documento_recebimento.numero_laudo
        assert (
            data["unidade_medida"]
            == ajuste_saldo.documento_recebimento.unidade_medida.abreviacao
        )
