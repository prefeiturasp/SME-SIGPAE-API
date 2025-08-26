from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    DocRecebimentoFichaDeRecebimentoSerializer,
)
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


class FichaDeRecebimentoDetalharSerializer(serializers.ModelSerializer):
    data_recebimento = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    etapa = serializers.SerializerMethodField()
    dados_cronograma = serializers.SerializerMethodField()
    documentos_recebimento = DocRecebimentoFichaDeRecebimentoSerializer(
        many=True, read_only=True
    )
    veiculos = serializers.SerializerMethodField()
    questoes = serializers.SerializerMethodField()
    ocorrencias = serializers.SerializerMethodField()
    arquivos = serializers.SerializerMethodField()

    def get_data_recebimento(self, obj):
        try:
            return obj.data_entrega.strftime("%d/%m/%Y") if obj.data_entrega else None
        except AttributeError:
            return None

    def get_etapa(self, obj):
        if obj.etapa:
            return {
                "uuid": obj.etapa.uuid,
                "etapa": obj.etapa.etapa,
                "data_programada": (
                    obj.etapa.data_programada.strftime("%Y-%m-%d")
                    if obj.etapa.data_programada
                    else None
                ),
                "numero_empenho": obj.etapa.numero_empenho,
                "parte": obj.etapa.parte,
                "qtd_total_empenho": obj.etapa.qtd_total_empenho,
                "quantidade": obj.etapa.quantidade,
                "total_embalagens": obj.etapa.total_embalagens,
            }
        return None

    def get_dados_cronograma(self, obj):
        try:
            cronograma = obj.etapa.cronograma
            ficha_tecnica = cronograma.ficha_tecnica
            return {
                "uuid": cronograma.uuid,
                "numero": cronograma.numero,
                "embalagem_primaria": (
                    ficha_tecnica.embalagem_primaria if ficha_tecnica else None
                ),
                "embalagem_secundaria": (
                    ficha_tecnica.embalagem_secundaria if ficha_tecnica else None
                ),
                "peso_liquido_embalagem_primaria": (
                    ficha_tecnica.peso_liquido_embalagem_primaria
                    if ficha_tecnica
                    else None
                ),
                "peso_liquido_embalagem_secundaria": (
                    ficha_tecnica.peso_liquido_embalagem_secundaria
                    if ficha_tecnica
                    else None
                ),
                "sistema_vedacao_embalagem_secundaria": (
                    ficha_tecnica.sistema_vedacao_embalagem_secundaria
                    if ficha_tecnica
                    else None
                ),
            }
        except AttributeError:
            return None

    def get_veiculos(self, obj):
        return [
            {
                "uuid": veiculo.uuid if hasattr(veiculo, "uuid") else None,
                "numero": veiculo.numero,
                "temperatura_recebimento": veiculo.temperatura_recebimento,
                "temperatura_produto": veiculo.temperatura_produto,
                "placa": getattr(veiculo, "placa", None),
                "lacre": getattr(veiculo, "lacre", None),
                "numero_sif_sisbi_sisp": getattr(
                    veiculo, "numero_sif_sisbi_sisp", None
                ),
                "numero_nota_fiscal": getattr(veiculo, "numero_nota_fiscal", None),
                "quantidade_nota_fiscal": getattr(
                    veiculo, "quantidade_nota_fiscal", None
                ),
                "embalagens_nota_fiscal": getattr(
                    veiculo, "embalagens_nota_fiscal", None
                ),
                "quantidade_recebida": getattr(veiculo, "quantidade_recebida", None),
                "embalagens_recebidas": getattr(veiculo, "embalagens_recebidas", None),
                "estado_higienico_adequado": getattr(
                    veiculo, "estado_higienico_adequado", None
                ),
                "termografo": getattr(veiculo, "termografo", None),
            }
            for veiculo in obj.veiculos.all()
        ]

    def get_questoes(self, obj):
        return [
            {
                "uuid": questao.uuid if hasattr(questao, "uuid") else None,
                "questao_conferencia": (
                    questao.questao_conferencia.uuid
                    if questao.questao_conferencia
                    else None
                ),
                "tipo_questao": getattr(questao, "tipo_questao", None),
                "resposta": questao.resposta,
            }
            for questao in obj.questaoficharecebimento_set.all()
        ]

    def get_ocorrencias(self, obj):
        return [
            {
                "uuid": ocorrencia.uuid if hasattr(ocorrencia, "uuid") else None,
                "tipo": ocorrencia.tipo,
                "relacao": getattr(ocorrencia, "relacao", None),
                "numero_nota": getattr(ocorrencia, "numero_nota", None),
                "quantidade": getattr(ocorrencia, "quantidade", None),
                "descricao": ocorrencia.descricao,
            }
            for ocorrencia in obj.ocorrencias.all()
        ]

    def get_arquivos(self, obj):
        return [
            {
                "uuid": arquivo.uuid if hasattr(arquivo, "uuid") else None,
                "nome": arquivo.nome if hasattr(arquivo, "nome") else None,
                "arquivo": (
                    arquivo.arquivo.url
                    if hasattr(arquivo, "arquivo") and arquivo.arquivo
                    else None
                ),
            }
            for arquivo in obj.arquivos.all()
        ]

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
