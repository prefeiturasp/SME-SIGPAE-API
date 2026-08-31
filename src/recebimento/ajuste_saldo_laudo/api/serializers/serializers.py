"""Serializers de leitura do submódulo de ajuste de saldo do laudo."""

from rest_framework import serializers

from src.recebimento.ajuste_saldo_laudo.models import AjusteSaldo


class AjusteSaldoDetalharSerializer(serializers.ModelSerializer):
    """Serializer de detalhe do ajuste de saldo.

    Expõe o número do cronograma, o número do laudo, a unidade de medida e
    a quantidade descontada, derivados do documento de recebimento.
    """

    numero_cronograma = serializers.SerializerMethodField()
    numero_laudo = serializers.SerializerMethodField()
    unidade_medida = serializers.SerializerMethodField()

    def get_numero_cronograma(self, obj):
        return obj.documento_recebimento.cronograma.numero

    def get_numero_laudo(self, obj):
        return obj.documento_recebimento.numero_laudo

    def get_unidade_medida(self, obj):
        return obj.documento_recebimento.unidade_medida.abreviacao

    class Meta:
        model = AjusteSaldo
        fields = [
            "uuid",
            "numero_cronograma",
            "numero_laudo",
            "unidade_medida",
            "quantidade_descontada",
        ]


class AjusteSaldoListagemSerializer(serializers.ModelSerializer):
    """Serializer de listagem do ajuste de saldo.

    Expõe o número do cronograma, produto, fornecedor, número do laudo,
    unidade de medida e a quantidade descontada, todos somente leitura.
    """

    numero_cronograma = serializers.SerializerMethodField()
    produto = serializers.SerializerMethodField()
    fornecedor = serializers.SerializerMethodField()
    numero_laudo = serializers.SerializerMethodField()
    unidade_medida = serializers.SerializerMethodField()

    def get_numero_cronograma(self, obj):
        return obj.documento_recebimento.cronograma.numero

    def get_produto(self, obj):
        cronograma = obj.documento_recebimento.cronograma
        if cronograma.ficha_tecnica and cronograma.ficha_tecnica.produto:
            return cronograma.ficha_tecnica.produto.nome
        return None

    def get_fornecedor(self, obj):
        return obj.documento_recebimento.cronograma.empresa.nome_fantasia

    def get_numero_laudo(self, obj):
        return obj.documento_recebimento.numero_laudo

    def get_unidade_medida(self, obj):
        return obj.documento_recebimento.unidade_medida.abreviacao

    class Meta:
        model = AjusteSaldo
        fields = [
            "uuid",
            "numero_cronograma",
            "produto",
            "fornecedor",
            "numero_laudo",
            "quantidade_descontada",
            "unidade_medida",
        ]
        read_only_fields = fields
