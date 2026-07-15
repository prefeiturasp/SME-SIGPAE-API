from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.escola.models import FaixaEtaria

from .models import (
    LogDietasAtivasCanceladasAutomaticamente,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    LogQuantidadeDietasAutorizadasRecreioNasFerias,
    LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI,
)


@admin.register(LogDietasAtivasCanceladasAutomaticamente)
class LogDietasAtivasCanceladasAutomaticamenteAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "codigo_eol_aluno",
        "codigo_eol_escola_origem",
        "codigo_eol_escola_destino",
        "get_escola_existe",
        "get_criado_em",
    )
    search_fields = (
        "codigo_eol_aluno",
        "nome_aluno",
        "codigo_eol_escola_origem",
        "nome_escola_origem",
        "codigo_eol_escola_destino",
        "nome_escola_destino",
    )

    def get_escola_existe(self, obj):
        if obj.escola_existe:
            return True
        return False

    get_escola_existe.boolean = True
    get_escola_existe.short_description = "escola existe"

    def get_criado_em(self, obj):
        if obj.criado_em:
            return obj.criado_em.strftime("%d/%m/%Y %H:%M:%S")

    get_criado_em.short_description = "Criado em"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(LogQuantidadeDietasAutorizadas)
class LogQuantidadeDietasAutorizadasAdmin(admin.ModelAdmin):
    list_display = (
        "escola",
        "periodo_escolar",
        "cei_ou_emei",
        "infantil_ou_fundamental",
        "classificacao",
        "quantidade",
        "data",
        "criado_em",
    )
    search_fields = ("escola__nome", "escola__codigo_eol")
    list_filter = (
        ("data", DateRangeFilter),
        "classificacao",
        "periodo_escolar",
        "cei_ou_emei",
        "infantil_ou_fundamental",
    )


class FaixaEtariaAtivaFilter(admin.SimpleListFilter):
    title = "faixa etária"
    parameter_name = "faixa_etaria"

    def lookups(self, request, model_admin):
        return [
            (str(faixa.id), str(faixa))
            for faixa in FaixaEtaria.objects.filter(ativo=True)
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(faixa_etaria_id=self.value())
        return queryset


@admin.register(LogQuantidadeDietasAutorizadasCEI)
class LogQuantidadeDietasAutorizadasCEIAdmin(admin.ModelAdmin):
    list_display = (
        "escola",
        "periodo_escolar",
        "faixa_etaria",
        "classificacao",
        "quantidade",
        "data",
        "criado_em",
    )
    search_fields = ("escola__nome", "escola__codigo_eol")
    list_filter = (
        ("data", DateRangeFilter),
        "classificacao",
        "periodo_escolar",
        FaixaEtariaAtivaFilter,
    )


@admin.register(LogQuantidadeDietasAutorizadasRecreioNasFerias)
class LogQuantidadeDietasAutorizadasRecreioNasFeriasAdmin(admin.ModelAdmin):
    list_display = (
        "escola",
        "classificacao",
        "quantidade",
        "data",
        "criado_em",
    )
    search_fields = ("escola__nome", "escola__codigo_eol")
    list_filter = (
        ("data", DateRangeFilter),
        "classificacao",
    )


@admin.register(LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI)
class LogQuantidadeDietasAutorizadasRecreioNasFeriasCEIAdmin(admin.ModelAdmin):
    list_display = (
        "escola",
        "faixa_etaria",
        "classificacao",
        "quantidade",
        "data",
        "criado_em",
    )
    search_fields = ("escola__nome", "escola__codigo_eol")
    list_filter = (
        ("data", DateRangeFilter),
        "classificacao",
        FaixaEtariaAtivaFilter,
    )
