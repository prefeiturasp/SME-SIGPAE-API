from django.contrib import admin

from .models import (
    Cronograma,
    EtapasDoCronograma,
    ProgramacaoDoRecebimentoDoCronograma,
    SolicitacaoAlteracaoCronograma,
)


class EtapasAntigasInline(admin.StackedInline):
    model = SolicitacaoAlteracaoCronograma.etapas_antigas.through
    extra = 0  # Quantidade de linhas que serão exibidas.


class EtapasNovasInline(admin.StackedInline):
    model = SolicitacaoAlteracaoCronograma.etapas_novas.through
    extra = 0  # Quantidade de linhas que serão exibidas.


@admin.register(SolicitacaoAlteracaoCronograma)
class SolicitacaoAdmin(admin.ModelAdmin):
    inlines = [EtapasAntigasInline, EtapasNovasInline]


class EtapasInline(admin.TabularInline):
    model = EtapasDoCronograma
    extra = 0


class CronogramaAdmin(admin.ModelAdmin):
    inlines = (EtapasInline,)


admin.site.register(EtapasDoCronograma)
admin.site.register(ProgramacaoDoRecebimentoDoCronograma)
admin.site.register(Cronograma, CronogramaAdmin)
