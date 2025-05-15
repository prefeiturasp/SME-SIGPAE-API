from django.contrib import admin

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
)


@admin.register(AlteracaoCardapio)
class AlteracaoCardapioModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "data_inicial", "data_final", "status", "DESCRICAO")
    list_filter = ("status",)
    readonly_fields = ("escola",)


admin.site.register(MotivoAlteracaoCardapio)
