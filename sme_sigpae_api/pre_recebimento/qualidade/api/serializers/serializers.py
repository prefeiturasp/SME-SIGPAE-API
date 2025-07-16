from rest_framework import serializers

from sme_sigpae_api.dados_comuns.api.serializers import ContatoSimplesSerializer
from sme_sigpae_api.pre_recebimento.qualidade.models import (
    Laboratorio,
    TipoEmbalagemQld,
)


class TipoEmbalagemQldSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEmbalagemQld
        exclude = ("id",)


class TipoEmbalagemQldSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEmbalagemQld
        fields = ("uuid", "nome", "abreviacao")


class LaboratorioSerializer(serializers.ModelSerializer):
    contatos = ContatoSimplesSerializer(many=True)

    class Meta:
        model = Laboratorio
        exclude = ("id",)


class LaboratorioSimplesFiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorio
        fields = ("nome", "cnpj")
        read_only_fields = ("nome", "cnpj")


class LaboratorioCredenciadoSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratorio
        fields = ("uuid", "nome")
        read_only_fields = ("uuid", "nome")
