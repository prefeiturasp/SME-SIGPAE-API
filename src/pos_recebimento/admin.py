from django.contrib import admin

from .models import CronogramaTermoRecebimentoDefinitivo, TermoRecebimentoDefinitivo


class CronogramaTermoRecebimentoDefinitivoInline(admin.TabularInline):
    """Inline dos cronogramas do termo com valor de contrato e quantidade
    total recebida (edição em linha no formulário do termo)."""

    model = CronogramaTermoRecebimentoDefinitivo
    extra = 0
    fields = ("cronograma", "valor_contrato", "quantidade_total_recebida")


@admin.register(TermoRecebimentoDefinitivo)
class TermoRecebimentoDefinitivoAdmin(admin.ModelAdmin):
    """Admin do Termo de Recebimento Definitivo com inline dos cronogramas."""

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
    """Admin dos cronogramas vinculados aos termos de recebimento definitivo."""

    list_display = (
        "termo",
        "cronograma",
        "valor_contrato",
        "quantidade_total_recebida",
    )
    search_fields = ("termo__uuid", "cronograma__numero")
