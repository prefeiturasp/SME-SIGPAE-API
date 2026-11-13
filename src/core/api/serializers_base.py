from __future__ import annotations

from rest_framework import serializers

from ..models import TipoGestao


class TipoGestaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoGestao
        exclude = ("id",)
