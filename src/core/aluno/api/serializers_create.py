from __future__ import annotations

from rest_framework import serializers

from ...models import AlunoPeriodoParcial, FaixaEtaria, MudancaFaixasEtarias


class FaixaEtariaSerializer(serializers.ModelSerializer):
    __str__ = serializers.CharField(required=False)

    def validate(self, attrs):
        if attrs["inicio"] >= attrs["fim"]:
            raise serializers.ValidationError(
                f"A faixa etária tem que terminar depois do início: inicio={attrs['inicio']};fim={attrs['fim']}"
            )
        return attrs

    class Meta:
        model = FaixaEtaria
        exclude = ("id", "ativo")


class MudancaFaixasEtariasCreateSerializer(serializers.Serializer):
    justificativa = serializers.CharField()
    faixas_etarias_ativadas = FaixaEtariaSerializer(many=True)

    # TODO: Ver se é possível eliminar esse método ou pelo menos usar bulk_create
    def create(self, validated_data):
        FaixaEtaria.objects.update(ativo=False)
        faixas_etarias = validated_data.pop("faixas_etarias_ativadas", [])

        fe_objs = []
        for fe in faixas_etarias:
            ser = FaixaEtariaSerializer(data=fe)
            if ser.is_valid():
                fe_objs.append(ser.save())
            else:
                raise serializers.ValidationError(
                    "Erro ao salvar faixa etária: " + ser.errors
                )

        mudanca = MudancaFaixasEtarias(justificativa=validated_data["justificativa"])
        mudanca.save()
        mudanca.faixas_etarias_ativadas.set(fe_objs)
        mudanca.save()
        return mudanca


class AlunoPeriodoParcialCreateSerializer(serializers.ModelSerializer):
    aluno = serializers.CharField()

    class Meta:
        model = AlunoPeriodoParcial
        fields = ("aluno", "data", "data_removido")
