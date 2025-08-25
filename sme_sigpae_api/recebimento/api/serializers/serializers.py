from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
    FichaTecnicaSimplesSerializer,
)

from ...models import (
    FichaDeRecebimento,
    QuestaoConferencia,
    QuestaoFichaRecebimento,
    QuestoesPorProduto,
)


class QuestaoConferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestaoConferencia
        fields = (
            "uuid",
            "questao",
            "tipo_questao",
            "pergunta_obrigatoria",
            "posicao",
        )


class QuestaoConferenciaSimplesSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestaoConferencia
        fields = (
            "uuid",
            "questao",
        )


class QuestoesPorProdutoSerializer(serializers.ModelSerializer):
    numero_ficha = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    questoes_primarias = serializers.SerializerMethodField()
    questoes_secundarias = serializers.SerializerMethodField()

    def get_numero_ficha(self, obj):
        return obj.ficha_tecnica.numero if obj.ficha_tecnica else None

    def get_nome_produto(self, obj):
        return obj.ficha_tecnica.produto.nome if obj.ficha_tecnica else None

    def get_questoes_primarias(self, obj):
        return (
            obj.questoes_primarias.order_by("posicao", "criado_em").values_list(
                "questao", flat=True
            )
            if obj.questoes_primarias
            else []
        )

    def get_questoes_secundarias(self, obj):
        return (
            obj.questoes_secundarias.order_by("posicao", "criado_em").values_list(
                "questao", flat=True
            )
            if obj.questoes_secundarias
            else []
        )

    class Meta:
        model = QuestoesPorProduto
        fields = (
            "uuid",
            "numero_ficha",
            "nome_produto",
            "questoes_primarias",
            "questoes_secundarias",
        )


class QuestoesPorProdutoSimplesSerializer(serializers.ModelSerializer):
    ficha_tecnica = FichaTecnicaSimplesSerializer()
    questoes_primarias = serializers.SlugRelatedField(
        slug_field="uuid",
        read_only=True,
        many=True,
    )
    questoes_secundarias = serializers.SlugRelatedField(
        slug_field="uuid",
        read_only=True,
        many=True,
    )

    class Meta:
        model = QuestoesPorProduto
        fields = (
            "uuid",
            "ficha_tecnica",
            "questoes_primarias",
            "questoes_secundarias",
        )


class QuestoesPorProdutoDetalheSerializer(serializers.ModelSerializer):
    questoes_primarias = QuestaoConferenciaSimplesSerializer(many=True)
    questoes_secundarias = QuestaoConferenciaSimplesSerializer(many=True)

    class Meta:
        model = QuestoesPorProduto
        fields = (
            "uuid",
            "questoes_primarias",
            "questoes_secundarias",
        )


class QuestaoFichaRecebimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestaoFichaRecebimento
        exclude = ("id",)


class FichaDeRecebimentoSerializer(serializers.ModelSerializer):
    numero_cronograma = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    fornecedor = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    data_recebimento = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")

    def get_numero_cronograma(self, obj):
        try:
            return obj.etapa.cronograma.numero
        except AttributeError:
            None

    def get_nome_produto(self, obj):
        try:
            return obj.etapa.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            None

    def get_fornecedor(self, obj):
        try:
            return obj.etapa.cronograma.empresa.nome_fantasia
        except AttributeError:
            None

    def get_pregao_chamada_publica(self, obj):
        try:
            return obj.etapa.cronograma.contrato.pregao_chamada_publica
        except AttributeError:
            None

    def get_data_recebimento(self, obj):
        try:
            return obj.data_entrega.strftime("%d/%m/%Y")
        except AttributeError:
            None

    class Meta:
        model = FichaDeRecebimento
        fields = (
            "uuid",
            "numero_cronograma",
            "nome_produto",
            "fornecedor",
            "pregao_chamada_publica",
            "data_recebimento",
            "status",
        )
