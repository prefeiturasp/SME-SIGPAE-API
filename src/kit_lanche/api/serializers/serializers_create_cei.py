from rest_framework import serializers

from ....dados_comuns.utils import update_instance_from_dict
from ....dados_comuns.validators import (
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
)
from ....escola.models import Aluno, Escola, FaixaEtaria
from ...models import (
    FaixaEtariaSolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
)
from .serializers_create import SolicitacaoKitLancheCreationSerializer


class FaixaEtariaSolicitacaoKitLancheCEIAvulsaCreateSerializer(
    serializers.ModelSerializer
):
    solicitacao_kit_lanche_avulsa = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SolicitacaoKitLancheCEIAvulsa.objects.all(),
    )
    faixa_etaria = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=FaixaEtaria.objects.all()
    )

    class Meta:
        model = FaixaEtariaSolicitacaoKitLancheCEIAvulsa
        exclude = ("id",)


class SolicitacaoKitLancheCEIAvulsaCreationSerializer(serializers.ModelSerializer):
    solicitacao_kit_lanche = SolicitacaoKitLancheCreationSerializer(required=True)
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )
    alunos_com_dieta_especial_participantes = serializers.SlugRelatedField(
        slug_field="uuid", many=True, queryset=Aluno.objects.all()
    )
    faixas_etarias = FaixaEtariaSolicitacaoKitLancheCEIAvulsaCreateSerializer(many=True)

    def validate_data(self, data_evento):
        nao_pode_ser_no_passado(data_evento)
        deve_pedir_com_antecedencia(data_evento)
        deve_ser_no_mesmo_ano_corrente(data_evento)

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user

        solicitacao_kit_lanche_data = validated_data.pop("solicitacao_kit_lanche")
        solicitacao_kit_lanche = SolicitacaoKitLancheCreationSerializer().create(
            solicitacao_kit_lanche_data
        )

        alunos_com_dieta = validated_data.pop("alunos_com_dieta_especial_participantes")
        faixas_etarias = validated_data.pop("faixas_etarias")

        solic = SolicitacaoKitLancheCEIAvulsa(
            solicitacao_kit_lanche=solicitacao_kit_lanche, **validated_data
        )
        solic.save()

        solic.alunos_com_dieta_especial_participantes.set(alunos_com_dieta)

        for linha in faixas_etarias:
            faixa = FaixaEtariaSolicitacaoKitLancheCEIAvulsa.objects.create(
                solicitacao_kit_lanche_avulsa=solic, **linha
            )
            solic.faixas_etarias.add(faixa)

        return solic

    def update(self, instance, validated_data):
        solicitacao_kit_lanche_data = validated_data.pop("solicitacao_kit_lanche")
        SolicitacaoKitLancheCreationSerializer().update(
            instance.solicitacao_kit_lanche, solicitacao_kit_lanche_data
        )

        alunos_com_dieta = validated_data.pop("alunos_com_dieta_especial_participantes")
        faixas_etarias = validated_data.pop("faixas_etarias")

        update_instance_from_dict(instance, validated_data, save=True)

        instance.alunos_com_dieta_especial_participantes.set(alunos_com_dieta)

        instance.faixas_etarias.all().delete()

        for linha in faixas_etarias:
            faixa = FaixaEtariaSolicitacaoKitLancheCEIAvulsa.objects.create(
                solicitacao_kit_lanche_avulsa=instance, **linha
            )
            instance.faixas_etarias.add(faixa)

        return instance

    class Meta:
        model = SolicitacaoKitLancheCEIAvulsa
        exclude = ("id", "status")
