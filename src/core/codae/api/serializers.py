from __future__ import annotations

from rest_framework import serializers

from ...models import Codae


class CODAESerializer(serializers.ModelSerializer):
    quantidade_alunos = serializers.IntegerField()

    class Meta:
        model = Codae
        fields = "__all__"
