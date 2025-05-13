from django.contrib import admin

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
)
from sme_sigpae_api.cardapio.base.models import (
    Cardapio,
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar,
    MotivoDRENaoValida,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)

admin.site.register(TipoAlimentacao)
admin.site.register(InversaoCardapio)
admin.site.register(MotivoAlteracaoCardapio)
admin.site.register(SuspensaoAlimentacaoDaCEI)
admin.site.register(MotivoSuspensao)
admin.site.register(MotivoDRENaoValida)
admin.site.register(HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar)


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


@admin.register(AlteracaoCardapio)
class AlteracaoCardapioModelAdmin(admin.ModelAdmin):
    list_display = ("uuid", "data_inicial", "data_final", "status", "DESCRICAO")
    list_filter = ("status",)
    readonly_fields = ("escola",)


class SubstituicoesCEIInLine(admin.TabularInline):
    model = SubstituicaoAlimentacaoNoPeriodoEscolarCEI
    extra = 1


@admin.register(AlteracaoCardapioCEI)
class AlteracaoCardapioCEIModelAdmin(admin.ModelAdmin):
    inlines = [SubstituicoesCEIInLine]
    list_display = ["uuid", "data", "status"]
    list_filter = ["status"]


@admin.register(AlteracaoCardapioCEMEI)
class AlteracaoCardapioCEMEIModelAdmin(admin.ModelAdmin):
    list_display = ["uuid", "data", "status"]
    list_filter = ["status"]


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
