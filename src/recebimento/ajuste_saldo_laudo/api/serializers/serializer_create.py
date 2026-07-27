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


class AjusteSaldoUpdateSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        nova_quantidade_descontada = validated_data.get("quantidade_descontada")
        if nova_quantidade_descontada is None:
            raise serializers.ValidationError(
                {"quantidade_descontada": "Quantidade a descontar é obrigatória."}
            )

        saldo_atual = calcular_saldo_laudo(instance.documento_recebimento)
        saldo_disponivel = saldo_atual + instance.quantidade_descontada

        if saldo_disponivel - nova_quantidade_descontada < 0:
            raise serializers.ValidationError(
                {"quantidade_descontada": "Saldo após desconto menor que 0"}
            )

        instance.quantidade_descontada = nova_quantidade_descontada
        instance.save()

        return instance

    class Meta:
        model = AjusteSaldo
        fields = ("quantidade_descontada",)
