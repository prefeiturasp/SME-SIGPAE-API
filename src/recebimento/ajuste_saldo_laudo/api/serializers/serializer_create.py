from rest_framework import serializers

from src.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    calcular_saldo_laudo,
)
from src.pre_recebimento.documento_recebimento.models import DocumentoDeRecebimento
from src.recebimento.ajuste_saldo_laudo.models import AjusteSaldo


class AjusteSaldoCreateSerializer(serializers.ModelSerializer):
    documento_recebimento = serializers.UUIDField()

    def create(self, validated_data):
        documento_field = validated_data.get("documento_recebimento")
        documento = DocumentoDeRecebimento.objects.get(uuid=documento_field)

        saldo_atual = calcular_saldo_laudo(documento)

        quantidade_descontada = validated_data.get("quantidade_descontada")
        if quantidade_descontada is None:
            raise serializers.ValidationError(
                {"quantidade_descontada": "Quantidade a descontar é obrigatória."}
            )

        if quantidade_descontada > saldo_atual:
            raise serializers.ValidationError(
                {
                    "quantidade_descontada": "Quantidade descontada maior que saldo disponível."
                }
            )

        ajuste_saldo = AjusteSaldo.objects.create(
            documento_recebimento=documento, quantidade_descontada=quantidade_descontada
        )

        return ajuste_saldo

    class Meta:
        model = AjusteSaldo
        exclude = ("id",)
