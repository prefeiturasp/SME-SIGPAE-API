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
    """Serializa uma faixa etaria com quantidade e matriculados de uma substituicao CEI.

    Expoe os campos publicos de ``FaixaEtariaSubstituicaoAlimentacaoCEI``
    utilizados nas respostas aninhadas em substituicoes de periodo escolar CEI.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioCEIViewSet``, aninhado em
          ``SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializer`` nas
          respostas de leitura.
    """

    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEI
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializer(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase
):
    """Serializa substituicoes completas de alimentacao por periodo escolar para CEI.

    Complementa o serializer base com o tipo de alimentacao de destino (FK) e
    as faixas etarias detalhadas, alem de injetar o total de alunos por faixa
    no periodo escolar via ``to_representation``.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioCEIViewSet``, aninhado em
          ``AlteracaoCardapioCEISerializer`` nas respostas de leitura.
    """

    tipo_alimentacao_para = TipoAlimentacaoSerializer()

    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEISerializer(many=True)

    def to_representation(self, instance):
        """Adiciona o total de alunos por faixa etaria no periodo escolar.

        Consulta o metodo ``alunos_por_periodo_e_faixa_etaria`` da escola para
        enriquecer cada faixa etaria com o campo ``total_alunos_no_periodo``.

        Args:
            instance (SubstituicaoAlimentacaoNoPeriodoEscolarCEI): Substituicao
                a ser representada.

        Returns:
            dict: Representacao da substituicao com o campo
            ``total_alunos_no_periodo`` adicionado a cada faixa etaria
            encontrada na consulta. Faixas nao encontradas no dicionario de
            alunos sao ignoradas silenciosamente.
        """
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
    """Serializa a representacao detalhada de uma alteracao de cardapio CEI.

    Inclui substituicoes por periodo com faixas etarias, motivo, escola, logs
    e dados de rastreabilidade usados nas respostas completas da API.

    Viewsets que utilizam este serializer:
        - ``AlteracoesCardapioCEIViewSet``: retornado por
          ``get_serializer_class()`` em todas as acoes de leitura e nas actions
          customizadas que respondem com o objeto serializado, exceto
          ``create``, ``update`` e ``partial_update``.
    """

    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AlteracaoCardapioCEI
        exclude = ("id",)
