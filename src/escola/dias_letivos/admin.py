from django.contrib import admin
from rangefilter.filters import DateRangeFilter

DIAS_SEMANA = [
    (2, "Segunda"),
    (3, "Terça"),
    (4, "Quarta"),
    (5, "Quinta"),
    (6, "Sexta"),
    (7, "Sábado"),
    (1, "Domingo"),
]


class DiaSemanaFilter(admin.SimpleListFilter):
    title = "Dia da semana"
    parameter_name = "dia_semana"

    def lookups(self, request, model_admin):
        return DIAS_SEMANA

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(data__week_day=self.value())
        return queryset


class DiaLetivoSIGPAEAdmin(admin.ModelAdmin):
    list_display = (
        "data",
        "get_dia_semana",
        "get_periodos_escolares",
        "get_lotes",
        "get_tipos_unidade",
        "get_escolas",
    )
    search_fields = ("escolas__nome", "escolas__codigo_eol")
    search_help_text = "Pesquise por: nome da escola ou código eol da escola"
    list_filter = (
        ("data", DateRangeFilter),
        "periodos_escolares",
        "lotes",
        DiaSemanaFilter,
    )
    ordering = ("-data",)
    readonly_fields = ("uuid", "criado_em", "criado_por", "alterado_em")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "periodos_escolares",
                "lotes",
                "tipos_unidade_escolar",
                "escolas",
            )
        )

    @admin.display(description="Dia da semana")
    def get_dia_semana(self, obj):
        return dict(DIAS_SEMANA).get(obj.data.isoweekday() % 7 + 1, "-")

    @admin.display(description="Períodos escolares")
    def get_periodos_escolares(self, obj):
        return ", ".join(p.nome for p in obj.periodos_escolares.all())

    @admin.display(description="Lotes")
    def get_lotes(self, obj):
        return ", ".join(lote.nome for lote in obj.lotes.all())

    @admin.display(description="Tipos de unidade")
    def get_tipos_unidade(self, obj):
        return ", ".join(t.iniciais for t in obj.tipos_unidade_escolar.all())

    @admin.display(description="Escolas")
    def get_escolas(self, obj):
        return ", ".join(e.nome for e in obj.escolas.all())
