import re

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path

from src.dieta_especial.tasks import processa_dietas_especiais_task
from src.dieta_especial.utils import is_alpha_numeric_and_has_single_space

from ..protocolo_padrao.admin import SubstituicaoAlimentoInline
from .models import (
    AlergiaIntolerancia,
    Anexo,
    ClassificacaoDieta,
    MotivoAlteracaoUE,
    MotivoNegacao,
    SolicitacaoDietaEspecial,
)


@admin.register(AlergiaIntolerancia)
class AlergiaIntoleranciaAdmin(admin.ModelAdmin):
    list_display = ("descricao",)
    search_fields = ("descricao",)
    ordering = ("descricao",)

    def message_user(self, *args):
        pass

    def save_model(self, request, obj, form, change):
        if obj.descricao in ["", None]:
            messages.error(request, "É necessário preencher o campo descrição!")
            return
        obj.descricao = obj.descricao.strip().upper()
        obj.descricao = re.sub(r"\s+", " ", obj.descricao)
        acao = "cadastrado"
        if change:
            acao = "alterado"
        if AlergiaIntolerancia.objects.filter(descricao=obj.descricao):
            messages.error(request, "Diagnóstico já cadastrado!")
            return
        if not is_alpha_numeric_and_has_single_space(obj.descricao):
            messages.error(
                request,
                f'Diagnóstico "{obj.descricao}" inválido. Permitido apenas letras e números!',
            )
            return
        messages.success(request, f"Diagnóstico {acao} com sucesso!")
        super(AlergiaIntoleranciaAdmin, self).save_model(request, obj, form, change)


@admin.register(SolicitacaoDietaEspecial)
class SolicitacaoDietaEspecialAdmin(admin.ModelAdmin):
    list_display = ("id_externo", "__str__", "status", "tipo_solicitacao", "ativo")
    list_display_links = ("__str__",)
    search_fields = ("uuid", "aluno__codigo_eol", "aluno__nome")
    readonly_fields = ("aluno",)
    list_filter = ("eh_importado", "conferido")
    filter_horizontal = ("alergias_intolerancias",)
    change_list_template = "dieta_especial/change_list.html"
    inlines = (SubstituicaoAlimentoInline,)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "inativa_dietas/",
                self.admin_site.admin_view(self.inativa_dietas, cacheable=True),
            ),
        ]
        return my_urls + urls

    def inativa_dietas(self, request):
        processa_dietas_especiais_task.delay()
        messages.add_message(
            request,
            messages.INFO,
            "Inativação de dietas disparada com sucesso. Dentro de instantes as dietas serão atualizadas.",
        )
        return redirect("admin:dieta_especial_solicitacaodietaespecial_changelist")


admin.site.register(Anexo)
admin.site.register(ClassificacaoDieta)
admin.site.register(MotivoAlteracaoUE)
admin.site.register(MotivoNegacao)
