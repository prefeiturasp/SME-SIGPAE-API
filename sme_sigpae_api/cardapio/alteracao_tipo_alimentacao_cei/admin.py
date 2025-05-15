from django.contrib import admin

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
)


class SubstituicoesCEIInLine(admin.TabularInline):
    model = SubstituicaoAlimentacaoNoPeriodoEscolarCEI
    extra = 1


@admin.register(AlteracaoCardapioCEI)
class AlteracaoCardapioCEIModelAdmin(admin.ModelAdmin):
    inlines = [SubstituicoesCEIInLine]
    list_display = ["uuid", "data", "status"]
    list_filter = ["status"]
