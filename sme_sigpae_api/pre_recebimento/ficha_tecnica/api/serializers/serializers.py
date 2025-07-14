import datetime

from rest_framework import serializers
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import (
    AnaliseFichaTecnica,
    InformacoesNutricionaisFichaTecnica,
)
from sme_sigpae_api.produto.api.serializers.serializers import (
    FabricanteSimplesSerializer,
    InformacaoNutricionalSerializer,
    MarcaSimplesSerializer,
    NomeDeProdutoEditalSerializer,
)
from sme_sigpae_api.terceirizada.api.serializers.serializers import (
    TerceirizadaLookUpSerializer,
)
from sme_sigpae_api.pre_recebimento.base.api.serializers.serializers import (
    UnidadeMedidaSimplesSerializer,
)

from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FabricanteFichaTecnica, FichaTecnicaDoProduto


class FichaTecnicaSimplesSerializer(serializers.ModelSerializer):
    produto = NomeDeProdutoEditalSerializer()
    uuid_empresa = serializers.SerializerMethodField()

    def get_uuid_empresa(self, obj):
        return obj.empresa.uuid if obj.empresa else None

    class Meta:
        model = FichaTecnicaDoProduto
        fields = (
            "uuid",
            "numero",
            "produto",
            "uuid_empresa",
            "pregao_chamada_publica",
        )


class FichaTecnicaCronogramaSerializer(FichaTecnicaSimplesSerializer):
    marca = MarcaSimplesSerializer()
    unidade_medida_volume_primaria = UnidadeMedidaSimplesSerializer()
    unidade_medida_primaria = UnidadeMedidaSimplesSerializer()
    unidade_medida_secundaria = UnidadeMedidaSimplesSerializer()

    class Meta(FichaTecnicaSimplesSerializer.Meta):
        fields = FichaTecnicaSimplesSerializer.Meta.fields + (
            "marca",
            "volume_embalagem_primaria",
            "unidade_medida_volume_primaria",
            "peso_liquido_embalagem_primaria",
            "unidade_medida_primaria",
            "peso_liquido_embalagem_secundaria",
            "unidade_medida_secundaria",
        )


class FichaTecnicaListagemSerializer(serializers.ModelSerializer):
    nome_produto = serializers.SerializerMethodField()
    criado_em = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")

    def get_nome_produto(self, obj):
        return obj.produto.nome if obj.produto else None

    def get_criado_em(self, obj):
        return obj.criado_em.strftime("%d/%m/%Y")

    class Meta:
        model = FichaTecnicaDoProduto
        fields = (
            "uuid",
            "numero",
            "nome_produto",
            "pregao_chamada_publica",
            "criado_em",
            "status",
        )


class InformacoesNutricionaisFichaTecnicaSerializer(serializers.ModelSerializer):
    informacao_nutricional = InformacaoNutricionalSerializer()

    class Meta:
        model = InformacoesNutricionaisFichaTecnica
        fields = (
            "uuid",
            "informacao_nutricional",
            "quantidade_por_100g",
            "quantidade_porcao",
            "valor_diario",
        )
        read_only_fields = ("uuid",)


class FabricanteFichaTecnicaSerializer(serializers.ModelSerializer):
    fabricante = FabricanteSimplesSerializer()

    class Meta:
        model = FabricanteFichaTecnica
        fields = (
            "uuid",
            "fabricante",
            "cnpj",
            "cep",
            "endereco",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "estado",
            "email",
            "telefone",
        )


class FichaTecnicaDetalharSerializer(serializers.ModelSerializer):
    criado_em = serializers.SerializerMethodField()
    produto = NomeDeProdutoEditalSerializer()
    marca = MarcaSimplesSerializer()
    empresa = TerceirizadaLookUpSerializer()
    fabricante = FabricanteFichaTecnicaSerializer()
    envasador_distribuidor = FabricanteFichaTecnicaSerializer()
    unidade_medida_porcao = UnidadeMedidaSimplesSerializer()
    status = serializers.CharField(source="get_status_display", read_only=True)
    informacoes_nutricionais = InformacoesNutricionaisFichaTecnicaSerializer(many=True)
    unidade_medida_primaria = UnidadeMedidaSimplesSerializer()
    unidade_medida_secundaria = UnidadeMedidaSimplesSerializer()
    unidade_medida_primaria_vazia = UnidadeMedidaSimplesSerializer()
    unidade_medida_secundaria_vazia = UnidadeMedidaSimplesSerializer()
    unidade_medida_volume_primaria = UnidadeMedidaSimplesSerializer()

    def get_criado_em(self, obj):
        return obj.criado_em.strftime("%d/%m/%Y")

    class Meta:
        model = FichaTecnicaDoProduto
        fields = (
            "uuid",
            "numero",
            "produto",
            "pregao_chamada_publica",
            "marca",
            "categoria",
            "status",
            "criado_em",
            "empresa",
            "fabricante",
            "envasador_distribuidor",
            "prazo_validade",
            "numero_registro",
            "agroecologico",
            "organico",
            "mecanismo_controle",
            "componentes_produto",
            "alergenicos",
            "ingredientes_alergenicos",
            "gluten",
            "lactose",
            "lactose_detalhe",
            "porcao",
            "unidade_medida_porcao",
            "valor_unidade_caseira",
            "unidade_medida_caseira",
            "informacoes_nutricionais",
            "prazo_validade_descongelamento",
            "condicoes_de_conservacao",
            "temperatura_congelamento",
            "temperatura_veiculo",
            "condicoes_de_transporte",
            "embalagem_primaria",
            "embalagem_secundaria",
            "embalagens_de_acordo_com_anexo",
            "material_embalagem_primaria",
            "produto_eh_liquido",
            "volume_embalagem_primaria",
            "unidade_medida_volume_primaria",
            "peso_liquido_embalagem_primaria",
            "unidade_medida_primaria",
            "peso_liquido_embalagem_secundaria",
            "unidade_medida_secundaria",
            "peso_embalagem_primaria_vazia",
            "unidade_medida_primaria_vazia",
            "peso_embalagem_secundaria_vazia",
            "unidade_medida_secundaria_vazia",
            "variacao_percentual",
            "sistema_vedacao_embalagem_secundaria",
            "rotulo_legivel",
            "nome_responsavel_tecnico",
            "habilitacao",
            "numero_registro_orgao",
            "arquivo",
            "modo_de_preparo",
            "informacoes_adicionais",
        )


class AnaliseFichaTecnicaSerializer(serializers.ModelSerializer):
    aprovada = serializers.BooleanField()

    class Meta:
        model = AnaliseFichaTecnica
        exclude = ("id", "ficha_tecnica")


class FichaTecnicaComAnaliseDetalharSerializer(FichaTecnicaDetalharSerializer):
    analise = serializers.SerializerMethodField()
    log_mais_recente = serializers.SerializerMethodField()

    def get_analise(self, obj):
        analise_mais_recente = obj.analises.order_by("-criado_em").first()

        return (
            AnaliseFichaTecnicaSerializer(analise_mais_recente).data
            if analise_mais_recente
            else None
        )

    def get_log_mais_recente(self, obj):
        log_mais_recente = obj.log_mais_recente

        if log_mais_recente:
            return datetime.datetime.strftime(
                log_mais_recente.criado_em, "%d/%m/%Y - %H:%M"
            )

        else:
            return datetime.datetime.strftime(obj.alterado_em, "%d/%m/%Y - %H:%M")

    class Meta(FichaTecnicaDetalharSerializer.Meta):
        fields = FichaTecnicaDetalharSerializer.Meta.fields + (
            "analise",
            "log_mais_recente",
        )


class PainelFichaTecnicaSerializer(serializers.ModelSerializer):
    numero_ficha = serializers.CharField(source="numero")
    nome_produto = serializers.CharField(source="produto.nome")
    nome_empresa = serializers.CharField(source="empresa.nome_fantasia")
    status = serializers.CharField(source="get_status_display")
    log_mais_recente = serializers.SerializerMethodField()

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
        model = FichaTecnicaDoProduto
        fields = (
            "uuid",
            "numero_ficha",
            "nome_produto",
            "nome_empresa",
            "status",
            "log_mais_recente",
        )
