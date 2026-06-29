from rest_framework import serializers

from src.recebimento.ajuste_saldo_laudo.models import AjusteSaldo


class AjusteSaldoListagemSerializer(serializers.ModelSerializer):
    numero_cronograma = serializers.SerializerMethodField()
    produto = serializers.SerializerMethodField()
    fornecedor = serializers.SerializerMethodField()
    numero_laudo = serializers.SerializerMethodField()
    unidade_medida = serializers.SerializerMethodField()

    def get_numero_cronograma(self, obj):
        return obj.documento_recebimento.cronograma.numero

    def get_produto(self, obj):
        return obj.documento_recebimento.cronograma.ficha_tecnica.produto.nome

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
