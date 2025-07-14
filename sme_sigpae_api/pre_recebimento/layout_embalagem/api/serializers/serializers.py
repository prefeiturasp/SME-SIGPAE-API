import datetime

from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.layout_embalagem.models import (
    ImagemDoTipoDeEmbalagem,
    LayoutDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)

from .....dados_comuns.api.serializers import (
    LogSolicitacoesUsuarioSimplesSerializer,
)


class ImagemDoTipoEmbalagemLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagemDoTipoDeEmbalagem
        exclude = ("id", "uuid", "tipo_de_embalagem")


class TipoEmbalagemLayoutLookupSerializer(serializers.ModelSerializer):
    imagens = ImagemDoTipoEmbalagemLookupSerializer(many=True)

    class Meta:
        model = TipoDeEmbalagemDeLayout
        exclude = ("id", "layout_de_embalagem")


class LayoutDeEmbalagemSerializer(serializers.ModelSerializer):
    numero_ficha_tecnica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")

    def get_numero_ficha_tecnica(self, obj):
        return obj.ficha_tecnica.numero if obj.ficha_tecnica else None

    def get_nome_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            None

    def get_pregao_chamada_publica(self, obj):
        return obj.ficha_tecnica.pregao_chamada_publica if obj.ficha_tecnica else None

    class Meta:
        model = LayoutDeEmbalagem
        fields = (
            "uuid",
            "numero_ficha_tecnica",
            "pregao_chamada_publica",
            "nome_produto",
            "status",
            "criado_em",
        )


class LayoutDeEmbalagemDetalheSerializer(serializers.ModelSerializer):
    numero_ficha_tecnica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    nome_empresa = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    tipos_de_embalagens = TipoEmbalagemLayoutLookupSerializer(many=True)
    log_mais_recente = serializers.SerializerMethodField()
    primeira_analise = serializers.SerializerMethodField()
    logs = LogSolicitacoesUsuarioSimplesSerializer(many=True)

    def get_numero_ficha_tecnica(self, obj):
        return obj.ficha_tecnica.numero if obj.ficha_tecnica else None

    def get_nome_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            None

    def get_nome_empresa(self, obj):
        try:
            return f"{obj.ficha_tecnica.empresa.nome_fantasia} / {obj.ficha_tecnica.empresa.razao_social}"
        except AttributeError:
            None

    def get_pregao_chamada_publica(self, obj):
        return obj.ficha_tecnica.pregao_chamada_publica if obj.ficha_tecnica else None

    def get_log_mais_recente(self, obj):
        if obj.log_mais_recente:
            return datetime.datetime.strftime(
                obj.log_mais_recente.criado_em, "%d/%m/%Y - %H:%M"
            )
        else:
            return datetime.datetime.strftime(obj.criado_em, "%d/%m/%Y - %H:%M")

    def get_primeira_analise(self, obj):
        return obj.eh_primeira_analise

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if "tipos_de_embalagens" in representation:
            embalagens = representation["tipos_de_embalagens"]
            emb_dict = {emb["tipo_embalagem"]: emb for emb in embalagens}

            ordered_embalagens = [
                emb_dict.get("PRIMARIA"),
                emb_dict.get("SECUNDARIA"),
                emb_dict.get("TERCIARIA"),
            ]
            representation["tipos_de_embalagens"] = ordered_embalagens

        return representation

    class Meta:
        model = LayoutDeEmbalagem
        fields = (
            "uuid",
            "observacoes",
            "criado_em",
            "status",
            "tipos_de_embalagens",
            "numero_ficha_tecnica",
            "pregao_chamada_publica",
            "nome_produto",
            "nome_empresa",
            "log_mais_recente",
            "primeira_analise",
            "logs",
        )


class PainelLayoutEmbalagemSerializer(serializers.ModelSerializer):
    numero_ficha_tecnica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    nome_empresa = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    log_mais_recente = serializers.SerializerMethodField()

    def get_numero_ficha_tecnica(self, obj):
        try:
            return obj.ficha_tecnica.numero
        except AttributeError:
            return ""

    def get_nome_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            return ""

    def get_nome_empresa(self, obj):
        try:
            return obj.ficha_tecnica.empresa.nome_fantasia
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
        model = LayoutDeEmbalagem
        fields = (
            "uuid",
            "numero_ficha_tecnica",
            "nome_produto",
            "nome_empresa",
            "status",
            "log_mais_recente",
        )
