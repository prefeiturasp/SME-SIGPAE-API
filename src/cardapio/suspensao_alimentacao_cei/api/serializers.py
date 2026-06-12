from rest_framework import serializers

from src.cardapio.suspensao_alimentacao.api.serializers import (
    MotivoSuspensaoSerializer,
)
from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from src.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from src.escola.api.serializers import (
    EscolaSimplesSerializer,
    PeriodoEscolarSimplesSerializer,
)
from src.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class SuspensaoAlimentacaoDaCEISerializer(serializers.ModelSerializer):
    """Serializa a representação completa de uma suspensão de CEI.

    Inclui escola, motivo, períodos escolares, logs e rastro da terceirizada
    usados nas respostas detalhadas da API de suspensão de alimentação CEI.

    Viewsets que utilizam este serializer:
        - ``SuspensaoAlimentacaoDaCEIViewSet``: retornado por
          ``get_serializer_class()`` em todas as ações de leitura e nas
          actions customizadas que respondem com o objeto serializado, exceto
          ``create``, ``update`` e ``partial_update``.
    """

    escola = EscolaSimplesSerializer()
    motivo = MotivoSuspensaoSerializer()
    periodos_escolares = PeriodoEscolarSimplesSerializer(many=True)
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
        exclude = ("id",)
