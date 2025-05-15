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
    class Meta:
        model = MotivoAlteracaoCardapio
        exclude = ("id",)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase(
    serializers.ModelSerializer
):
    periodo_escolar = PeriodoEscolarSerializer()
    alteracao_cardapio = serializers.SlugRelatedField(
        slug_field="uuid", required=False, queryset=AlteracaoCardapio.objects.all()
    )
    tipos_alimentacao_de = TipoAlimentacaoSerializer(many=True)


class SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializerBase
):
    tipos_alimentacao_para = TipoAlimentacaoSerializer(many=True)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolar
        exclude = ("id",)


class AlteracaoCardapioSerializerBase(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    motivo = MotivoAlteracaoCardapioSerializer()
    foi_solicitado_fora_do_prazo = serializers.BooleanField()
    eh_alteracao_com_lanche_repetida = serializers.BooleanField()
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    prioridade = serializers.CharField()


class AlteracaoCardapioSerializer(AlteracaoCardapioSerializerBase):
    substituicoes = SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(many=True)
    datas_intervalo = DatasIntervaloAlteracaoCardapioSerializerCreateSerializer(
        many=True
    )
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = AlteracaoCardapio
        exclude = ("id",)


class AlteracaoCardapioSimplesSerializer(serializers.ModelSerializer):
    prioridade = serializers.CharField()

    class Meta:
        model = AlteracaoCardapio
        exclude = ("id", "criado_por", "escola", "motivo")
