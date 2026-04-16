from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.cronograma_semanal.models import (
    CronogramaSemanal,
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
