from rest_framework import serializers

from sme_sigpae_api.dados_comuns.api.serializers import (
    LogSolicitacoesUsuarioSimplesSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    ContratoSimplesSerializer,
    TerceirizadaLookUpSerializer,
    UnidadeMedidaSerialzer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import Cronograma
from sme_sigpae_api.pre_recebimento.cronograma_semanal.models import (
    CronogramaSemanal,
    ProgramacaoEntregaSemanal,
)


class CronogramaSemanalListagemSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de Cronogramas Semanais.
    Campos somente leitura conforme especificação.
    Ordenação por data de alteração (mais recente primeiro).
    """

    numero = serializers.CharField(source="cronograma_mensal.numero", read_only=True)
    produto = serializers.CharField(
        source="cronograma_mensal.ficha_tecnica.produto.nome", read_only=True
    )
    quantidade_total = serializers.SerializerMethodField(read_only=True)
    unidade_medida = serializers.SerializerMethodField(read_only=True)
    empresa = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(source="get_status_display", read_only=True)

    def get_quantidade_total(self, obj):
        """
        Retorna a quantidade total com unidade de medida do cronograma mensal.
        """
        if obj.cronograma_mensal:
            return str(obj.cronograma_mensal.qtd_total_programada)
        return "-"

    def get_unidade_medida(self, obj):
        """
        Retorna a unidade de medida do cronograma mensal.
        """
        if obj.cronograma_mensal and obj.cronograma_mensal.unidade_medida:
            return obj.cronograma_mensal.unidade_medida.abreviacao
        return "-"

    def get_empresa(self, obj):
        """
        Retorna o nome da empresa do cronograma mensal.
        """
        return obj.cronograma_mensal.empresa.nome if obj.cronograma_mensal else "-"

    class Meta:
        model = CronogramaSemanal
        fields = [
            "uuid",
            "numero",
            "produto",
            "quantidade_total",
            "unidade_medida",
            "empresa",
            "status",
            "alterado_em",
        ]
        read_only_fields = fields


class ProgramacaoEntregaSemanalDetailSerializer(serializers.ModelSerializer):
    """Serializer para leitura de ProgramacaoEntregaSemanal"""

    class Meta:
        model = ProgramacaoEntregaSemanal
        fields = (
            "mes_programado",
            "data_inicio",
            "data_fim",
            "quantidade",
        )


class CronogramaMensalSimplesSerializer(serializers.ModelSerializer):
    """Serializer simplificado para dados do Cronograma Mensal"""

    empresa = TerceirizadaLookUpSerializer()
    contrato = ContratoSimplesSerializer()
    unidade_medida = UnidadeMedidaSerialzer()
    produto = serializers.SerializerMethodField()

    class Meta:
        model = Cronograma
        fields = (
            "uuid",
            "numero",
            "empresa",
            "contrato",
            "numero_empenho",
            "qtd_total_empenho",
            "custo_unitario_produto",
            "unidade_medida",
            "produto",
        )

    def get_produto(self, obj):
        from sme_sigpae_api.produto.api.serializers.serializers import ProdutoSimplesSerializer

        if obj.ficha_tecnica and obj.ficha_tecnica.produto:
            return ProdutoSimplesSerializer(obj.ficha_tecnica.produto).data
        return None


class CronogramaSemanalRascunhosSerializer(serializers.ModelSerializer):
    numero = serializers.CharField(source="cronograma_mensal.numero", read_only=True)

    class Meta:
        model = CronogramaSemanal
        fields = ("uuid", "numero", "alterado_em")


class CronogramaSemanalDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para detalhamento de CronogramaSemanal (retrieve).
    Inclui dados do cronograma mensal, programações e logs.
    """

    status = serializers.CharField(source="get_status_display", read_only=True)
    cronograma_mensal = CronogramaMensalSimplesSerializer()
    programacoes = ProgramacaoEntregaSemanalDetailSerializer(many=True)
    logs = LogSolicitacoesUsuarioSimplesSerializer(many=True)

    class Meta:
        model = CronogramaSemanal
        fields = (
            "uuid",
            "numero",
            "status",
            "observacoes",
            "cronograma_mensal",
            "programacoes",
            "logs",
        )
