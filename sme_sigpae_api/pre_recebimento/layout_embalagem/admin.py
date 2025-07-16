from django.contrib import admin
from nested_inline.admin import NestedModelAdmin, NestedStackedInline

from ..forms import ArquivoForm
from .models import (
    ImagemDoTipoDeEmbalagem,
    LayoutDeEmbalagem,
    TipoDeEmbalagemDeLayout,
)


class ImagemDoTipoDeEmbalagemInline(NestedStackedInline):
    model = ImagemDoTipoDeEmbalagem
    extra = 0
    fk_name = "tipo_de_embalagem"
    show_change_link = True


class TipoEmbalagemLayoutInline(NestedStackedInline):
    model = TipoDeEmbalagemDeLayout
    extra = 0
    show_change_link = True
    readonly_fields = ("uuid",)
    fk_name = "layout_de_embalagem"
    inlines = [
        ImagemDoTipoDeEmbalagemInline,
    ]


class LayoutDeEmbalagemAdmin(NestedModelAdmin):
    form = ArquivoForm
    list_display = ("__str__", "get_ficha_tecnica", "get_produto", "criado_em")
    search_fields = ("ficha_tecnica__numero", "produto__nome")
    readonly_fields = ("uuid",)
    inlines = [
        TipoEmbalagemLayoutInline,
    ]

    def get_produto(self, obj):
        try:
            return obj.ficha_tecnica.produto.nome
        except AttributeError:
            return ""

    get_produto.short_description = "Produto"

    def get_ficha_tecnica(self, obj):
        return obj.ficha_tecnica.numero if obj.ficha_tecnica else ""

    get_ficha_tecnica.short_description = "Ficha Técnica"


admin.site.register(LayoutDeEmbalagem, LayoutDeEmbalagemAdmin)
