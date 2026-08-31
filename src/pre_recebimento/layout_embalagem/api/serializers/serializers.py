"""Serializers de leitura do submódulo de layout de embalagem."""

import datetime

from rest_framework import serializers

from src.dados_comuns.constants import (
    FORMATO_DATA_BRASILEIRO,
    FORMATO_DATA_HORA_BRASILEIRO,
)
from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto
from src.pre_recebimento.layout_embalagem.models import (
    ImagemDoTipoDeEmbalagem,
    LayoutDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)

from .....dados_comuns.api.serializers import (
    LogSolicitacoesUsuarioSimplesSerializer,
)


class ImagemDoTipoEmbalagemLookupSerializer(serializers.ModelSerializer):
    """Serializer de leitura das imagens de um tipo de embalagem."""

    class Meta:
        model = ImagemDoTipoDeEmbalagem
        exclude = ("id", "tipo_de_embalagem")


class TipoEmbalagemLayoutLookupSerializer(serializers.ModelSerializer):
    """Serializer de leitura dos tipos de embalagem de um layout.

    Inclui as ``imagens`` de cada tipo de embalagem.
    """

    imagens = ImagemDoTipoEmbalagemLookupSerializer(many=True)

    class Meta:
        model = TipoDeEmbalagemDeLayout
        exclude = ("id", "layout_de_embalagem")


class LayoutDeEmbalagemSerializer(serializers.ModelSerializer):
    """Serializer de listagem dos layouts de embalagem.

    Expõe dados resumidos do layout: número da ficha técnica, pregão/chamada
    pública, nome do produto, status (texto), data de criação e programa.
    """

    numero_ficha_tecnica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    programa = serializers.SerializerMethodField()

    def get_numero_ficha_tecnica(self, obj):
        return obj.ficha_tecnica.numero if obj.ficha_tecnica else None

    def get_nome_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            None

    def get_pregao_chamada_publica(self, obj):
        return obj.ficha_tecnica.pregao_chamada_publica if obj.ficha_tecnica else None

    def get_programa(self, obj):
        return obj.ficha_tecnica.programa if obj.ficha_tecnica else None

    class Meta:
        model = LayoutDeEmbalagem
        fields = (
            "uuid",
            "numero_ficha_tecnica",
            "pregao_chamada_publica",
            "nome_produto",
            "status",
            "criado_em",
            "programa",
        )


class LayoutDeEmbalagemDetalheSerializer(serializers.ModelSerializer):
    """Serializer de detalhe dos layouts de embalagem.

    Expõe todos os dados do layout, incluindo os tipos de embalagem (com
    suas imagens, ordenados por primária/secundária/terciária), o log mais
    recente, a indicação de primeira análise e o histórico de logs.
    """

    numero_ficha_tecnica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    nome_empresa = serializers.SerializerMethodField()
    pregao_chamada_publica = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    tipos_de_embalagens = TipoEmbalagemLayoutLookupSerializer(many=True)
    log_mais_recente = serializers.SerializerMethodField()
    primeira_analise = serializers.SerializerMethodField()
    logs = LogSolicitacoesUsuarioSimplesSerializer(many=True)
    programa = serializers.SerializerMethodField()

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
                obj.log_mais_recente.criado_em, FORMATO_DATA_HORA_BRASILEIRO
            )
        else:
            return datetime.datetime.strftime(
                obj.criado_em, FORMATO_DATA_HORA_BRASILEIRO
            )

    def get_primeira_analise(self, obj):
        return obj.eh_primeira_analise

    def get_programa(self, obj):
        return obj.ficha_tecnica.programa if obj.ficha_tecnica else None

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
            "programa",
        )


class PainelLayoutEmbalagemSerializer(serializers.ModelSerializer):
    """Serializer do painel/dashboard de layouts de embalagem.

    Expõe os dados exibidos nos cards do dashboard: número da ficha
    técnica, produto, empresa, status, log mais recente e indicadores de
    programa (``LEVE_LEITE``) e de ficha técnica FLV.
    """

    numero_ficha_tecnica = serializers.SerializerMethodField()
    nome_produto = serializers.SerializerMethodField()
    nome_empresa = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    log_mais_recente = serializers.SerializerMethodField()
    programa_leve_leite = serializers.SerializerMethodField()
    eh_ficha_tecnica_flv = serializers.SerializerMethodField()

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
                obj.log_mais_recente.criado_em, FORMATO_DATA_BRASILEIRO
            )

        return datetime.datetime.strftime(obj.criado_em, FORMATO_DATA_BRASILEIRO)

    def get_programa_leve_leite(self, obj):
        try:
            return obj.ficha_tecnica.programa == "LEVE_LEITE"
        except AttributeError:
            return None

    def get_eh_ficha_tecnica_flv(self, obj):
        try:
            print(FichaTecnicaDoProduto)
            return obj.ficha_tecnica.categoria == FichaTecnicaDoProduto.CATEGORIA_FLV
        except AttributeError:
            return False

    class Meta:
        model = LayoutDeEmbalagem
        fields = (
            "uuid",
            "numero_ficha_tecnica",
            "nome_produto",
            "nome_empresa",
            "status",
            "log_mais_recente",
            "programa_leve_leite",
            "eh_ficha_tecnica_flv",
        )
