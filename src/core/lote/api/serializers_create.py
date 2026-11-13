from __future__ import annotations

from rest_framework import serializers

from ...models import DiretoriaRegional, Escola, Lote, Subprefeitura, TipoGestao


class LoteCreateSerializer(serializers.ModelSerializer):
    # TODO: calvin criar metodo create e update daqui. vide kit lanche para se basear
    diretoria_regional = serializers.SlugRelatedField(
        slug_field="uuid", queryset=DiretoriaRegional.objects.all()
    )
    subprefeituras = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=Subprefeitura.objects.all()
    )
    tipo_gestao = serializers.SlugRelatedField(
        slug_field="uuid", queryset=TipoGestao.objects.all()
    )

    escolas = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=Escola.objects.all()
    )

    class Meta:
        model = Lote
        exclude = ("id",)
