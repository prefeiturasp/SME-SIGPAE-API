from django.contrib import admin

from src.dados_comuns.constants import StringsSearchHelpText

from .models import (
    AnaliseFichaTecnica,
    FabricanteFichaTecnica,
    FichaTecnicaDoProduto,
    InformacoesNutricionaisFichaTecnica,
)


class InformacoesNutricionaisFichaTecnicaInline(admin.TabularInline):
    model = InformacoesNutricionaisFichaTecnica
    extra = 1


class AnaliseFichaTecnicaInline(admin.StackedInline):
    model = AnaliseFichaTecnica
    extra = 1


class FichaTecnicaDoProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "produto",
        "categoria",
        "empresa",
        "fabricante",
    )
    inlines = (
        InformacoesNutricionaisFichaTecnicaInline,
        AnaliseFichaTecnicaInline,
    )
    search_fields = (
        "produto__nome",
        "numero",
        "categoria",
        "empresa__nome_fantasia",
        "fabricante__fabricante__nome",
    )
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DO_PRODUTO_NUMERO_CATEGORIA_NOME_DA_EMPRESA_NOME_DO_FABRICANTE.value
    )
    list_filter = ("status",)


@admin.register(FabricanteFichaTecnica)
class FabricanteFichaTecnicaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "fabricante", "cidade", "estado", "telefone", "email")
    list_filter = ("estado",)
    search_fields = ("fabricante__nome", "cnpj", "cidade", "email")
    readonly_fields = ("uuid",)


admin.site.register(FichaTecnicaDoProduto, FichaTecnicaDoProdutoAdmin)
