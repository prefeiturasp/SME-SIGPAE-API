from rest_framework import serializers

from sme_sigpae_api.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    LogQuantidadeDietasAutorizadasRecreioNasFerias,
    LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI,
)
from sme_sigpae_api.dieta_especial.solicitacao_dieta_especial.api.serializers import (
    CLASSIFICACAO_NOME_SOURCE,
)
from sme_sigpae_api.escola.api.serializers import (
    FaixaEtariaSerializer,
)
from sme_sigpae_api.escola.models import Escola, PeriodoEscolar


class LogQuantidadeDietasAutorizadasSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Escola.objects.all()
    )
    classificacao = serializers.CharField(
        source=CLASSIFICACAO_NOME_SOURCE, required=False
    )
    dia = serializers.SerializerMethodField()
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=PeriodoEscolar.objects.all()
    )

    def get_dia(self, obj):
        dia = obj.data.day
        return f"{dia:02d}"

    class Meta:
        model = LogQuantidadeDietasAutorizadas
        exclude = ("id", "uuid")


class LogQuantidadeDietasAutorizadasCEISerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="nome", required=False, queryset=Escola.objects.all()
    )
    classificacao = serializers.CharField(
        source=CLASSIFICACAO_NOME_SOURCE, required=False
    )
    dia = serializers.SerializerMethodField()
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="nome", required=False, queryset=PeriodoEscolar.objects.all()
    )
    faixa_etaria = FaixaEtariaSerializer()

    def get_dia(self, obj):
        dia = obj.data.day
        return f"{dia:02d}"

    class Meta:
        model = LogQuantidadeDietasAutorizadasCEI
        exclude = ("id", "uuid")


class LogQuantidadeDietasAutorizadasRecreioNasFeriasSerializer(
    serializers.ModelSerializer
):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=Escola.objects.all()
    )
    classificacao = serializers.CharField(
        source=CLASSIFICACAO_NOME_SOURCE, read_only=True
    )
    dia = serializers.SerializerMethodField()

    def get_dia(self, obj):
        dia = obj.data.day
        return f"{dia:02d}"

    class Meta:
        model = LogQuantidadeDietasAutorizadasRecreioNasFerias
        exclude = ("id", "uuid")


class LogQuantidadeDietasAutorizadasRecreioNasFeriasCEISerializer(
    serializers.ModelSerializer
):
    escola = serializers.SlugRelatedField(
        slug_field="nome", required=False, queryset=Escola.objects.all()
    )
    classificacao = serializers.CharField(
        source=CLASSIFICACAO_NOME_SOURCE, required=False
    )
    dia = serializers.SerializerMethodField()
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="nome", required=False, queryset=PeriodoEscolar.objects.all()
    )
    faixa_etaria = FaixaEtariaSerializer()

    def get_dia(self, obj):
        dia = obj.data.day
        return f"{dia:02d}"

    class Meta:
        model = LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI
        exclude = ("id", "uuid")
