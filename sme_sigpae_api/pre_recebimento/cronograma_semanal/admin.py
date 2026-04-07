from django.contrib import admin

from .models import CronogramaSemanal, ProgramacaoEntregaSemanal


@admin.register(CronogramaSemanal)
class CronogramaSemanalAdmin(admin.ModelAdmin):
    list_display = ("uuid", "cronograma_mensal", "status", "criado_em")
    list_filter = ("status", "criado_em")
    search_fields = ("uuid", "cronograma_mensal__numero")
    readonly_fields = ("uuid", "criado_em", "alterado_em")
    raw_id_fields = ("cronograma_mensal",)


@admin.register(ProgramacaoEntregaSemanal)
class ProgramacaoEntregaSemanalAdmin(admin.ModelAdmin):
    list_display = ("uuid", "cronograma_semanal", "mes_programado", "data_inicio", "data_fim")
    list_filter = ("mes_programado",)
    search_fields = ("uuid", "cronograma_semanal__uuid")
    readonly_fields = ("uuid",)
    raw_id_fields = ("cronograma_semanal",)
