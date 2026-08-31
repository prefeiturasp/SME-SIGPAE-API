"""Serializers de leitura do submódulo de qualidade."""

from rest_framework import serializers

from src.dados_comuns.api.serializers import ContatoSimplesSerializer
from src.pre_recebimento.qualidade.models import (
    Laboratorio,
    TipoEmbalagemQld,
)


class TipoEmbalagemQldSerializer(serializers.ModelSerializer):
    """Serializer completo do tipo de embalagem (qualidade).

    Expõe todos os campos do modelo, exceto ``id``. Usado nas listagens e
    detalhes do viewset.
    """

    class Meta:
        model = TipoEmbalagemQld
        exclude = ("id",)


class TipoEmbalagemQldSimplesSerializer(serializers.ModelSerializer):
    """Serializer simples do tipo de embalagem (qualidade).

    Expõe apenas ``uuid``, ``nome`` e ``abreviacao``, para uso em
    seletores.
    """

    class Meta:
        model = TipoEmbalagemQld
        fields = ("uuid", "nome", "abreviacao")


class LaboratorioSerializer(serializers.ModelSerializer):
    """Serializer completo do laboratório.

    Expõe todos os campos do modelo, exceto ``id``, incluindo a lista de
    ``contatos`` serializada com ``ContatoSimplesSerializer``.
    """

    contatos = ContatoSimplesSerializer(many=True)

    class Meta:
        model = Laboratorio
        exclude = ("id",)


class LaboratorioSimplesFiltroSerializer(serializers.ModelSerializer):
    """Serializer de laboratório para filtros.

    Expõe apenas ``nome`` e ``cnpj``, ambos somente leitura. Usado no
    endpoint ``lista-laboratorios``.
    """

    class Meta:
        model = Laboratorio
        fields = ("nome", "cnpj")
        read_only_fields = ("nome", "cnpj")


class LaboratorioCredenciadoSimplesSerializer(serializers.ModelSerializer):
    """Serializer simples do laboratório credenciado.

    Expõe apenas ``uuid`` e ``nome``, ambos somente leitura. Usado no
    endpoint ``lista-laboratorios-credenciados``.
    """

    class Meta:
        model = Laboratorio
        fields = ("uuid", "nome")
        read_only_fields = ("uuid", "nome")
