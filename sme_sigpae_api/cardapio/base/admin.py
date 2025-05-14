from django.contrib import admin

from sme_sigpae_api.cardapio.base.models import (
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)


@admin.register(SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE)
class SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUEModelAdmin(
    admin.ModelAdmin
):
    list_display = ("__str__",)


class SubstituicaoComboInline(admin.TabularInline):
    model = SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE
    extra = 2


@admin.register(ComboDoVinculoTipoAlimentacaoPeriodoTipoUE)
class ComboDoVinculoTipoAlimentacaoPeriodoTipoUEModelAdmin(admin.ModelAdmin):
    inlines = [SubstituicaoComboInline]
    search_fields = ("vinculo__tipo_unidade_escolar__iniciais",)
    filter_horizontal = ("tipos_alimentacao",)
    readonly_fields = ("vinculo",)


class ComboVinculoLine(admin.TabularInline):
    model = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE
    extra = 1


@admin.register(VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar)
class VinculoTipoAlimentacaoModelAdmin(admin.ModelAdmin):
    list_filter = ("periodo_escolar__nome", "tipo_unidade_escolar__iniciais", "ativo")
    inlines = [ComboVinculoLine]


@admin.register(Cardapio)
class CardapioAdmin(admin.ModelAdmin):
    list_display = ["data", "criado_em", "ativo"]
    ordering = ["data", "criado_em"]


admin.site.register(MotivoDRENaoValida)
admin.site.register(HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar)
admin.site.register(TipoAlimentacao)
