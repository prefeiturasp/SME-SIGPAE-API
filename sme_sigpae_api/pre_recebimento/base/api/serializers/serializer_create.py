from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.base.models import UnidadeMedida


class UnidadeMedidaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao", "criado_em")
        read_only_fields = ("uuid", "criado_em")

    def validate_nome(self, value):
        if not value.isupper():
            raise serializers.ValidationError(
                "O campo deve conter apenas letras maiúsculas."
            )
        return value

    def validate_abreviacao(self, value):
        if not value.islower():
            raise serializers.ValidationError(
                "O campo deve conter apenas letras minúsculas."
            )
        return value
