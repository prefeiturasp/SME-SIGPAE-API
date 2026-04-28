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
    """Serializa a escrita de uma faixa etaria de substituicao de alimentacao CEI.

    Recebe referencias por UUID para a substituicao de periodo escolar e para a
    faixa etaria ao criar a solicitacao CEI.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioCEIViewSet``, aninhado em
          ``SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate`` nas
          actions ``create``, ``update`` e ``partial_update``.
    """

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
):
    """Serializa a escrita completa de substituicoes por periodo escolar para CEI.

    Complementa o serializer base com o tipo de alimentacao de destino (FK) e
    as faixas etarias detalhadas, criando todos os relacionamentos vinculados.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioCEIViewSet``, aninhado em
          ``AlteracaoCardapioCEISerializerCreate`` nas actions ``create``,
          ``update`` e ``partial_update``.
    """

    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapioCEI.objects.all()
    )

    tipo_alimentacao_para = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=TipoAlimentacao.objects.all()
    )

    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEISerializerCreate(many=True)

    def create(self, validated_data):
        """Cria uma substituicao de alimentacao CEI com relacionamentos M2M e faixas etarias.

        Args:
            validated_data (dict): Dados validados pelo serializer, incluindo
                ``tipos_alimentacao_de`` e ``faixas_etarias``.

        Returns:
            SubstituicaoAlimentacaoNoPeriodoEscolarCEI: Instancia criada com
            os tipos de alimentacao de origem vinculados e as faixas etarias
            associadas.
        """
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
    """Serializa a criacao e atualizacao completas de alteracoes de cardapio CEI.

    Valida datas e regras de negocio especificas para CEI (incluindo
    duplicidade de RPL), resolve relacionamentos por UUID e cria as
    substituicoes por periodo e faixa etaria associadas ao pedido.

    Viewsets que utilizam este serializer:
        - ``AlteracoesCardapioCEIViewSet``: retornado por
          ``get_serializer_class()`` nas actions ``create``, ``update`` e
          ``partial_update``.
    """

    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarCEISerializerCreate(
        many=True
    )

    def validate_data(self, data):
        """Aplica as validacoes de negocio especificas para a data da solicitacao CEI.

        Args:
            data (datetime.date): Data informada na solicitacao.

        Returns:
            datetime.date: A mesma data recebida, apos passar pelas
            validacoes de prazo, ano corrente e duplicidade de RPL.

        Raises:
            ValidationError: Quando a data viola alguma das regras de negocio
                aplicadas.
        """
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
