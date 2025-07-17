from rest_framework import serializers

from sme_sigpae_api.dados_comuns.api.serializers import (
    ContatoSerializer,
)
from sme_sigpae_api.dados_comuns.utils import (
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.qualidade.models import (
    Laboratorio,
    TipoEmbalagemQld,
)


class LaboratorioCreateSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(required=True)
    cnpj = serializers.CharField(required=True)
    cep = serializers.CharField(required=True)
    logradouro = serializers.CharField(required=True)
    numero = serializers.CharField(required=True)
    bairro = serializers.CharField(required=True)
    cidade = serializers.CharField(required=True)
    estado = serializers.CharField(required=True)
    credenciado = serializers.BooleanField(required=True)
    contatos = ContatoSerializer(many=True)

    def cria_contatos(self, contatos, laboratorio):
        for contato_json in contatos:
            contato = ContatoSerializer().create(validated_data=contato_json)
            laboratorio.contatos.add(contato)

    def create(self, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        contatos = validated_data.pop("contatos", [])
        laboratorio = Laboratorio.objects.create(**validated_data)

        self.cria_contatos(contatos, laboratorio)
        return laboratorio

    def update(self, instance, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        contatos = validated_data.pop("contatos", [])

        instance.contatos.all().delete()

        self.cria_contatos(contatos, instance)
        update_instance_from_dict(instance, validated_data, save=True)

        return instance

    class Meta:
        model = Laboratorio
        exclude = ("id",)


class TipoEmbalagemQldCreateSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(required=True)
    abreviacao = serializers.CharField(required=True)

    def create(self, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        validated_data["abreviacao"] = validated_data["abreviacao"].upper()
        embalagem = TipoEmbalagemQld.objects.create(**validated_data)

        return embalagem

    def update(self, instance, validated_data):
        validated_data["nome"] = validated_data["nome"].upper()
        validated_data["abreviacao"] = validated_data["abreviacao"].upper()
        update_instance_from_dict(instance, validated_data, save=True)

        return instance

    class Meta:
        model = TipoEmbalagemQld
        exclude = ("id",)
