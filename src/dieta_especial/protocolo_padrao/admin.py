from django.contrib import admin

from .models import (
    Alimento,
    ProtocoloPadraoDietaEspecial,
    SubstituicaoAlimento,
    SubstituicaoAlimentoProtocoloPadrao,
)


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    ordering = ("nome",)
    list_filter = ("tipo_listagem_protocolo",)


class SubstituicaoAlimentoInline(admin.TabularInline):
    model = SubstituicaoAlimento
    extra = 0


class SubstituicaoAlimentoProtocoloPadraoInline(admin.TabularInline):
    model = SubstituicaoAlimentoProtocoloPadrao
    filter_horizontal = ("substitutos",)
    extra = 0


@admin.register(ProtocoloPadraoDietaEspecial)
class ProtocoloPadraoDietaEspecialAdmin(admin.ModelAdmin):
    list_display = ("nome_protocolo", "status")
    search_fields = ("nome_protocolo",)
    inlines = (SubstituicaoAlimentoProtocoloPadraoInline,)


admin.site.register(SubstituicaoAlimento)
admin.site.register(SubstituicaoAlimentoProtocoloPadrao)
