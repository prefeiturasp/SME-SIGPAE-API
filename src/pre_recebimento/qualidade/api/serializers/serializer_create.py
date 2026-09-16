"""Serializers de criação do submódulo de qualidade."""

from rest_framework import serializers

from src.dados_comuns.api.serializers import (
    ContatoSerializer,
)
from src.dados_comuns.utils import (
    update_instance_from_dict,
)
from src.pre_recebimento.qualidade.models import (
    Laboratorio,
    TipoEmbalagemQld,
)


class LaboratorioCreateSerializer(serializers.ModelSerializer):
    """Serializer de criação/atualização do laboratório.

    Exige os dados cadastrais (``nome``, ``cnpj``, ``cep``,
    ``logradouro``, ``numero``, ``bairro``, ``cidade``, ``estado`` e
    ``credenciado``) e a lista de ``contatos``. O ``nome`` é normalizado
    em letras maiúsculas. Na atualização, os contatos existentes são
    substituídos pelos novos.
    """

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
        """Cria e associa os contatos ao laboratório.

        Args:
            contatos: Lista de dados de contato (dicts).
            laboratorio: Instância do laboratório.
        """
        for contato_json in contatos:
            contato = ContatoSerializer().create(validated_data=contato_json)
            laboratorio.contatos.add(contato)

    def create(self, validated_data):
        """Cria o laboratório normalizando o nome em maiúsculas.

        Args:
            validated_data: Dados validados do laboratório e contatos.

        Returns:
            Laboratório criado com os contatos associados.
        """
        validated_data["nome"] = validated_data["nome"].upper()
        contatos = validated_data.pop("contatos", [])
        laboratorio = Laboratorio.objects.create(**validated_data)

        self.cria_contatos(contatos, laboratorio)
        return laboratorio

    def update(self, instance, validated_data):
        """Atualiza o laboratório substituindo os contatos.

        Args:
            instance: Laboratório existente.
            validated_data: Dados validados do laboratório e contatos.

        Returns:
            Laboratório atualizado.
        """
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
    """Serializer de criação/atualização do tipo de embalagem.

    Exige ``nome`` e ``abreviacao``, ambos normalizados em letras
    maiúsculas na criação e na atualização.
    """

    nome = serializers.CharField(required=True)
    abreviacao = serializers.CharField(required=True)

    def create(self, validated_data):
        """Cria o tipo de embalagem normalizando nome e abreviação.

        Args:
            validated_data: Dados validados do tipo de embalagem.

        Returns:
            Tipo de embalagem criado.
        """
        validated_data["nome"] = validated_data["nome"].upper()
        validated_data["abreviacao"] = validated_data["abreviacao"].upper()
        embalagem = TipoEmbalagemQld.objects.create(**validated_data)

        return embalagem

    def update(self, instance, validated_data):
        """Atualiza o tipo de embalagem normalizando nome e abreviação.

        Args:
            instance: Tipo de embalagem existente.
            validated_data: Dados validados do tipo de embalagem.

        Returns:
            Tipo de embalagem atualizado.
        """
        validated_data["nome"] = validated_data["nome"].upper()
        validated_data["abreviacao"] = validated_data["abreviacao"].upper()
        update_instance_from_dict(instance, validated_data, save=True)

        return instance

    class Meta:
        model = TipoEmbalagemQld
        exclude = ("id",)
