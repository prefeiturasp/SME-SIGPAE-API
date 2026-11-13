from __future__ import annotations

from rest_framework import serializers

from ...models import DiretoriaRegional


class DiretoriaRegionalSimplissimaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiretoriaRegional
        fields = (
            "uuid",
            "nome",
            "codigo_eol",
            "iniciais",
            "acesso_modulo_medicao_inicial",
        )


class DiretoriaRegionalLookUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiretoriaRegional
        fields = ("uuid", "iniciais", "nome", "codigo_eol")


class DiretoriaRegionalParaFiltroSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiretoriaRegional
        fields = ("uuid", "nome")
