"""Serializers de leitura do submódulo base de pré-recebimento."""

from rest_framework import serializers

from src.pre_recebimento.base.models import UnidadeMedida


class UnidadeMedidaSimplesSerializer(serializers.ModelSerializer):
    """Serializer simples da unidade de medida.

    Expõe apenas ``uuid``, ``nome`` e ``abreviacao``, todos somente
    leitura. Usado no endpoint ``lista-nomes-abreviacoes`` para popular
    seletores.
    """

    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao")
        read_only_fields = ("uuid", "nome", "abreviacao")


class UnidadeMedidaSerialzer(serializers.ModelSerializer):
    """Serializer de leitura completo da unidade de medida.

    Expõe ``uuid``, ``nome``, ``abreviacao`` e ``criado_em``, todos
    somente leitura. Usado nas listagens e detalhes do viewset.
    """

    class Meta:
        model = UnidadeMedida
        fields = ("uuid", "nome", "abreviacao", "criado_em")
        read_only_fields = ("uuid", "nome", "abreviacao", "criado_em")
