from django.contrib import admin
from nested_inline.admin import NestedModelAdmin, NestedTabularInline
from rangefilter.filters import DateRangeFilter

from sme_sigpae_api.medicao_inicial.recreio_nas_ferias.models import (
    CategoriaAlimentacao,
    RecreioNasFerias,
    RecreioNasFeriasUnidadeParticipante,
    RecreioNasFeriasUnidadeTipoAlimentacao,
)


class UnidadeTipoAlimentacaoInline(NestedTabularInline):
    model = RecreioNasFeriasUnidadeTipoAlimentacao
    extra = 0


class RecreioNasFeriasUnidadeParticipanteInline(NestedTabularInline):
    model = RecreioNasFeriasUnidadeParticipante
    readonly_fields = ("unidade_educacional", "lote")
    fields = (
        "lote",
        "unidade_educacional",
        "num_inscritos",
        "num_colaboradores",
        "liberar_medicao",
        "cei_ou_emei",
    )
    inlines = (UnidadeTipoAlimentacaoInline,)
    extra = 0


@admin.register(RecreioNasFerias)
class RecreioNasFeriasAdmin(NestedModelAdmin):
    inlines = (RecreioNasFeriasUnidadeParticipanteInline,)
    list_filter = (
        ("data_inicio", DateRangeFilter),
        ("data_fim", DateRangeFilter),
    )
    search_fields = (
        "unidades_participantes__unidade_educacional__nome",
        "unidades_participantes__unidade_educacional__codigo_eol",
    )
    search_help_text = "Pesquisa por: nome da escola, código eol da escola"


@admin.register(RecreioNasFeriasUnidadeParticipante)
class RecreioNasFeriasUnidadeParticipanteAdmin(admin.ModelAdmin):
    list_filter = ("recreio_nas_ferias__titulo",)
    search_fields = ("recreio_nas_ferias__titulo",)
    search_help_text = "Pesquisa por: título do recreio nas férias"


admin.site.register(CategoriaAlimentacao)
