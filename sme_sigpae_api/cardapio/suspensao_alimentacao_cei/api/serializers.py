from rest_framework import serializers

from sme_sigpae_api.cardapio.suspensao_alimentacao.api.serializers import (
    MotivoSuspensaoSerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from sme_sigpae_api.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from sme_sigpae_api.escola.api.serializers import (
    EscolaSimplesSerializer,
    PeriodoEscolarSimplesSerializer,
)
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    TerceirizadaSimplesSerializer,
)


class SuspensaoAlimentacaoDaCEISerializer(serializers.ModelSerializer):
    escola = EscolaSimplesSerializer()
    motivo = MotivoSuspensaoSerializer()
    periodos_escolares = PeriodoEscolarSimplesSerializer(many=True)
    id_externo = serializers.CharField()
    logs = LogSolicitacoesUsuarioSerializer(many=True)
    rastro_terceirizada = TerceirizadaSimplesSerializer()

    class Meta:
        model = SuspensaoAlimentacaoDaCEI
        exclude = ("id",)
