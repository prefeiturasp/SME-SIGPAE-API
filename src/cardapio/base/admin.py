from django.contrib import admin

from src.cardapio.base.models import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)


@admin.register(VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar)
class VinculoTipoAlimentacaoModelAdmin(admin.ModelAdmin):
    list_filter = ("periodo_escolar__nome", "tipo_unidade_escolar__iniciais", "ativo")


@admin.register(TipoAlimentacao)
class TipoAlimentacaoAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    readonly_fields = ("uuid",)


admin.site.register(MotivoDRENaoValida)
admin.site.register(HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar)
