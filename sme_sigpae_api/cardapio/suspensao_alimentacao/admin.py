from django.contrib import admin

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)


class SuspensaoAlimentacaoInline(admin.TabularInline):
    model = SuspensaoAlimentacao
    extra = 1


class QuantidadePorPeriodoSuspensaoAlimentacaoInline(admin.TabularInline):
    model = QuantidadePorPeriodoSuspensaoAlimentacao
    extra = 1


@admin.register(GrupoSuspensaoAlimentacao)
class GrupoSuspensaoAlimentacaoModelAdmin(admin.ModelAdmin):
    inlines = [
        SuspensaoAlimentacaoInline,
        QuantidadePorPeriodoSuspensaoAlimentacaoInline,
    ]


admin.site.register(MotivoSuspensao)
