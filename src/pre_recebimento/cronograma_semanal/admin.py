"""Configuração do Django Admin do submódulo de cronograma semanal."""

from django.contrib import admin

from .models import CronogramaSemanal, ProgramacaoEntregaSemanal


class ProgramacaoEntregaSemanalInline(admin.TabularInline):
    """Inline das programações de entrega semanais do cronograma semanal."""

    model = ProgramacaoEntregaSemanal
    extra = 0
    readonly_fields = ("uuid",)
    fields = ("uuid", "mes_programado", "data_inicio", "data_fim", "quantidade")


@admin.register(CronogramaSemanal)
class CronogramaSemanalAdmin(admin.ModelAdmin):
    """Admin dos cronogramas semanais.

    Exibe ``numero``, ``cronograma_mensal``, ``status`` e ``criado_em`` na
    listagem; filtra por ``status`` e ``criado_em``; busca por número do
    cronograma semanal ou do cronograma mensal. ``uuid``, ``numero``,
    ``criado_em`` e ``alterado_em`` são somente leitura.
    """

    list_display = ("numero", "cronograma_mensal", "status", "criado_em")
    list_filter = ("status", "criado_em")
    search_fields = ("numero", "cronograma_mensal__numero")
    readonly_fields = ("uuid", "numero", "criado_em", "alterado_em")
    raw_id_fields = ("cronograma_mensal",)
    inlines = [ProgramacaoEntregaSemanalInline]


@admin.register(ProgramacaoEntregaSemanal)
class ProgramacaoEntregaSemanalAdmin(admin.ModelAdmin):
    """Admin das programações de entrega semanais.

    Exibe ``uuid``, ``cronograma_semanal``, ``mes_programado``,
    ``data_inicio`` e ``data_fim`` na listagem; filtra por
    ``mes_programado``. ``uuid`` é somente leitura.
    """
