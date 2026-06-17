from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)


@admin.register(SuspensaoAlimentacaoDaCEI)
class SuspensaoAlimentacaoDaCEIModelAdmin(admin.ModelAdmin):
    """Admin do Django para solicitações de suspensão de alimentação de CEI.

    Configura a listagem administrativa de
    :class:`SuspensaoAlimentacaoDaCEI`, exibindo informações da escola,
    data, status, motivo e períodos escolares. Habilita busca textual por
    nome e código EOL da escola, filtros por lote, DRE, intervalo de data
    e motivo.
    """

    list_display = (
        "escola__codigo_eol",
        "escola__nome",
        "data",
        "status",
        "motivo__nome",
        "get_periodos_escolares",
    )
    search_fields = ("uuid", "escola__nome", "escola__codigo_eol")
    search_help_text = "Pesquisar por: UUID, nome da escola, código EOL da escola"
    list_filter = (
        ("data", DateRangeFilter),
        "escola__lote",
        "status",
    )
    list_select_related = ("escola",)
    readonly_fields = ("escola",)

    @admin.display(description="Períodos escolares")
    def get_periodos_escolares(self, obj):
        """Retorna os períodos escolares vinculados à suspensão.

        Args:
            obj (SuspensaoAlimentacaoDaCEI): Solicitação exibida na linha
                atual.

        Returns:
            str: Nomes dos períodos escolares separados por vírgula, ou
                ``"-"`` quando nenhum.
        """
        periodos = obj.periodos_escolares.all()
        if not periodos:
            return "-"
        return ", ".join(p.nome for p in periodos)
