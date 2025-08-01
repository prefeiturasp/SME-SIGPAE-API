import datetime

from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.base.api.serializers.serializers import (
    UnidadeMedidaSimplesSerializer,
)
from sme_sigpae_api.pre_recebimento.documento_recebimento.models import (
    ArquivoDoTipoDeDocumento,
    DataDeFabricaoEPrazo,
    DocumentoDeRecebimento,
    TipoDeDocumentoDeRecebimento,
)
from sme_sigpae_api.pre_recebimento.qualidade.api.serializers.serializers import (
    LaboratorioCredenciadoSimplesSerializer,
)

from .....dados_comuns.api.serializers import (
    LogSolicitacoesUsuarioSimplesSerializer,
)


class DocRecebimentoFichaDeRecebimentoSerializer(serializers.ModelSerializer):
    datas_fabricacao = serializers.SerializerMethodField()
    datas_validade = serializers.SerializerMethodField()

    def get_datas_fabricacao(self, obj):
        try:
            return ", ".join(
                [
                    d.strftime("%d/%m/%Y")
                    for d in obj.datas_fabricacao_e_prazos.values_list(
                        "data_fabricacao", flat=True
                    )
                ]
            )

        except AttributeError:
            return None

    def get_datas_validade(self, obj):
        try:
            return ", ".join(
                [
                    d.strftime("%d/%m/%Y")
                    for d in obj.datas_fabricacao_e_prazos.values_list(
                        "data_validade", flat=True
                    )
                ]
            )

        except AttributeError:
            return None

    class Meta:
        model = DocumentoDeRecebimento
        fields = (
            "uuid",
            "numero_laudo",
            "numero_lote_laudo",
            "datas_fabricacao",
            "datas_validade",
        )


class DocumentoDeRecebimentoSerializer(serializers.ModelSerializer):
    criado_em = serializers.SerializerMethodField()
    numero_cronograma = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")

    def get_numero_cronograma(self, obj):
        return obj.cronograma.numero if obj.cronograma else None

    def get_pregao_chamada_publica(self, obj):
        return (
            obj.cronograma.contrato.pregao_chamada_publica
            if obj.cronograma.contrato
            else None
        )

    def get_nome_produto(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            None

    def get_criado_em(self, obj):
        return obj.criado_em.strftime("%d/%m/%Y")

    class Meta:
        model = DocumentoDeRecebimento
        fields = (
            "uuid",
            "numero_cronograma",
            "numero_laudo",
            "pregao_chamada_publica",
            "nome_produto",
            "status",
            "criado_em",
        )


class PainelDocumentoDeRecebimentoSerializer(serializers.ModelSerializer):
    numero_cronograma = serializers.CharField(source="cronograma.numero")
    nome_produto = serializers.SerializerMethodField()
    nome_empresa = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    log_mais_recente = serializers.SerializerMethodField()

    def get_nome_produto(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            return ""

    def get_nome_empresa(self, obj):
        try:
            return obj.cronograma.empresa.nome_fantasia
        except AttributeError:
            return ""

    def get_log_mais_recente(self, obj):
        if obj.log_mais_recente:
            if obj.log_mais_recente.criado_em.date() == datetime.date.today():
                return datetime.datetime.strftime(
                    obj.log_mais_recente.criado_em, "%d/%m/%Y %H:%M"
                )
            return datetime.datetime.strftime(
                obj.log_mais_recente.criado_em, "%d/%m/%Y"
            )
        else:
            return datetime.datetime.strftime(obj.criado_em, "%d/%m/%Y")

    class Meta:
        model = DocumentoDeRecebimento
        fields = (
            "uuid",
            "numero_cronograma",
            "nome_produto",
            "nome_empresa",
            "status",
            "log_mais_recente",
        )


class ArquivoDoTipoDeDocumentoLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArquivoDoTipoDeDocumento
        exclude = ("id", "uuid", "tipo_de_documento")


class TipoDocumentoDeRecebimentoLookupSerializer(serializers.ModelSerializer):
    arquivos = ArquivoDoTipoDeDocumentoLookupSerializer(many=True)

    class Meta:
        model = TipoDeDocumentoDeRecebimento
        exclude = ("id", "documento_recebimento")


class DocRecebimentoDetalharSerializer(serializers.ModelSerializer):
    criado_em = serializers.SerializerMethodField()
    numero_cronograma = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    tipos_de_documentos = TipoDocumentoDeRecebimentoLookupSerializer(many=True)
    logs = LogSolicitacoesUsuarioSimplesSerializer(many=True)

    def get_numero_cronograma(self, obj):
        return obj.cronograma.numero if obj.cronograma else None

    def get_pregao_chamada_publica(self, obj):
        return (
            obj.cronograma.contrato.pregao_chamada_publica
            if obj.cronograma.contrato
            else None
        )

    def get_nome_produto(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            return None

    def get_criado_em(self, obj):
        return obj.criado_em.strftime("%d/%m/%Y")

    class Meta:
        model = DocumentoDeRecebimento
        fields = (
            "uuid",
            "numero_cronograma",
            "pregao_chamada_publica",
            "nome_produto",
            "numero_laudo",
            "status",
            "criado_em",
            "tipos_de_documentos",
            "correcao_solicitada",
            "logs",
        )


class DataDeFabricacaoEPrazoLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDeFabricaoEPrazo
        exclude = ("id", "documento_recebimento")


class DocRecebimentoDetalharCodaeSerializer(DocRecebimentoDetalharSerializer):
    laboratorio = LaboratorioCredenciadoSimplesSerializer()
    unidade_medida = UnidadeMedidaSimplesSerializer()
    datas_fabricacao_e_prazos = DataDeFabricacaoEPrazoLookupSerializer(many=True)
    numero_sei = serializers.SerializerMethodField()
    fornecedor = serializers.SerializerMethodField()

    def get_numero_sei(self, obj):
        return obj.cronograma.contrato.processo if obj.cronograma.contrato else None

    def get_fornecedor(self, obj):
        return obj.cronograma.empresa.nome_fantasia if obj.cronograma.empresa else None

    class Meta(DocRecebimentoDetalharSerializer.Meta):
        fields = DocRecebimentoDetalharSerializer.Meta.fields + (
            "fornecedor",
            "numero_sei",
            "laboratorio",
            "quantidade_laudo",
            "unidade_medida",
            "saldo_laudo",
            "numero_lote_laudo",
            "data_final_lote",
            "datas_fabricacao_e_prazos",
            "correcao_solicitada",
        )
