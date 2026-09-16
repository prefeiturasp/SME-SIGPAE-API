from django.contrib import admin
from nested_inline.admin import NestedModelAdmin, NestedStackedInline

from ..forms import ArquivoForm
from .models import (
    ArquivoDoTipoDeDocumento,
    DataDeFabricaoEPrazo,
    DocumentoDeRecebimento,
    TipoDeDocumentoDeRecebimento,
)


class ArquivoDoTipoDeDocumentoInline(NestedStackedInline):
    """Inline dos arquivos de um tipo de documento (aninhada ao inline de tipos)."""

    model = ArquivoDoTipoDeDocumento
    extra = 0
    fk_name = "tipo_de_documento"
    show_change_link = True


class TipoDocumentoRecebimentoInline(NestedStackedInline):
    """Inline dos tipos de documento do recebimento, com os arquivos aninhados."""

    model = TipoDeDocumentoDeRecebimento
    extra = 0
    show_change_link = True
    readonly_fields = ("uuid",)
    fk_name = "documento_recebimento"
    inlines = [
        ArquivoDoTipoDeDocumentoInline,
    ]


class DocumentoDeRecebimentoAdmin(NestedModelAdmin):
    """Admin do Documento de Recebimento com inlines aninhadas de tipos e arquivos."""

    form = ArquivoForm
    list_display = ("get_cronograma", "get_produto", "numero_laudo", "criado_em")
    search_fields = ("cronograma__numero", "cronograma__ficha_tecnica__produto__nome")
    readonly_fields = ("uuid",)
    inlines = [
        TipoDocumentoRecebimentoInline,
    ]

    def get_produto(self, obj):
        try:
            return obj.cronograma.ficha_tecnica.produto.nome
        except AttributeError:
            return ""

    get_produto.short_description = "Produto"

    def get_cronograma(self, obj):
        return obj.cronograma.numero

    get_cronograma.short_description = "Cronograma"


admin.site.register(DocumentoDeRecebimento, DocumentoDeRecebimentoAdmin)
admin.site.register(DataDeFabricaoEPrazo)
