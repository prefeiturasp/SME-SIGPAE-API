from django.contrib import admin

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
)


@admin.register(AlteracaoCardapioCEMEI)
class AlteracaoCardapioCEMEIModelAdmin(admin.ModelAdmin):
    list_display = ["uuid", "data", "status"]
    list_filter = ["status"]
