from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from sme_sigpae_api.inclusao_alimentacao.models import (
    DiasMotivosInclusaoDeAlimentacaoCEI,
    DiasMotivosInclusaoDeAlimentacaoCEMEI,
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoAlimentacaoNormal,
    InclusaoDeAlimentacaoCEMEI,
    MotivoInclusaoContinua,
    MotivoInclusaoNormal,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI,
    QuantidadePorPeriodo,
)


class QuantidadePorPeriodoContinuaInline(admin.TabularInline):
    model = QuantidadePorPeriodo
    fk_name = "inclusao_alimentacao_continua"
    extra = 0
    autocomplete_fields = ("periodo_escolar", "tipos_alimentacao")
    fields = (
        "periodo_escolar",
        "numero_alunos",
        "tipos_alimentacao",
        "dias_semana",
        "observacao",
        "cancelado",
        "cancelado_justificativa",
    )
    show_change_link = True


class QuantidadePorPeriodoGrupoInline(admin.TabularInline):
    model = QuantidadePorPeriodo
    fk_name = "grupo_inclusao_normal"
    extra = 0
    autocomplete_fields = ("periodo_escolar", "tipos_alimentacao")
    fields = (
        "periodo_escolar",
        "numero_alunos",
        "tipos_alimentacao",
        "dias_semana",
        "observacao",
        "cancelado",
        "cancelado_justificativa",
    )
    show_change_link = True


class InclusaoAlimentacaoNormalInline(admin.TabularInline):
    model = InclusaoAlimentacaoNormal
    fk_name = "grupo_inclusao"
    extra = 0
    autocomplete_fields = ("motivo",)
    fields = (
        "data",
        "motivo",
        "outro_motivo",
        "evento",
        "cancelado",
        "cancelado_justificativa",
    )
    show_change_link = True


class QuantidadeAlunosFaixaEtariaCEIInline(admin.TabularInline):
    model = QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI
    fk_name = "inclusao_alimentacao_da_cei"
    extra = 0
    show_change_link = True


class DiasMotivosInclusaoCEIInline(admin.TabularInline):
    model = DiasMotivosInclusaoDeAlimentacaoCEI
    fk_name = "inclusao_cei"
    extra = 0
    show_change_link = True


class QuantidadeAlunosFaixaEtariaCEMEIInline(admin.TabularInline):
    model = QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI
    fk_name = "inclusao_alimentacao_cemei"
    extra = 0
    show_change_link = True


class QuantidadeAlunosEMEICEMEIInline(admin.TabularInline):
    model = QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI
    fk_name = "inclusao_alimentacao_cemei"
    extra = 0
    filter_horizontal = ("tipos_alimentacao",)
    show_change_link = True


class DiasMotivosInclusaoCEMEIInline(admin.TabularInline):
    model = DiasMotivosInclusaoDeAlimentacaoCEMEI
    fk_name = "inclusao_alimentacao_cemei"
    extra = 0
    show_change_link = True


class SolicitacaoInclusaoAlimentacaoAdmin(admin.ModelAdmin):
    autocomplete_fields = ("escola",)
    readonly_fields = ("uuid", "criado_em")
    search_fields = ("=uuid", "escola__nome", "escola__codigo_eol")
    search_help_text = "Pesquisa por: uuid, nome da escola, código eol da escola"
    list_select_related = ("escola", "escola__lote", "escola__diretoria_regional")

    @admin.display(description="Lote", ordering="escola__lote__nome")
    def get_lote(self, obj):
        return obj.escola.lote

    @admin.display(description="DRE", ordering="escola__diretoria_regional__nome")
    def get_dre(self, obj):
        return obj.escola.diretoria_regional


@admin.register(MotivoInclusaoContinua)
class MotivoInclusaoContinuaAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    readonly_fields = ("uuid",)


@admin.register(MotivoInclusaoNormal)
class MotivoInclusaoNormalAdmin(admin.ModelAdmin):
    search_fields = ("nome",)
    readonly_fields = ("uuid",)


@admin.register(InclusaoAlimentacaoContinua)
class InclusaoAlimentacaoContinuaAdmin(SolicitacaoInclusaoAlimentacaoAdmin):
    inlines = (QuantidadePorPeriodoContinuaInline,)
    list_display = (
        "uuid",
        "escola",
        "get_lote",
        "get_dre",
        "data_inicial",
        "data_final",
        "status",
    )
    list_filter = (
        ("escola__lote", admin.RelatedOnlyFieldListFilter),
        ("escola__diretoria_regional", admin.RelatedOnlyFieldListFilter),
        "status",
        ("data_inicial", DateRangeFilter),
        ("data_final", DateRangeFilter),
    )

    def get_fields(self, request, obj=None):
        if obj:
            return (
                "uuid",
                "status",
                "escola",
                "motivo",
                "outro_motivo",
                "descricao",
                "criado_por",
                "criado_em",
                "foi_solicitado_fora_do_prazo",
                "terceirizada_conferiu_gestao",
                "data_inicial",
                "data_final",
            )
        return (
            "escola",
            "motivo",
            "outro_motivo",
            "descricao",
            "data_inicial",
            "data_final",
            "criado_por",
        )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.extend(
                [
                    "escola",
                    "motivo",
                    "outro_motivo",
                    "descricao",
                    "criado_por",
                    "foi_solicitado_fora_do_prazo",
                    "terceirizada_conferiu_gestao",
                ]
            )
        return tuple(readonly_fields)


@admin.register(GrupoInclusaoAlimentacaoNormal)
class GrupoInclusaoAlimentacaoNormalAdmin(SolicitacaoInclusaoAlimentacaoAdmin):
    inlines = (InclusaoAlimentacaoNormalInline, QuantidadePorPeriodoGrupoInline)
    list_display = (
        "uuid",
        "escola",
        "get_lote",
        "get_dre",
        "datas",
        "status",
    )
    list_filter = (
        ("escola__lote", admin.RelatedOnlyFieldListFilter),
        ("escola__diretoria_regional", admin.RelatedOnlyFieldListFilter),
        "status",
        ("inclusoes_normais__data", DateRangeFilter),
    )

    def get_fields(self, request, obj=None):
        if obj:
            return (
                "uuid",
                "status",
                "escola",
                "descricao",
                "criado_por",
                "criado_em",
                "foi_solicitado_fora_do_prazo",
                "terceirizada_conferiu_gestao",
            )
        return ("escola", "descricao", "criado_por")

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.extend(
                [
                    "escola",
                    "descricao",
                    "criado_por",
                    "foi_solicitado_fora_do_prazo",
                    "terceirizada_conferiu_gestao",
                ]
            )
        return tuple(readonly_fields)


@admin.register(InclusaoAlimentacaoDaCEI)
class InclusaoAlimentacaoDaCEIAdmin(SolicitacaoInclusaoAlimentacaoAdmin):
    inlines = (DiasMotivosInclusaoCEIInline, QuantidadeAlunosFaixaEtariaCEIInline)
    filter_horizontal = ("tipos_alimentacao",)
    list_display = (
        "uuid",
        "escola",
        "get_lote",
        "get_dre",
        "datas",
        "status",
    )
    list_filter = (
        ("escola__lote", admin.RelatedOnlyFieldListFilter),
        ("escola__diretoria_regional", admin.RelatedOnlyFieldListFilter),
        "status",
        ("dias_motivos_da_inclusao_cei__data", DateRangeFilter),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly_fields.extend(
                [
                    "escola",
                    "criado_por",
                    "foi_solicitado_fora_do_prazo",
                    "terceirizada_conferiu_gestao",
                ]
            )
        return tuple(readonly_fields)


@admin.register(InclusaoDeAlimentacaoCEMEI)
class InclusaoDeAlimentacaoCEMEIAdmin(SolicitacaoInclusaoAlimentacaoAdmin):
    inlines = (
        DiasMotivosInclusaoCEMEIInline,
        QuantidadeAlunosFaixaEtariaCEMEIInline,
        QuantidadeAlunosEMEICEMEIInline,
    )
    list_display = (
        "uuid",
        "escola",
        "get_lote",
        "get_dre",
        "datas",
        "status",
    )
    list_filter = (
        ("escola__lote", admin.RelatedOnlyFieldListFilter),
        ("escola__diretoria_regional", admin.RelatedOnlyFieldListFilter),
        "status",
        ("dias_motivos_da_inclusao_cemei__data", DateRangeFilter),
    )


admin.site.register(QuantidadePorPeriodo)
admin.site.register(InclusaoAlimentacaoNormal)
admin.site.register(QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI)
