from rest_framework import serializers

from src.perfil.api.serializers import UsuarioSimplesSerializer
from src.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaSimplesSerializer,
)
from src.terceirizada.api.serializers.serializers import (
    ContratoSimplesSerializer,
    TerceirizadaSimplesSerializer,
)

from ...models import CronogramaTermoRecebimentoDefinitivo, TermoRecebimentoDefinitivo


class CronogramaTermoRecebimentoDefinitivoSerializer(serializers.ModelSerializer):
    """Cronograma do termo com valor de contrato e quantidade recebida."""

    cronograma = CronogramaSimplesSerializer(read_only=True)

    class Meta:
        model = CronogramaTermoRecebimentoDefinitivo
        fields = (
            "cronograma",
            "valor_contrato",
            "quantidade_total_recebida",
        )
        read_only_fields = fields


class TermoRecebimentoDefinitivoSerializer(serializers.ModelSerializer):
    """Serializador de saída do Termo de Recebimento Definitivo.

    Os modelos já existentes (empresa, contrato, cronogramas e fiscais)
    são serializados pelos serializers de seus respectivos módulos. Cada
    cronograma possui seu próprio valor de contrato e quantidade recebida.
    """

    empresa = TerceirizadaSimplesSerializer(read_only=True)
    contrato = ContratoSimplesSerializer(read_only=True)
    cronogramas = CronogramaTermoRecebimentoDefinitivoSerializer(
        source="cronogramas_termo",
        many=True,
        read_only=True,
    )
    fiscal_1 = UsuarioSimplesSerializer(read_only=True)
    fiscal_2 = UsuarioSimplesSerializer(read_only=True)
    fiscal_3 = UsuarioSimplesSerializer(read_only=True)

    class Meta:
        model = TermoRecebimentoDefinitivo
        fields = (
            "uuid",
            "empresa",
            "contrato",
            "cronogramas",
            "fiscal_1",
            "fiscal_2",
            "fiscal_3",
            "texto_termo",
            "status",
            "criado_em",
            "alterado_em",
        )
        read_only_fields = fields
