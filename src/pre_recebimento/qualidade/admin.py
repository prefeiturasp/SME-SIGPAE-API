from django.contrib import admin

from ..forms import CaixaAltaNomeForm
from .models import (
    Laboratorio,
    TipoEmbalagemQld,
)


@admin.register(Laboratorio)
class Laboratoriodmin(admin.ModelAdmin):
    form = CaixaAltaNomeForm
    list_display = ("nome", "cnpj", "cidade", "credenciado")
    ordering = ("-criado_em",)
    search_fields = ("nome",)
    list_filter = ("nome",)
    readonly_fields = ("uuid",)


@admin.register(TipoEmbalagemQld)
class EmbalagemQldAdmin(admin.ModelAdmin):
    form = CaixaAltaNomeForm
    list_display = ("nome", "abreviacao", "criado_em")
    search_fields = ("nome",)
    readonly_fields = ("uuid",)
