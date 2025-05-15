from rest_framework import serializers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers_create import (
    AlteracaoCardapioSerializerCreateBase,
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    FaixaEtariaSubstituicaoAlimentacaoCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
)
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.dados_comuns.validators import (
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    nao_pode_ser_no_passado,
    valida_duplicidade_solicitacoes_cei,
)
from sme_sigpae_api.escola.models import FaixaEtaria


class FaixaEtariaSubstituicaoAlimentacaoCEISerializerCreate(
    serializers.ModelSerializer
):
    substituicao_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=SubstituicaoAlimentacaoNoPeriodoEscolarCEI.objects.all(),
    )

    faixa_etaria = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=FaixaEtaria.objects.all()
    )

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEI
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerCreateBase
):  # noqa E501
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapioCEI.objects.all()
    )

    tipo_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=TipoAlimentacao.objects.all()
    )

    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEISerializerCreate(many=True)

    def create(self, validated_data):
        faixas_etarias = validated_data.pop("faixas_etarias", "")
        tipos_alimentacao_de = validated_data.pop("tipos_alimentacao_de")
        substituicao_alimentacao = (
            SubstituicaoAlimentacaoNoPeriodoEscolarCEI.objects.create(**validated_data)
        )
        substituicao_alimentacao.tipos_alimentacao_de.set(tipos_alimentacao_de)
        substituicao_alimentacao.save()
        for faixa_etaria_dados in faixas_etarias:
            FaixaEtariaSubstituicaoAlimentacaoCEI.objects.create(
                substituicao_alimentacao=substituicao_alimentacao, **faixa_etaria_dados
            )
        return substituicao_alimentacao

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEI
        exclude = ("id",)


class AlteracaoCardapioCEISerializerCreate(AlteracaoCardapioSerializerCreateBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate(
        many=True
    )

    def validate_data(self, data):
        nao_pode_ser_no_passado(data)
        deve_pedir_com_antecedencia(data)
        deve_ser_no_mesmo_ano_corrente(data)
        attrs = self.context["request"].data
        motivo = MotivoAlteracaoCardapio.objects.filter(uuid=attrs["motivo"]).first()
        if motivo and motivo.nome == "RPL - Refeição por Lanche":
            valida_duplicidade_solicitacoes_cei(attrs, data)
        return data

    class Meta:
        model = AlteracaoCardapioCEI
        serializer_substituicao = (
            SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate
        )
        exclude = ("id", "status")
