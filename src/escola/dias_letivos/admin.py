from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from rangefilter.filters import DateRangeFilter

from .models import DiaLetivoSIGPAE

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
    """Filtro do admin Django para filtrar dias letivos por dia da semana.

    Utiliza o campo data__week_day do banco de dados para realizar
    a filtragem de acordo com o dia selecionado.
    """

    title = "Dia da semana"
    parameter_name = "dia_semana"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[int, str]]:
        """Retorna as opções de dias da semana disponíveis para o filtro."""
        return DIAS_SEMANA

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        """Aplica o filtro de dia da semana ao queryset.

        Se nenhum valor for selecionado, retorna o queryset sem filtro.
        """
        if self.value():
            return queryset.filter(data__week_day=self.value())
        return queryset


class DiaLetivoSIGPAEAdmin(admin.ModelAdmin):
    """Configuração do admin Django para o modelo DiaLetivoSIGPAE.

    Exibe campos customizados para dia da semana, períodos, lotes,
    tipos de unidade e escolas. Inclui filtro por range de data
    e por dia da semana.
    """

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
    filter_horizontal = (
        "periodos_escolares",
        "lotes",
        "tipos_unidade_escolar",
        "escolas",
    )
    ordering = ("-data",)
    readonly_fields = ("uuid", "criado_em", "criado_por", "alterado_em")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Retorna o queryset com prefetch_related para evitar N+1 queries.

        Pré-carrega periodos_escolares, lotes, tipos_unidade_escolar e escolas.
        """
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
    def get_dia_semana(self, obj: DiaLetivoSIGPAE) -> str:
        """Retorna o nome do dia da semana formatado para exibição no admin."""
        return dict(DIAS_SEMANA).get(obj.data.isoweekday() % 7 + 1, "-")

    @admin.display(description="Períodos escolares")
    def get_periodos_escolares(self, obj: DiaLetivoSIGPAE) -> str:
        """Retorna os nomes (até 3) ou o total de períodos vinculados."""
        count = obj.periodos_escolares.count()
        if count == 0:
            return "Nenhum"
        if 1 <= count <= 3:
            nomes = obj.periodos_escolares.values_list("nome", flat=True)
            return ", ".join(nomes)
        return f"{count} períodos"

    @admin.display(description="Lotes")
    def get_lotes(self, obj: DiaLetivoSIGPAE) -> str:
        """Retorna os nomes (até 3) ou o total de lotes vinculados."""
        count = obj.lotes.count()
        if count == 0:
            return "Nenhum"
        if 1 <= count <= 3:
            nomes = obj.lotes.values_list("nome", flat=True)
            return ", ".join(nomes)
        return f"{count} lotes"

    @admin.display(description="Tipos de unidade")
    def get_tipos_unidade(self, obj: DiaLetivoSIGPAE) -> str:
        """Retorna as iniciais (até 3) ou o total de tipos vinculados."""
        count = obj.tipos_unidade_escolar.count()
        if count == 0:
            return "Nenhum"
        if 1 <= count <= 3:
            iniciais = obj.tipos_unidade_escolar.values_list("iniciais", flat=True)
            return ", ".join(iniciais)
        return f"{count} tipos"

    @admin.display(description="Escolas")
    def get_escolas(self, obj: DiaLetivoSIGPAE) -> str:
        """Retorna os nomes (até 3) ou o total de escolas vinculadas."""
        count = obj.escolas.count()
        if count == 0:
            return "Nenhuma"
        if 1 <= count <= 3:
            nomes = obj.escolas.values_list("nome", flat=True)
            return ", ".join(nomes)
        return f"{count} escolas"
