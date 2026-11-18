from django.contrib import admin

from ..models import Lote


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("iniciais", "__str__")
    list_display_links = ("__str__",)
    search_fields = ("iniciais", "nome", "diretoria_regional__nome")
