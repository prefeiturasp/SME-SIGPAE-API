from rest_framework import serializers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers import (
    AlteracaoCardapioSerializerBase,
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    FaixaEtariaSubstituicaoAlimentacaoCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
)
from sme_sigpae_api.escola.api.serializers import (
    FaixaEtariaSerializer,
    TipoAlimentacaoSerializer,
)
from sme_sigpae_api.escola.models import FaixaEtaria
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class FaixaEtariaSubstituicaoAlimentacaoCEISerializer(serializers.ModelSerializer):
    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEI
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializer(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase
):
    tipo_alimentacao_para = TipoAlimentacaoSerializer()

    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEISerializer(many=True)

    def to_representation(self, instance):
        retorno = super().to_representation(instance)

        faixas_etarias_da_solicitacao = FaixaEtaria.objects.filter(
            uuid__in=[f.faixa_etaria.uuid for f in instance.faixas_etarias.all()]
        )

        # Inclui o total de alunos nas faixas etárias num período
        qtde_alunos = (
            instance.alteracao_cardapio.escola.alunos_por_periodo_e_faixa_etaria(
                instance.alteracao_cardapio.data, faixas_etarias_da_solicitacao
            )
        )

        nome_periodo_correcoes = {
            "PARCIAL": "INTEGRAL",
            "MANHA": "MANHÃ",
        }
        nome_periodo = nome_periodo_correcoes.get(
            instance.periodo_escolar.nome, instance.periodo_escolar.nome
        )

        for faixa_etaria in retorno["faixas_etarias"]:
            try:
                uuid_faixa_etaria = faixa_etaria["faixa_etaria"]["uuid"]
                faixa_etaria["total_alunos_no_periodo"] = qtde_alunos[nome_periodo][
                    uuid_faixa_etaria
                ]
            except KeyError:
                continue

        return retorno

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEI
        exclude = ("id",)


class AlteracaoCardapioCEISerializer(AlteracaoCardapioSerializerBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AlteracaoCardapioCEI
        exclude = ("id",)
