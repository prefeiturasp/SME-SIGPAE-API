from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from .models import HistoricoAcessoMedicaoInicialUE


@admin.register(HistoricoAcessoMedicaoInicialUE)
class HistoricoAcessoMedicaoInicialUEAdmin(admin.ModelAdmin):
    list_display = ("escola", "data_inicial", "data_final")
    search_fields = ("escola__nome", "escola__codigo_eol")
    search_help_text = "Pesquise por: nome da escola ou código eol da escola"
    list_filter = (("data_inicial", DateRangeFilter), ("data_final", DateRangeFilter))
