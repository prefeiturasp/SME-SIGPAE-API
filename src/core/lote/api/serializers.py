from __future__ import annotations

from rest_framework import serializers

from ....dados_comuns.mixins.serializer_context import (
    EscolaNomeHistoricoSerializerMixin,
)
from ....terceirizada.api.serializers.serializers import (
    ContratoEditalSerializer,
    TerceirizadaSimplesSerializer,
)
from ...api.serializers_base import TipoGestaoSerializer
from ...diretoria_regional.api.serializers import (
    DiretoriaRegionalParaFiltroSerializer,
    DiretoriaRegionalSimplissimaSerializer,
)
from ...models import Escola, Lote
from ...subprefeitura.api.serializers import SubprefeituraSerializer


class LoteReclamacaoSerializer(serializers.ModelSerializer):
    terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "terceirizada")


class LoteNomeSerializer(serializers.ModelSerializer):
    contratos_do_lote = ContratoEditalSerializer(many=True)
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    tipo_gestao = serializers.CharField()
    terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = Lote
        fields = (
            "uuid",
            "nome",
            "tipo_gestao",
            "diretoria_regional",
            "terceirizada",
            "contratos_do_lote",
        )


class LoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lote
        fields = ("uuid", "nome")


class EscolaNomeCodigoEOLSerializer(
    EscolaNomeHistoricoSerializerMixin, serializers.ModelSerializer
):
    nome = serializers.SerializerMethodField()
    lote = LoteSerializer()

    class Meta:
        model = Escola
        fields = ("uuid", "nome", "codigo_eol", "lote")


class LoteSimplesSerializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalSimplissimaSerializer()
    tipo_gestao = TipoGestaoSerializer()
    escolas = EscolaNomeCodigoEOLSerializer(many=True)
    terceirizada = TerceirizadaSimplesSerializer()
    subprefeituras = SubprefeituraSerializer(many=True)

    class Meta:
        model = Lote
        exclude = ("id",)


class LoteComContratosSerializer(serializers.ModelSerializer):
    contratos_do_lote = ContratoEditalSerializer(many=True)

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "contratos_do_lote")


class LoteParaFiltroSerializer(serializers.ModelSerializer):
    diretoria_regional = DiretoriaRegionalParaFiltroSerializer()

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "diretoria_regional")
