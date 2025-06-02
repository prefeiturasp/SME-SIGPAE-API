from rest_framework import serializers

from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
    SuspensaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.dados_comuns.utils import update_instance_from_dict
from sme_sigpae_api.dados_comuns.validators import (
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from sme_sigpae_api.escola.models import Escola, PeriodoEscolar


class SuspensaoAlimentacaoNoPeriodoEscolarCreateSerializer(serializers.ModelSerializer):
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=PeriodoEscolar.objects.all()
    )
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=TipoAlimentacao.objects.all()
    )

    class Meta:
        model = SuspensaoAlimentacaoNoPeriodoEscolar
        exclude = ("id", "suspensao_alimentacao")


class SuspensaoAlimentacaoCreateSerializer(serializers.ModelSerializer):
    motivo = serializers.SlugRelatedField(
        slug_field="uuid", queryset=MotivoSuspensao.objects.all()
    )

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return data

    class Meta:
        model = SuspensaoAlimentacao
        exclude = ("id",)


class QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer(
    serializers.ModelSerializer
):
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=PeriodoEscolar.objects.all()
    )
    tipos_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=TipoAlimentacao.objects.all()
    )
    alunos_cei_ou_emei = serializers.CharField(required=False)

    class Meta:
        model = QuantidadePorPeriodoSuspensaoAlimentacao
        exclude = ("id", "grupo_suspensao")


class GrupoSuspensaoAlimentacaoCreateSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Escola.objects.all()
    )
    quantidades_por_periodo = QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer(
        many=True
    )
    suspensoes_alimentacao = SuspensaoAlimentacaoCreateSerializer(many=True)

    def create(self, validated_data):
        quantidades_por_periodo_array = validated_data.pop("quantidades_por_periodo")
        suspensoes_alimentacao_array = validated_data.pop("suspensoes_alimentacao")
        validated_data["criado_por"] = self.context["request"].user

        quantidades = []
        for quantidade_json in quantidades_por_periodo_array:
            quantidade = (
                QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer().create(
                    quantidade_json
                )
            )
            quantidades.append(quantidade)

        suspensoes = []
        for suspensao_json in suspensoes_alimentacao_array:
            suspensao = SuspensaoAlimentacaoCreateSerializer().create(suspensao_json)
            suspensoes.append(suspensao)

        grupo = GrupoSuspensaoAlimentacao.objects.create(**validated_data)
        grupo.quantidades_por_periodo.set(quantidades)
        grupo.suspensoes_alimentacao.set(suspensoes)
        return grupo

    def update(self, instance, validated_data):
        quantidades_por_periodo_array = validated_data.pop("quantidades_por_periodo")
        suspensoes_alimentacao_array = validated_data.pop("suspensoes_alimentacao")

        instance.quantidades_por_periodo.all().delete()
        instance.suspensoes_alimentacao.all().delete()

        quantidades = []
        for quantidade_json in quantidades_por_periodo_array:
            quantidade = (
                QuantidadePorPeriodoSuspensaoAlimentacaoCreateSerializer().create(
                    quantidade_json
                )
            )
            quantidades.append(quantidade)

        suspensoes = []
        for suspensao_json in suspensoes_alimentacao_array:
            suspensao = SuspensaoAlimentacaoCreateSerializer().create(suspensao_json)
            suspensoes.append(suspensao)

        update_instance_from_dict(instance, validated_data, save=True)
        instance.quantidades_por_periodo.set(quantidades)
        instance.suspensoes_alimentacao.set(suspensoes)

        return instance

    class Meta:
        model = GrupoSuspensaoAlimentacao
        exclude = ("id",)
