from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.base.models import UnidadeMedida


class UnidadeMedidaSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao")
        read_only_fields = ("uuid", "nome", "abreviacao")


class UnidadeMedidaSerialzer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao", "criado_em")
        read_only_fields = ("uuid", "nome", "abreviacao", "criado_em")
