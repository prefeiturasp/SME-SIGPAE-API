from rest_framework import serializers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers_create import (
    DatasIntervaloAlteracaoCardapioSerializerCreateSerializer,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from sme_sigpae_api.escola.api.serializers import (
    EscolaSimplesSerializer,
    PeriodoEscolarSerializer,
    TipoAlimentacaoSerializer,
)
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class MotivoAlteracaoCardapioSerializer(serializers.ModelSerializer):
    """Serializa motivos ativos de alteracao do tipo de alimentacao.

    Expoe os campos publicos de ``MotivoAlteracaoCardapio`` usados para listar
    e embutir o motivo selecionado em respostas de solicitacoes.

    Viewsets que utilizam este serializer:
        - ``MotivosAlteracaoCardapioViewSet``: uso direto como
          ``serializer_class`` nas acoes ``list`` e ``retrieve``.
        - ``AlteracoesCardapioViewSet``: uso indireto, aninhado em
          ``AlteracaoCardapioSerializer`` e retornado nas respostas que usam
          esse serializer.
    """

    class Meta:
        model = MotivoAlteracaoCardapio
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase(
    serializers.ModelSerializer
):
    """Define os campos base de substituicoes por periodo escolar.

    Centraliza a serializacao comum de periodo escolar, UUID da alteracao de
    cardapio e tipos de alimentacao de origem.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioViewSet``, por meio de
          ``SubstituicoesAlimentacaoNoPeriodoEscolarSerializer`` aninhado em
          ``AlteracaoCardapioSerializer``.
    """

    periodo_escolar = PeriodoEscolarSerializer()
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )
    tipos_alimentacao_de = TipoAlimentacaoSerializer(many=True)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase
):
    """Serializa substituicoes completas de alimentacao por periodo escolar.

    Complementa o serializer base com os tipos de alimentacao de destino para
    representar cada item da lista ``substituicoes`` de uma alteracao.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioViewSet``, aninhado em
          ``AlteracaoCardapioSerializer`` nas respostas de leitura.
    """

    tipos_alimentacao_para = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
        exclude = ("id",)


class AlteracaoCardapioSerializerBase(serializers.ModelSerializer):
    """Define os campos comuns das respostas de alteracao de cardapio.

    Reune os relacionamentos e campos calculados compartilhados pelos
    serializers de leitura de ``AlteracaoCardapio``.

    Viewsets que utilizam este serializer:
        - Nenhum diretamente.
        - Uso indireto em ``AlteracoesCardapioViewSet``, como classe base de
          ``AlteracaoCardapioSerializer``.
    """

    escola = EscolaSimplesSerializer()
    motivo = MotivoAlteracaoCardapioSerializer()
    foi_solicitado_fora_do_prazo = serializers.BooleanField()
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    prioridade = serializers.CharField()


class AlteracaoCardapioSerializer(AlteracaoCardapioSerializerBase):
    """Serializa a representacao detalhada de uma alteracao de cardapio.

    Inclui substituicoes por periodo, datas do intervalo, motivo, escola,
    logs e dados de rastreabilidade usados nas respostas completas da API.

    Viewsets que utilizam este serializer:
        - ``AlteracoesCardapioViewSet``: retornado por
          ``get_serializer_class()`` em todas as acoes de leitura e nas actions
          customizadas que respondem com o objeto serializado, exceto
          ``create``, ``update`` e ``partial_update``.
    """

    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(many=True)
    datas_intervalo = DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
        many=True
    )
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AlteracaoCardapio
        exclude = ("id",)


class AlteracaoCardapioSimplesSerializer(serializers.ModelSerializer):
    """Serializa uma visao resumida de alteracao de cardapio.

    Remove campos mais pesados e relacionamentos aninhados para atender listagens
    que precisam de um payload menor.

    Viewsets que utilizam este serializer:
        - ``AlteracoesCardapioViewSet``: uso direto na action
          ``solicitacoes_dre``.
    """

    prioridade = serializers.CharField()

    class Meta:
        model = AlteracaoCardapio
        exclude = ("id", "criado_por", "escola", "motivo")
