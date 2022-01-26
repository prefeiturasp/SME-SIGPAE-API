from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.core.management import call_command
from django.utils.translation import ugettext_lazy as _
from utility.carga_dados.escola.importa_dados import cria_usuario_cogestor, cria_usuario_diretor
from utility.carga_dados.perfil.importa_dados import (
    importa_usuarios_perfil_codae,
    importa_usuarios_perfil_dre,
    importa_usuarios_perfil_escola,
    valida_arquivo_importacao_usuarios
)

from .models import (
    Cargo,
    ImportacaoPlanilhaUsuarioPerfilCodae,
    ImportacaoPlanilhaUsuarioPerfilDre,
    ImportacaoPlanilhaUsuarioPerfilEscola,
    Perfil,
    PlanilhaDiretorCogestor,
    Usuario,
    Vinculo
)


class BaseUserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {
            'fields': (
                'email', 'tipo_email', 'password', 'cpf',
                'registro_funcional', 'nome', 'cargo', 'crn_numero'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions'
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    add_fieldsets = ((None, {
        'classes': ('wide',),
        'fields': (
            'email', 'password1', 'password2', 'cpf', 'registro_funcional',
            'nome', 'cargo'
        ),
    }),)
    list_display = ('email', 'nome', 'is_staff', 'is_active')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    actions = ('carga_dados',)

    def carga_dados(self, request, queryset):
        return call_command('carga_dados')


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('nome', 'super_usuario', 'ativo')
    search_fields = ('nome',)


@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'perfil', 'content_type')
    search_fields = ('usuario__nome', 'usuario__email', 'usuario__registro_funcional')


@admin.register(PlanilhaDiretorCogestor)
class PlanilhaDiretorCogestorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'criado_em')

    def save_model(self, request, obj, form, change):
        # Lendo arquivo InMemoryUploadedFile
        arquivo = request.FILES.get('arquivo')
        items = cria_usuario_diretor(arquivo, in_memory=True)
        cria_usuario_cogestor(items)
        super(PlanilhaDiretorCogestorAdmin, self).save_model(request, obj, form, change)  # noqa


@admin.register(ImportacaoPlanilhaUsuarioPerfilEscola)
class ImportacaoPlanilhaUsuarioPerfilEscolaAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', '__str__', 'criado_em', 'status')
    readonly_fields = ('resultado', 'status', 'log')
    list_filter = ('status',)
    actions = ('processa_planilha',)
    change_list_template = 'admin/perfil/importacao_usuarios_perfil_escola.html'

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, 'Escolha somente uma planilha.', messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, 'Arquivo não suportado.', messages.ERROR)
            return

        importa_usuarios_perfil_escola(request.user, arquivo)

        self.message_user(request, f'Processo Terminado. Verifique o status do processo: {arquivo.uuid}')

    processa_planilha.short_description = 'Realizar a importação dos usuários perfil Escola'


@admin.register(ImportacaoPlanilhaUsuarioPerfilCodae)
class ImportacaoPlanilhaUsuarioPerfilCodaeAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', '__str__', 'criado_em', 'status')
    readonly_fields = ('resultado', 'status', 'log')
    list_filter = ('status',)
    actions = ('processa_planilha',)
    change_list_template = 'admin/perfil/importacao_usuarios_perfil_codae.html'

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, 'Escolha somente uma planilha.', messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, 'Arquivo não suportado.', messages.ERROR)
            return

        importa_usuarios_perfil_codae(request.user, arquivo)

        self.message_user(request, f'Processo Terminado. Verifique o status do processo: {arquivo.uuid}')

    processa_planilha.short_description = 'Realizar a importação dos usuários perfil Codae'


@admin.register(ImportacaoPlanilhaUsuarioPerfilDre)
class ImportacaoPlanilhaUsuarioPerfilDreAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', '__str__', 'criado_em', 'status')
    readonly_fields = ('resultado', 'status', 'log')
    list_filter = ('status',)
    actions = ('processa_planilha',)
    change_list_template = 'admin/perfil/importacao_usuarios_perfil_dre.html'

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, 'Escolha somente uma planilha.', messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, 'Arquivo não suportado.', messages.ERROR)
            return

        importa_usuarios_perfil_dre(request.user, arquivo)

        self.message_user(request, f'Processo Terminado. Verifique o status do processo: {arquivo.uuid}')

    processa_planilha.short_description = 'Realizar a importação dos usuários perfil Dre'


admin.site.register(Usuario, BaseUserAdmin)
admin.site.register(Cargo)
