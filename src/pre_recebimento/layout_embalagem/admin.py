"""Configuração do Django Admin do submódulo de layout de embalagem."""

from django.contrib import admin
from nested_inline.admin import NestedModelAdmin, NestedStackedInline

from ..forms import ArquivoForm
from .models import (
    ImagemDoTipoDeEmbalagem,
    LayoutDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)


class ImagemDoTipoDeEmbalagemInline(NestedStackedInline):
    """Inline das imagens de um tipo de embalagem de layout."""

    model = ImagemDoTipoDeEmbalagem
    extra = 0
    fk_name = "tipo_de_embalagem"
    show_change_link = True


class TipoEmbalagemLayoutInline(NestedStackedInline):
    """Inline dos tipos de embalagem de um layout."""

    model = TipoDeEmbalagemDeLayout
    extra = 0
    show_change_link = True
    readonly_fields = ("uuid",)
    fk_name = "layout_de_embalagem"
    inlines = [
        ImagemDoTipoDeEmbalagemInline,
    ]


class LayoutDeEmbalagemAdmin(NestedModelAdmin):
    """Admin dos layouts de embalagem.

    Exibe a representação textual do layout, ficha técnica, produto e
    ``criado_em`` na listagem; busca por número da ficha técnica ou nome
    do produto; ``uuid`` é somente leitura. Os tipos de embalagem e suas
    imagens são editados em inline aninhados.
    """

    form = ArquivoForm
    list_display = ("__str__", "get_ficha_tecnica", "get_produto", "criado_em")
    search_fields = ("ficha_tecnica__numero", "produto__nome")
    readonly_fields = ("uuid",)
    inlines = [
        TipoEmbalagemLayoutInline,
    ]

    def get_produto(self, obj):
        """Retorna o nome do produto da ficha técnica do layout."""
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            return ""

    get_produto.short_description = "Produto"

    def get_ficha_tecnica(self, obj):
        """Retorna o número da ficha técnica do layout."""
        return obj.ficha_tecnica.numero if obj.ficha_tecnica else ""

    get_ficha_tecnica.short_description = "Ficha Técnica"


admin.site.register(LayoutDeEmbalagem, LayoutDeEmbalagemAdmin)
