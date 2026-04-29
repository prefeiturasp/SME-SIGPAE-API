from rest_framework import serializers

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers import (
    MotivoAlteracaoCardapioSerializer,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api.serializers_create import (
    DatasIntervaloAlteracaoCardapioCEMEICreateSerializer,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from sme_sigpae_api.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from sme_sigpae_api.escola.api.serializers import (
    EscolaSimplesSerializer,
    FaixaEtariaSerializer,
    PeriodoEscolarSerializer,
    TipoAlimentacaoSerializer,
)
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class FaixaEtariaSubstituicaoAlimentacaoCEMEICEISerializer(serializers.ModelSerializer):
    """Serializer de leitura para ``FaixaEtariaSubstituicaoAlimentacaoCEMEICEI``.

    Expande o campo ``faixa_etaria`` com a representação completa via
    ``FaixaEtariaSerializer``.
    """

    faixa_etaria = FaixaEtariaSerializer()

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEMEICEI
        exclude = ("id",)


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEISerializer(
    serializers.ModelSerializer
):
    """Serializer de leitura para ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI``.

    Expande ``periodo_escolar``, ``faixas_etarias``, ``tipos_alimentacao_de`` e
    ``tipos_alimentacao_para`` com seus respectivos serializers aninhados.
    """

    periodo_escolar = PeriodoEscolarSerializer()
    faixas_etarias = FaixaEtariaSubstituicaoAlimentacaoCEMEICEISerializer(many=True)
    tipos_alimentacao_de = TipoAlimentacaoSerializer(many=True)
    tipos_alimentacao_para = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI
        exclude = ("id",)


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEISerializer(
    serializers.ModelSerializer
):
    """Serializer de leitura para ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI``.

    Expande ``periodo_escolar``, ``tipos_alimentacao_de`` e
    ``tipos_alimentacao_para`` com seus respectivos serializers aninhados.
    """

    periodo_escolar = PeriodoEscolarSerializer()
    tipos_alimentacao_de = TipoAlimentacaoSerializer(many=True)
    tipos_alimentacao_para = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI
        exclude = ("id",)


class AlteracaoCardapioCEMEISerializer(serializers.ModelSerializer):
    """Serializer de leitura para ``AlteracaoCardapioCEMEI``.

    Utilizado pelo ``AlteracoesCardapioCEMEIViewSet`` nas actions de listagem e
    recuperação de solicitações. Expande todos os campos relacionados com
    representações completas, incluindo as substituições separadas por parte
    CEI (``substituicoes_cemei_cei_periodo_escolar``) e EMEI
    (``substituicoes_cemei_emei_periodo_escolar``), datas do intervalo,
    rastro de terceirizada e logs de transição.
    """

    escola = EscolaSimplesSerializer()
    motivo = MotivoAlteracaoCardapioSerializer()
    foi_solicitado_fora_do_prazo = serializers.BooleanField()
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    prioridade = serializers.CharField()
    substituicoes_cemei_cei_periodo_escolar = (
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEISerializer(many=True)
    )
    substituicoes_cemei_emei_periodo_escolar = (
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEISerializer(many=True)
    )
    datas_intervalo = DatasIntervaloAlteracaoCardapioCEMEICreateSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AlteracaoCardapioCEMEI
        exclude = ("id",)
