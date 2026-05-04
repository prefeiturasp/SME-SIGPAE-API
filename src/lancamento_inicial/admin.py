from django.contrib import admin

from .models import LancamentoDiario, Refeicao

admin.site.register(Refeicao)


@admin.register(LancamentoDiario)
class LancamentoDiarioAdmin(admin.ModelAdmin):
    list_display = ("__str__",)
    readonly_fields = ["escola_periodo_escolar", "criado_por"]
