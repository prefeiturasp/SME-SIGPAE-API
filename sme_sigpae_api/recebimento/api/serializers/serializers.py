import environ
from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    EtapasDoCronogramaSerializer,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    DocRecebimentoFichaDeRecebimentoSerializer,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializers import (
    FichaTecnicaSimplesSerializer,
)

from ...models import (
    ArquivoFichaRecebimento,
    FichaDeRecebimento,
    OcorrenciaFichaRecebimento,
    QuestaoConferencia,
    QuestaoFichaRecebimento,
    QuestoesPorProduto,
    VeiculoFichaDeRecebimento,
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


class VeiculoFichaDeRecebimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VeiculoFichaDeRecebimento
        exclude = ("id", "ficha_recebimento")


class QuestaoFichaRecebimentoDetailSerializer(serializers.ModelSerializer):
    questao_conferencia = QuestaoConferenciaSimplesSerializer(read_only=True)

    class Meta:
        model = QuestaoFichaRecebimento
        exclude = ("id", "ficha_recebimento")


class OcorrenciaFichaRecebimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OcorrenciaFichaRecebimento
        exclude = ("id", "ficha_recebimento")


class ArquivoFichaRecebimentoSerializer(serializers.ModelSerializer):
    nome = serializers.CharField()
    arquivo = serializers.SerializerMethodField()

    def get_arquivo(self, instance):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        return f"{api_url}{instance.arquivo.url}"

    class Meta:
        model = ArquivoFichaRecebimento
        exclude = ("id", "ficha_recebimento", "uuid")


class DadosCronogramaSerializer(serializers.Serializer):
    uuid = serializers.CharField(source="cronograma.uuid")
    numero = serializers.CharField(source="cronograma.numero")
    embalagem_primaria = serializers.CharField(
        source="cronograma.ficha_tecnica.embalagem_primaria"
    )
    embalagem_secundaria = serializers.CharField(
        source="cronograma.ficha_tecnica.embalagem_secundaria"
    )
    peso_liquido_embalagem_primaria = serializers.FloatField(
        source="cronograma.ficha_tecnica.peso_liquido_embalagem_primaria"
    )
    peso_liquido_embalagem_secundaria = serializers.FloatField(
        source="cronograma.ficha_tecnica.peso_liquido_embalagem_secundaria"
    )
    sistema_vedacao_embalagem_secundaria = serializers.CharField(
        source="cronograma.ficha_tecnica.sistema_vedacao_embalagem_secundaria"
    )


class FichaDeRecebimentoDetalharSerializer(serializers.ModelSerializer):
    data_recebimento = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    etapa = EtapasDoCronogramaSerializer(read_only=True)
    dados_cronograma = DadosCronogramaSerializer(source="etapa", read_only=True)
    documentos_recebimento = DocRecebimentoFichaDeRecebimentoSerializer(
        many=True, read_only=True
    )
    veiculos = VeiculoFichaDeRecebimentoSerializer(many=True, read_only=True)
    questoes = QuestaoFichaRecebimentoDetailSerializer(
        source="questaoficharecebimento_set", many=True, read_only=True
    )

    ocorrencias = OcorrenciaFichaRecebimentoSerializer(many=True, read_only=True)
    arquivos = ArquivoFichaRecebimentoSerializer(many=True, read_only=True)

    def get_data_recebimento(self, obj):
        try:
            return obj.data_entrega.strftime("%d/%m/%Y") if obj.data_entrega else None
        except AttributeError:
            return None

    class Meta:
        model = FichaDeRecebimento
        fields = (
            "uuid",
            "dados_cronograma",
            "data_recebimento",
            "status",
            "etapa",
            "data_entrega",
            "documentos_recebimento",
            "lote_fabricante_de_acordo",
            "lote_fabricante_divergencia",
            "data_fabricacao_de_acordo",
            "data_fabricacao_divergencia",
            "data_validade_de_acordo",
            "data_validade_divergencia",
            "numero_lote_armazenagem",
            "numero_paletes",
            "peso_embalagem_primaria_1",
            "peso_embalagem_primaria_2",
            "peso_embalagem_primaria_3",
            "peso_embalagem_primaria_4",
            "sistema_vedacao_embalagem_secundaria",
            "observacao",
            "observacoes_conferencia",
            "veiculos",
            "questoes",
            "ocorrencias",
            "arquivos",
        )
