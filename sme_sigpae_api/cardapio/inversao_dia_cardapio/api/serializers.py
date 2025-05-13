from rest_framework import serializers

from sme_sigpae_api.cardapio.base.api.serializers import (
    CardapioSimplesSerializer,
    TipoAlimentacaoSimplesSerializer,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from sme_sigpae_api.escola.api.serializers import EscolaSimplesSerializer
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class InversaoCardapioSerializer(serializers.ModelSerializer):
    cardapio_de = CardapioSimplesSerializer()
    cardapio_para = CardapioSimplesSerializer()
    escola = EscolaSimplesSerializer()
    id_externo = serializers.CharField()
    prioridade = serializers.CharField()
    data = serializers.DateField()
    data_de = serializers.DateField()
    data_para = serializers.DateField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()
    tipos_alimentacao = TipoAlimentacaoSimplesSerializer(many=True)

    class Meta:
        model = InversaoCardapio
        exclude = ("id", "criado_por")


class InversaoCardapioSimpleserializer(serializers.ModelSerializer):
    id_externo = serializers.CharField()
    prioridade = serializers.CharField()
    escola = EscolaSimplesSerializer()
    data = serializers.DateField()

    class Meta:
        model = InversaoCardapio
        exclude = (
            "id",
            "criado_por",
            "cardapio_de",
            "cardapio_para",
        )
