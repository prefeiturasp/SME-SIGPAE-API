import logging

import magic
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path

from src.dados_comuns.constants import StringsValidationErrors

from ..api.viewsets import exportar_planilha_importacao_tipo_gestao_escola
from ..models import (
    PlanilhaAtualizacaoTipoGestaoEscola,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
)
from ..tasks import (
    atualiza_codigo_codae_das_escolas_task,
    atualiza_tipo_gestao_das_escolas_task,
)

logger = logging.getLogger("sigpae.escola")


@admin.register(PlanilhaEscolaDeParaCodigoEolCodigoCoade)
class PlanilhaEscolaDeParaCodigoEolCodigoCoadeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "criado_em", "codigos_codae_vinculados")
    actions = ("vincular_codigos_codae_da_planilha",)

    def vincular_codigos_codae_da_planilha(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(
                request,
                StringsValidationErrors.ESCOLHA_UMA_PLANILHA.value,
                messages.ERROR,
            )
            return

        arquivo = queryset.first()
        atualiza_codigo_codae_das_escolas_task.delay(
            path_planilha=arquivo.planilha.path, id_planilha=arquivo.id
        )

        messages.add_message(
            request,
            messages.INFO,
            "Atualização de códigos codae das escolas disparada. Este procedimento pode demorar alguns minutos..",
        )
        return redirect(
            "admin:escola_planilhaescoladeparacodigoeolcodigocoade_changelist"
        )

    vincular_codigos_codae_da_planilha.short_description = (
        "Executar atualização dos códigos codae das escolas"
    )


@admin.register(PlanilhaAtualizacaoTipoGestaoEscola)
class PlanilhaAtualizacaoTipoGestaoEscolaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "criado_em", "status")
    change_list_template = "admin/escola/importacao_tipos_de_gestao_das_escolas.html"
    actions = ("processa_planilha",)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_tipo_gestao_escola/",
                self.admin_site.admin_view(
                    self.exporta_planilha_modelo, cacheable=True
                ),
            ),
        ]
        return my_urls + urls

    def exporta_planilha_modelo(self, request):
        return exportar_planilha_importacao_tipo_gestao_escola(request)

    def valida_arquivo_importacao(self, arquivo):
        logger.debug(
            f"Iniciando validação do arquivo {arquivo.conteudo}: {arquivo.uuid}"
        )

        mime_types_validos = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ]
        extensoes_validas = [".xlsx", ".xls"]
        arquivo_mime_type = magic.from_buffer(arquivo.conteudo.read(2048), mime=True)
        if arquivo_mime_type not in mime_types_validos:
            arquivo.log = "Formato de arquivo não suportado."
            arquivo.erro_no_processamento()
            logger.error(f"Arquivo inválido: {arquivo.uuid}")
            return False
        if not arquivo.conteudo.path.endswith(tuple(extensoes_validas)):
            arquivo.log = "Extensão de arquivo não suportada"
            arquivo.erro_no_processamento()
            logger.error(f"Arquivo inválido: {arquivo.uuid}")
            return False

        logger.info("Arquivo válido.")
        return True

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(
                request,
                StringsValidationErrors.ESCOLHA_UMA_PLANILHA.value,
                messages.ERROR,
            )
            return
        if not self.valida_arquivo_importacao(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        atualiza_tipo_gestao_das_escolas_task.delay(
            path_planilha=arquivo.conteudo.path, id_planilha=arquivo.id
        )

        messages.add_message(
            request,
            messages.INFO,
            "Atualização de Tipo de Gestão das escolas iniciada. Este procedimento pode demorar alguns minutos...",
        )
        return redirect("admin:escola_planilhaatualizacaotipogestaoescola_changelist")

    processa_planilha.short_description = (
        "Executar atualização do tipo de gestão das escolas"
    )
