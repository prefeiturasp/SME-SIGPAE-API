from __future__ import annotations

from rest_framework import serializers

from ...models import Subprefeitura


class SubprefeituraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subprefeitura
        exclude = ("id",)


class SubprefeituraSerializerSimples(serializers.ModelSerializer):
    class Meta:
        model = Subprefeitura
        fields = ("codigo_eol", "nome")
