import datetime

from rest_framework import serializers


def deve_ter_atributos(data, atributos):
    for atributo in atributos:
        if atributo not in data:
            raise serializers.ValidationError(f"deve ter atributo {atributo}")


def atributos_lista_nao_vazios(data, atributos):
    for atributo in atributos:
        if len(data[atributo]) < 1:
            raise serializers.ValidationError(f"atributo {atributo} não pode ser vazio")


def atributos_string_nao_vazios(data, atributos):
    for atributo in atributos:
        if data[atributo] == "":
            raise serializers.ValidationError(f"atributo {atributo} não pode ser vazio")


def masca_data_valida(data):
    try:
        datetime.datetime.strptime(data, "%d/%m/%Y")
        return True
    except ValueError:
        raise serializers.ValidationError(
            "Formato de data inválido, deve ser dd/mm/aaaa"
        )


def somente_digitos(codigo_eol):
    if not "".join([p for p in codigo_eol if p in "0123456789"]) == codigo_eol:
        raise serializers.ValidationError("Deve ter somente dígitos")


class AlunoSerializerValidator(serializers.Serializer):
    codigo_eol = serializers.CharField(max_length=7, validators=[somente_digitos])
    nome = serializers.CharField(max_length=100)
    data_nascimento = serializers.CharField(
        max_length=10, validators=[masca_data_valida]
    )
