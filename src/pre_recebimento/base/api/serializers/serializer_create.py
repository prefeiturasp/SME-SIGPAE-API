"""Serializers de criação do submódulo base de pré-recebimento."""

from rest_framework import serializers

from src.pre_recebimento.base.models import UnidadeMedida


class UnidadeMedidaCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação/atualização da unidade de medida.

    Valida que o ``nome`` contenha apenas letras maiúsculas e que a
    ``abreviacao`` contenha apenas letras minúsculas.
    """

    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao", "criado_em")
        read_only_fields = ("uuid", "criado_em")

    def validate_nome(self, value):
        """Valida que o nome contém apenas letras maiúsculas."""
        if not value.isupper():
            raise serializers.ValidationError(
                "O campo deve conter apenas letras maiúsculas."
            )
        return value

    def validate_abreviacao(self, value):
        """Valida que a abreviação contém apenas letras minúsculas."""
        if not value.islower():
            raise serializers.ValidationError(
                "O campo deve conter apenas letras minúsculas."
            )
        return value
