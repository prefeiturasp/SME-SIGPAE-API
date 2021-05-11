from datetime import date

from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path

from sme_terceirizadas.dados_comuns.constants import COORDENADOR_LOGISTICA
from sme_terceirizadas.escola.models import Codae
from sme_terceirizadas.escola.utils_analise_dietas_ativas import main
from sme_terceirizadas.escola.utils_escola import create_tempfile, escreve_escolas_json

from .forms import AlimentoProprioForm
from .models import (
    AlergiaIntolerancia,
    Alimento,
    AlimentoProprio,
    Anexo,
    ClassificacaoDieta,
    LogDietasAtivasCanceladasAutomaticamente,
    MotivoAlteracaoUE,
    MotivoNegacao,
    PlanilhaDietasAtivas,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
    SubstituicaoAlimentoProtocoloPadrao,
    TipoContagem
)
from .tasks import get_escolas_task, processa_dietas_especiais_task


@admin.register(AlergiaIntolerancia)
class AlergiaIntoleranciaAdmin(admin.ModelAdmin):
    list_display = ('descricao',)
    search_fields = ('descricao',)
    ordering = ('descricao',)


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(AlimentoProprio)
class AlimentoProprioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'marca', 'outras_informacoes', 'ativo')
    search_fields = ('nome', 'marca__nome', 'outras_informacoes')
    list_filter = ('ativo',)
    ordering = ('nome',)
    readonly_fields = ('tipo',)
    form = AlimentoProprioForm
    actions = ('inativar_alimentos',)

    def inativar_alimentos(self, request, queryset):
        count = queryset.update(ativo=False)

        if count == 1:
            msg = '{} alimento próprio foi inativado.'  # noqa P103
        else:
            msg = '{} alimentos próprios foram inativados.'  # noqa P103

        self.message_user(request, msg.format(count))

    inativar_alimentos.short_description = 'Marcar para inativar alimentos'

    def has_module_permission(self, request, obj=None):
        usuario = request.user
        if usuario:
            if not usuario.is_anonymous:
                return (
                    not usuario.is_anonymous and
                    usuario.vinculo_atual and
                    isinstance(usuario.vinculo_atual.instituicao, Codae) and
                    usuario.vinculo_atual.perfil.nome in [COORDENADOR_LOGISTICA] or
                    usuario.email == 'admin@admin.com'
                )
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SubstituicaoAlimentoInline(admin.TabularInline):
    model = SubstituicaoAlimento
    extra = 0


@admin.register(SolicitacaoDietaEspecial)
class SolicitacaoDietaEspecialAdmin(admin.ModelAdmin):
    list_display = ('id_externo', '__str__', 'status', 'tipo_solicitacao', 'ativo')
    list_display_links = ('__str__',)
    search_fields = ('uuid', 'aluno__codigo_eol')
    readonly_fields = ('aluno',)
    change_list_template = 'dieta_especial/change_list.html'
    inlines = (SubstituicaoAlimentoInline,)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('inativa_dietas/', self.admin_site.admin_view(self.inativa_dietas, cacheable=True)),
        ]
        return my_urls + urls

    def inativa_dietas(self, request):
        processa_dietas_especiais_task.delay()
        messages.add_message(
            request,
            messages.INFO,
            'Inativação de dietas disparada com sucesso. Dentro de instantes as dietas serão atualizadas.'
        )
        return redirect('admin:dieta_especial_solicitacaodietaespecial_changelist')


@admin.register(PlanilhaDietasAtivas)
class PlanilhaDietasAtivasAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tempfile', 'criado_em')
    actions = ('analisar_planilha_dietas_ativas', 'gerar_json_do_eol')

    def save_model(self, request, obj, form, change):
        if not change:
            # Gera JSON temporario
            obj.tempfile = create_tempfile()
            escreve_escolas_json(obj.tempfile, '{\n')
            obj.save
        super(PlanilhaDietasAtivasAdmin, self).save_model(request, obj, form, change)

    def analisar_planilha_dietas_ativas(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(request, 'Escolha somente uma planilha.', messages.ERROR)
            return

        count = 1
        msg = '{} planilha foi marcada para ser analisada.'  # noqa P103
        self.message_user(request, msg.format(count))

        tempfile = queryset[0].tempfile

        arquivo = queryset[0].arquivo
        arquivo_unidades_da_rede = queryset[0].arquivo_unidades_da_rede
        resultado, arquivo_final = main(
            arquivo=arquivo,
            arquivo_codigos_escolas=arquivo_unidades_da_rede,
            tempfile=tempfile
        )

        with open(arquivo_final, 'rb') as f:
            resultado = f.read()

        # Testando o download do arquivo
        DATA = date.today().isoformat().replace('-', '_')
        nome_arquivo = f'resultado_analise_dietas_ativas_{DATA}_01.xlsx'
        response = HttpResponse(resultado, content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
        return response

    analisar_planilha_dietas_ativas.short_description = 'Analisar planilha dietas ativas'

    def gerar_json_do_eol(self, request, queryset):
        # Lê a API do EOL e gera um arquivo JSON.
        if len(queryset) > 1:
            self.message_user(request, 'Escolha somente uma planilha.', messages.ERROR)
            return

        count = 1
        msg = '{} planilha foi marcada para ser analisada.'  # noqa P103
        self.message_user(request, msg.format(count))
        get_escolas_task.delay()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LogDietasAtivasCanceladasAutomaticamente)
class LogDietasAtivasCanceladasAutomaticamenteAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'codigo_eol_aluno',
        'codigo_eol_escola_origem',
        'codigo_eol_escola_destino',
        'get_escola_existe',
        'get_criado_em'
    )
    search_fields = (
        'codigo_eol_aluno',
        'nome_aluno',
        'codigo_eol_escola_origem',
        'nome_escola_origem',
        'codigo_eol_escola_destino',
        'nome_escola_destino',
    )

    def get_escola_existe(self, obj):
        if obj.escola_existe:
            return True
        return False

    get_escola_existe.boolean = True
    get_escola_existe.short_description = 'escola existe'

    def get_criado_em(self, obj):
        if obj.criado_em:
            return obj.criado_em.strftime('%d/%m/%Y %H:%M:%S')

    get_criado_em.short_description = 'Criado em'

    def has_add_permission(self, request, obj=None):
        return False


class SubstituicaoAlimentoProtocoloPadraoInline(admin.TabularInline):
    model = SubstituicaoAlimentoProtocoloPadrao
    extra = 0


@admin.register(ProtocoloPadraoDietaEspecial)
class ProtocoloPadraoDietaEspecialAdmin(admin.ModelAdmin):
    list_display = ('nome_protocolo', 'status')
    search_fields = ('nome_protocolo',)
    inlines = (SubstituicaoAlimentoProtocoloPadraoInline,)


admin.site.register(Anexo)
admin.site.register(ClassificacaoDieta)
admin.site.register(MotivoAlteracaoUE)
admin.site.register(MotivoNegacao)
admin.site.register(SubstituicaoAlimento)
admin.site.register(SubstituicaoAlimentoProtocoloPadrao)
admin.site.register(TipoContagem)
