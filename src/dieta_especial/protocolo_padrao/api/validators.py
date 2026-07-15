from rest_framework import serializers


def edital_ja_existe_protocolo(editais, quantidade_editais_enviados=1):
    if len(editais) > 0 and quantidade_editais_enviados > 1:
        str_editais = ", ".join(str(edital["numero"]) for edital in editais)
        raise serializers.ValidationError(
            f"Já existe um protocolo padrão com esse nome para os editais: {str_editais}."
        )
    raise serializers.ValidationError("Já existe um protocolo padrão com esse nome.")
