from django.contrib import admin

from .models import (
    UnidadeMedida,
)


@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ("nome", "abreviacao", "criado_em")
    search_fields = ("nome", "abreviacao")
