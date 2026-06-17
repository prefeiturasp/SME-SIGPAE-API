from datetime import date

from django.contrib import admin, messages
from django.http import HttpResponse

from src.dieta_especial.tasks.admin_actions import get_escolas_task
from src.escola.utils_analise_dietas_ativas import main
from src.escola.utils_escola import create_tempfile, escreve_escolas_json
from src.processamento_arquivos.dieta_especial import (
    importa_alimentos,
    importa_dietas_especiais,
)

from .models import (
    ArquivoCargaAlimentosSubstitutos,
    ArquivoCargaDietaEspecial,
    PlanilhaDietasAtivas,
)


@admin.register(PlanilhaDietasAtivas)
class PlanilhaDietasAtivasAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tempfile", "criado_em")
    actions = ("analisar_planilha_dietas_ativas", "gerar_json_do_eol")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.tempfile = create_tempfile()
            escreve_escolas_json(obj.tempfile, "{\n")
            obj.save
        super(PlanilhaDietasAtivasAdmin, self).save_model(request, obj, form, change)

    def analisar_planilha_dietas_ativas(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return

        count = 1
        msg = "{} planilha foi marcada para ser analisada."
        self.message_user(request, msg.format(count))

        tempfile = queryset[0].tempfile

        arquivo = queryset[0].arquivo
        arquivo_unidades_da_rede = queryset[0].arquivo_unidades_da_rede
        resultado, arquivo_final = main(
            arquivo=arquivo,
            arquivo_codigos_escolas=arquivo_unidades_da_rede,
            tempfile=tempfile,
        )

        with open(arquivo_final, "rb") as f:
            resultado = f.read()

        DATA = date.today().isoformat().replace("-", "_")
        nome_arquivo = f"resultado_analise_dietas_ativas_{DATA}_01.xlsx"
        response = HttpResponse(resultado, content_type="application/ms-excel")
        response["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
        return response

    analisar_planilha_dietas_ativas.short_description = (
        "Analisar planilha dietas ativas"
    )

    def gerar_json_do_eol(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return

        count = 1
        msg = "{} planilha foi marcada para ser analisada."
        self.message_user(request, msg.format(count))
        get_escolas_task.delay()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ArquivoCargaDietaEspecial)
class ArquivoCargaDietaEspecialAdmin(admin.ModelAdmin):
    list_display = ("uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_carga",)

    def processa_carga(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return

        importa_dietas_especiais(usuario=request.user, arquivo=queryset.first())
        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo. {queryset.first().uuid}",
        )

    processa_carga.short_description = (
        "Realiza a importação das solicitações de dietas especiais"
    )


@admin.register(ArquivoCargaAlimentosSubstitutos)
class ArquivoCargaAlimentosSubstitutosAdmin(admin.ModelAdmin):
    list_display = ("uuid", "__str__", "criado_em", "status")
    readonly_fields = ("status", "log")
    list_filter = ("status",)
    actions = ("processa_carga",)

    def processa_carga(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return

        importa_alimentos(arquivo=queryset.first())
        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo. {queryset.first().uuid}",
        )

    processa_carga.short_description = (
        "Realiza a importação dos alimentos e alimentos substitutos"
    )
