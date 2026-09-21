from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.dados_comuns.constants import StringsSearchHelpText

from .models import HistoricoAcessoMedicaoInicialUE


@admin.register(HistoricoAcessoMedicaoInicialUE)
class HistoricoAcessoMedicaoInicialUEAdmin(admin.ModelAdmin):
    list_display = ("escola", "lote", "data_inicial", "data_final")
    search_fields = ("escola__nome", "escola__codigo_eol")
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DA_ESCOLA_OU_CODIGO_EOL_DA_ESCOLA.value
    )
    list_filter = (("data_inicial", DateRangeFilter), ("data_final", DateRangeFilter))
