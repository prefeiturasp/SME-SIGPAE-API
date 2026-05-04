from django.contrib import admin

from .models import (
    EscolaQuantidade,
    FaixaEtariaSolicitacaoKitLancheCEIAvulsa,
    ItemKitLanche,
    KitLanche,
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheUnificada,
)

admin.site.register(KitLanche)
admin.site.register(ItemKitLanche)
admin.site.register(SolicitacaoKitLancheUnificada)
admin.site.register(EscolaQuantidade)
admin.site.register(FaixaEtariaSolicitacaoKitLancheCEIAvulsa)


@admin.register(SolicitacaoKitLancheAvulsa)
class SolicitacaoKitLancheAvulsaAdmin(admin.ModelAdmin):
    list_display = ["escola", "status", "solicitacao_kit_lanche"]
    ordering = ["escola", "status"]


@admin.register(SolicitacaoKitLanche)
class SolicitacaoKitLancheAdmin(admin.ModelAdmin):
    list_display = ["criado_em", "data"]


@admin.register(SolicitacaoKitLancheCEIAvulsa)
class SolicitacaoKitLancheCEIAvulsaAdmin(admin.ModelAdmin):
    list_display = ["escola", "status", "solicitacao_kit_lanche"]
    ordering = ["escola", "status"]
