from django.contrib import admin

from .models import (
    Cronograma,
    EtapasDoCronograma,
    InterrupcaoProgramadaEntrega,
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
    """Admin para Solicitação de Alteração de Cronograma com inlines de etapas."""

    inlines = [EtapasAntigasInline, EtapasNovasInline]


class EtapasInline(admin.TabularInline):
    """Inline para exibir etapas do cronograma no formulário admin."""

    model = EtapasDoCronograma
    extra = 0


class CronogramaAdmin(admin.ModelAdmin):
    """Admin para Cronograma com inline de etapas."""

    inlines = (EtapasInline,)


admin.site.register(EtapasDoCronograma)
admin.site.register(InterrupcaoProgramadaEntrega)
admin.site.register(ProgramacaoDoRecebimentoDoCronograma)
admin.site.register(Cronograma, CronogramaAdmin)
