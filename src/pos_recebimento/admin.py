from django.contrib import admin

from .models import (
    AssinaturaTermoRecebimentoProvisorio,
    CronogramaTermoRecebimentoProvisorio,
    TermoRecebimentoProvisorio,
)


class CronogramaTermoRecebimentoProvisorioInline(admin.TabularInline):
    """Inline dos cronogramas do termo com a quantidade total recebida
    (edição em linha no formulário do termo)."""

    model = CronogramaTermoRecebimentoProvisorio
    extra = 0
    fields = ("cronograma", "quantidade_total_recebida")


@admin.register(TermoRecebimentoProvisorio)
class TermoRecebimentoProvisorioAdmin(admin.ModelAdmin):
    """Admin do Termo de Recebimento Provisório com inline dos cronogramas."""

    list_display = (
        "uuid",
        "empresa",
        "contrato",
        "valor_contrato",
        "status",
        "criado_em",
        "alterado_em",
    )
    inlines = (CronogramaTermoRecebimentoProvisorioInline,)
    readonly_fields = ("uuid", "criado_em", "alterado_em", "criado_por")
    search_fields = ("empresa__nome_fantasia", "contrato__numero", "uuid")
    list_filter = ("status",)


@admin.register(CronogramaTermoRecebimentoProvisorio)
class CronogramaTermoRecebimentoProvisorioAdmin(admin.ModelAdmin):
    """Admin dos cronogramas vinculados aos termos de recebimento provisório."""

    list_display = (
        "termo",
        "cronograma",
        "quantidade_total_recebida",
    )
    search_fields = ("termo__uuid", "cronograma__numero")


@admin.register(AssinaturaTermoRecebimentoProvisorio)
class AssinaturaTermoRecebimentoProvisorioAdmin(admin.ModelAdmin):
    """Admin das assinaturas dos termos de recebimento provisório."""

    list_display = (
        "termo",
        "usuario",
        "etapa",
        "criado_em",
    )
    list_filter = ("etapa",)
    search_fields = ("termo__uuid", "usuario__nome", "usuario__email")
