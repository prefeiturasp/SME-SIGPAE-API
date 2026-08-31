"""Configuração do Django Admin do submódulo base de pré-recebimento."""

from django.contrib import admin

from .models import (
    UnidadeMedida,
)


@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    """Admin das unidades de medida.

    Exibe ``nome``, ``abreviacao`` e ``criado_em`` na listagem e permite
    busca por nome e abreviação.
    """
