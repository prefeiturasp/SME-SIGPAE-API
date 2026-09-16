"""Configuração do Django Admin do submódulo de qualidade."""

from django.contrib import admin

from ..forms import CaixaAltaNomeForm
from .models import (
    Laboratorio,
    TipoEmbalagemQld,
)


@admin.register(Laboratorio)
class Laboratoriodmin(admin.ModelAdmin):
    """Admin dos laboratórios.

    Exibe ``nome``, ``cnpj``, ``cidade`` e ``credenciado`` na listagem,
    ordena por ``-criado_em``, busca por nome e filtra por nome. O campo
    ``nome`` é normalizado em letras maiúsculas (``CaixaAltaNomeForm``) e
    ``uuid`` é somente leitura.
    """

    form = CaixaAltaNomeForm
    list_display = ("nome", "cnpj", "cidade", "credenciado")
    ordering = ("-criado_em",)
    search_fields = ("nome",)
    list_filter = ("nome",)
    readonly_fields = ("uuid",)


@admin.register(TipoEmbalagemQld)
class EmbalagemQldAdmin(admin.ModelAdmin):
    """Admin dos tipos de embalagem (qualidade).

    Exibe ``nome``, ``abreviacao`` e ``criado_em`` na listagem e busca por
    nome. O campo ``nome`` é normalizado em letras maiúsculas
    (``CaixaAltaNomeForm``) e ``uuid`` é somente leitura.
    """
