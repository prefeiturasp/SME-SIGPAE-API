from rest_framework import serializers

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from src.perfil.api.serializers import UsuarioSimplesSerializer
from src.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaSerializer,
)
from src.terceirizada.api.serializers.serializers import (
    ContratoSimplesSerializer,
    TerceirizadaSimplesSerializer,
)

from ...models import CronogramaTermoRecebimentoDefinitivo, TermoRecebimentoDefinitivo


class CronogramaTermoRecebimentoDefinitivoSerializer(serializers.ModelSerializer):
    """Cronograma do termo com valor de contrato e quantidade recebida."""

    cronograma = CronogramaSerializer(read_only=True)

    class Meta:
        model = CronogramaTermoRecebimentoDefinitivo
        fields = (
            "cronograma",
            "valor_contrato",
            "quantidade_total_recebida",
        )
        read_only_fields = fields


class TermoRecebimentoDefinitivoListagemSerializer(serializers.ModelSerializer):
    """
    Serializador para a listagem de Termos de Recebimento Definitivo.
    """

    nome_empresa = serializers.CharField(
        source="empresa.nome_fantasia",
        read_only=True,
    )
    cnpj_empresa = serializers.CharField(
        source="empresa.cnpj",
        read_only=True,
    )
    numero_contrato = serializers.CharField(
        source="contrato.numero",
        read_only=True,
    )
    numeros_cronogramas = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    data_cadastro = serializers.SerializerMethodField()

    def get_data_cadastro(self, obj):
        return obj.criado_em.strftime(FORMATO_DATA_BRASILEIRO)

    def get_numeros_cronogramas(self, obj):
        """Números dos cronogramas vinculados ao termo."""
        return [cronograma.numero for cronograma in obj.cronogramas.all()]

    class Meta:
        model = TermoRecebimentoDefinitivo
        fields = (
            "uuid",
            "nome_empresa",
            "cnpj_empresa",
            "numero_contrato",
            "numeros_cronogramas",
            "status",
            "status_display",
            "data_cadastro",
            "alterado_em",
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
