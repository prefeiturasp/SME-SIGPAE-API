"""Serializers de leitura da API de inversao de dia de cardapio."""

from rest_framework import serializers

from src.cardapio.base.api.serializers import (
    TipoAlimentacaoSimplesSerializer,
)
from src.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from src.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from src.escola.api.serializers import EscolaSimplesSerializer
from src.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class InversaoCardapioSerializer(serializers.ModelSerializer):
    """Serializa a representação detalhada de uma Inversao de dia de Cardápio.

    Inclui dados da escola, terceirizada, logs da solicitação e os tipos de
    alimentação associados à inversão.
    """

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
    """Serializa uma visão resumida de uma inversão de cardápio.

    Exibe os campos essenciais para listagens em que não é necessário carregar
    toda a estrutura detalhada da solicitação.
    """

    id_externo = serializers.CharField()
    prioridade = serializers.CharField()
    escola = EscolaSimplesSerializer()
    data = serializers.DateField()

    class Meta:
        model = InversaoCardapio
        exclude = ("id", "criado_por")
