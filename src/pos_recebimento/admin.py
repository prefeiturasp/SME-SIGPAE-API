from django.contrib import admin

from .models import CronogramaTermoRecebimentoDefinitivo, TermoRecebimentoDefinitivo


class CronogramaTermoRecebimentoDefinitivoInline(admin.TabularInline):
    model = CronogramaTermoRecebimentoDefinitivo
    extra = 0
    fields = ("cronograma", "valor_contrato", "quantidade_total_recebida")


@admin.register(TermoRecebimentoDefinitivo)
class TermoRecebimentoDefinitivoAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "empresa",
        "contrato",
        "status",
        "criado_em",
        "alterado_em",
    )
    inlines = (CronogramaTermoRecebimentoDefinitivoInline,)
    readonly_fields = ("uuid", "criado_em", "alterado_em", "criado_por")
    search_fields = ("empresa__nome_fantasia", "contrato__numero", "uuid")
    list_filter = ("status",)


@admin.register(CronogramaTermoRecebimentoDefinitivo)
class CronogramaTermoRecebimentoDefinitivoAdmin(admin.ModelAdmin):
    list_display = (
        "termo",
        "cronograma",
        "valor_contrato",
        "quantidade_total_recebida",
    )
    search_fields = ("termo__uuid", "cronograma__numero")
