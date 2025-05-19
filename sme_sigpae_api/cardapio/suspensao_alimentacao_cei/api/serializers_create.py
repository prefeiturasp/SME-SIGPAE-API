from rest_framework import serializers

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from sme_sigpae_api.dados_comuns.utils import update_instance_from_dict
from sme_sigpae_api.dados_comuns.validators import (
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from sme_sigpae_api.escola.models import Escola, PeriodoEscolar


class SuspensaoAlimentacaodeCEICreateSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )

    motivo = serializers.SlugRelatedField(
        slug_field="uuid", queryset=MotivoSuspensao.objects.all()
    )

    outro_motivo = serializers.CharField(required=False)

    periodos_escolares = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=PeriodoEscolar.objects.all()
    )

    def validate(self, attrs):
        data = attrs["data"]
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        return attrs

    def create(self, validated_data):
        periodos_escolares = validated_data.pop("periodos_escolares", "")
        validated_data["criado_por"] = self.context["request"].user
        suspensao_alimentacao = SuspensaoAlimentacaoDaCEI.objects.create(
            **validated_data
        )
        suspensao_alimentacao.periodos_escolares.set(periodos_escolares)
        suspensao_alimentacao.save()
        return suspensao_alimentacao

    def update(self, instance, validated_data):
        periodos_escolares = validated_data.pop("periodos_escolares", "")
        update_instance_from_dict(instance, validated_data)
        instance.periodos_escolares.set([])
        instance.periodos_escolares.set(periodos_escolares)
        instance.save()
        return instance

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
        exclude = ("id", "status", "criado_por")
