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

from ...models import (
    CronogramaTermoRecebimentoDefinitivo,
    LoteMemorandoOcorrencia,
    MemorandoOcorrencia,
    TermoRecebimentoDefinitivo,
)


class CronogramaTermoRecebimentoDefinitivoSerializer(serializers.ModelSerializer):
    """Cronograma do termo com a quantidade recebida."""

    cronograma = CronogramaSerializer(read_only=True)

    class Meta:
        model = CronogramaTermoRecebimentoDefinitivo
        fields = (
            "cronograma",
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
    produtos = serializers.SerializerMethodField()
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

    def get_produtos(self, obj):
        """Nomes dos produtos dos cronogramas do termo, sem duplicidades."""
        produtos = []
        for cronograma in obj.cronogramas.all():
            ficha_tecnica = cronograma.ficha_tecnica
            nome = ficha_tecnica.produto.nome if ficha_tecnica else None
            if nome and nome not in produtos:
                produtos.append(nome)
        return produtos

    class Meta:
        model = TermoRecebimentoDefinitivo
        fields = (
            "uuid",
            "nome_empresa",
            "cnpj_empresa",
            "numero_contrato",
            "numeros_cronogramas",
            "produtos",
            "status",
            "status_display",
            "data_cadastro",
            "alterado_em",
        )
        read_only_fields = fields


class TermoRecebimentoDefinitivoPainelAssinaturaSerializer(serializers.ModelSerializer):
    """Termo no painel de assinaturas do fiscal."""

    empresa = serializers.CharField(
        source="empresa.nome_fantasia",
        read_only=True,
    )
    razao_social = serializers.CharField(
        source="empresa.razao_social",
        read_only=True,
    )
    numero_contrato = serializers.CharField(
        source="contrato.numero",
        read_only=True,
    )
    numeros_cronogramas = serializers.SerializerMethodField()
    nomes_produtos = serializers.SerializerMethodField()
    criado_em = serializers.SerializerMethodField()

    def get_numeros_cronogramas(self, obj):
        """Números dos cronogramas vinculados ao termo."""
        return [cronograma.numero for cronograma in obj.cronogramas.all()]

    def get_nomes_produtos(self, obj):
        """Nomes dos produtos dos cronogramas do termo, sem duplicidades."""
        produtos = []
        for cronograma in obj.cronogramas.all():
            ficha_tecnica = cronograma.ficha_tecnica
            nome = ficha_tecnica.produto.nome if ficha_tecnica else None
            if nome and nome not in produtos:
                produtos.append(nome)
        return produtos

    def get_criado_em(self, obj):
        return obj.criado_em.strftime(FORMATO_DATA_BRASILEIRO)

    class Meta:
        model = TermoRecebimentoDefinitivo
        fields = (
            "uuid",
            "empresa",
            "razao_social",
            "numero_contrato",
            "numeros_cronogramas",
            "nomes_produtos",
            "criado_em",
        )
        read_only_fields = fields


class TermoRecebimentoDefinitivoSerializer(serializers.ModelSerializer):
    """Serializador de saída do Termo de Recebimento Definitivo.

    Os modelos já existentes (empresa, contrato, cronogramas e fiscais)
    são serializados pelos serializers de seus respectivos módulos. Cada
    cronograma possui sua própria quantidade recebida;
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
    pode_assinar = serializers.SerializerMethodField()

    def get_pode_assinar(self, obj):
        """O usuário logado pode assinar o termo agora?"""
        request = self.context.get("request")
        if not request:
            return False
        return obj.pode_assinar(request.user)

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
            "valor_contrato",
            "texto_termo",
            "status",
            "pode_assinar",
            "criado_em",
            "alterado_em",
        )
        read_only_fields = fields


class LoteMemorandoOcorrenciaSerializer(serializers.ModelSerializer):
    """Lote do Memorando de Ocorrência para leitura."""

    class Meta:
        model = LoteMemorandoOcorrencia
        fields = (
            "uuid",
            "lote",
            "marca",
            "data_fabricacao",
            "data_validade",
            "quantidade_problema_devolucao",
            "ordem",
        )
        read_only_fields = fields


class MemorandoOcorrenciaSerializer(serializers.ModelSerializer):
    """Memorando de Ocorrência para leitura."""

    categoria_display = serializers.CharField(
        source="get_categoria_display",
        read_only=True,
    )
    tipo_ocorrencia_display = serializers.CharField(
        source="get_tipo_ocorrencia_display",
        read_only=True,
    )
    lotes = LoteMemorandoOcorrenciaSerializer(many=True, read_only=True)

    class Meta:
        model = MemorandoOcorrencia
        fields = (
            "uuid",
            "categoria",
            "categoria_display",
            "produto",
            "tipo_ocorrencia",
            "tipo_ocorrencia_display",
            "lotes",
        )
        read_only_fields = fields
