import json

from drf_base64.serializers import ModelSerializer
from rest_framework import serializers

from sme_sigpae_api.dieta_especial.protocolo_padrao.models import (
    Alimento,
    ProtocoloPadraoDietaEspecial,
    SubstituicaoAlimento,
    SubstituicaoAlimentoProtocoloPadrao,
)
from sme_sigpae_api.produto.api.serializers.serializers import (
    MarcaSimplesSerializer,
    ProdutoSimplesSerializer,
)
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    EditalSimplesSerializer,
)


class AlimentoSerializer(serializers.ModelSerializer):
    marca = MarcaSimplesSerializer()

    class Meta:
        model = Alimento
        fields = "__all__"
        ordering = "nome"


class AlimentosSubstitutosSerializer(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()

    def get_tipo(self, instance):
        return "a"

    class Meta:
        model = Alimento
        fields = ("uuid", "nome", "tipo")


class SubstituicaoAlimentoSerializer(ModelSerializer):
    alimento = AlimentoSerializer()
    substitutos = ProdutoSimplesSerializer(many=True)
    alimentos_substitutos = AlimentoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimento
        fields = "__all__"


class SubstituicaoAlimentoProtocoloPadraoSerializer(ModelSerializer):
    alimento = AlimentoSerializer()
    substitutos = ProdutoSimplesSerializer(many=True)
    alimentos_substitutos = AlimentoSerializer(many=True)
    tipo = serializers.CharField(source="get_tipo_display")

    class Meta:
        model = SubstituicaoAlimentoProtocoloPadrao
        fields = "__all__"


class ProtocoloPadraoDietaEspecialSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocoloPadraoDietaEspecial
        fields = ("nome_protocolo", "uuid")


class ProtocoloPadraoDietaEspecialSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    substituicoes = serializers.SerializerMethodField()
    historico = serializers.SerializerMethodField()
    editais = EditalSimplesSerializer(many=True)

    class Meta:
        model = ProtocoloPadraoDietaEspecial
        fields = (
            "uuid",
            "nome_protocolo",
            "status",
            "orientacoes_gerais",
            "substituicoes",
            "editais",
            "historico",
            "outras_informacoes",
        )

    def get_historico(self, obj):
        return json.loads(obj.historico) if obj.historico else []

    def get_substituicoes(self, obj):
        substituicoes = obj.substituicoes.all().order_by("alimento__nome")
        return SubstituicaoAlimentoProtocoloPadraoSerializer(
            substituicoes, many=True
        ).data
