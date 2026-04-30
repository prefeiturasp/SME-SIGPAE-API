from django.contrib import admin

from .models import CronogramaSemanal, ProgramacaoEntregaSemanal


class ProgramacaoEntregaSemanalInline(admin.TabularInline):
    model = ProgramacaoEntregaSemanal
    extra = 0
    readonly_fields = ("uuid",)
    fields = ("uuid", "mes_programado", "data_inicio", "data_fim", "quantidade")


@admin.register(CronogramaSemanal)
class CronogramaSemanalAdmin(admin.ModelAdmin):
    list_display = ("numero", "cronograma_mensal", "status", "criado_em")
    list_filter = ("status", "criado_em")
    search_fields = ("numero", "cronograma_mensal__numero")
    readonly_fields = ("uuid", "numero", "criado_em", "alterado_em")
    raw_id_fields = ("cronograma_mensal",)
    inlines = [ProgramacaoEntregaSemanalInline]


@admin.register(ProgramacaoEntregaSemanal)
class ProgramacaoEntregaSemanalAdmin(admin.ModelAdmin):
    list_display = ("uuid", "cronograma_semanal", "mes_programado", "data_inicio", "data_fim")
    list_filter = ("mes_programado",)
    search_fields = ("uuid", "cronograma_semanal__uuid")
    readonly_fields = ("uuid",)
    raw_id_fields = ("cronograma_semanal",)
