from django.contrib import admin

from ..models import DiretoriaRegional


@admin.register(DiretoriaRegional)
class DiretoriaRegionalAdmin(admin.ModelAdmin):
    list_display = ("iniciais", "__str__")
    list_display_links = ("__str__",)
    search_fields = ("codigo_eol", "nome")
    list_filter = ("acesso_modulo_medicao_inicial",)
