from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.urls import path
from django.utils.translation import gettext_lazy as _

from utility.carga_dados.escola.importa_dados import (
    cria_usuario_cogestor,
    cria_usuario_diretor,
)
from utility.carga_dados.perfil.importa_dados import (
    importa_usuarios_externos_coresso,
    importa_usuarios_perfil_codae,
    importa_usuarios_perfil_dre,
    importa_usuarios_perfil_escola,
    importa_usuarios_servidores_coresso,
    importa_usuarios_ues_parceiras_coresso,
    valida_arquivo_importacao_usuarios,
)

from ..escola.models import Escola
from .api.viewsets import (
    exportar_planilha_importacao_usuarios_externos_coresso,
    exportar_planilha_importacao_usuarios_perfil_codae,
    exportar_planilha_importacao_usuarios_perfil_dre,
    exportar_planilha_importacao_usuarios_perfil_escola,
    exportar_planilha_importacao_usuarios_servidor_coresso,
    exportar_planilha_importacao_usuarios_ue_parceira_coresso,
)
from .models import (
    Cargo,
    ImportacaoPlanilhaUsuarioPerfilCodae,
    ImportacaoPlanilhaUsuarioPerfilDre,
    ImportacaoPlanilhaUsuarioPerfilEscola,
    Perfil,
    PerfisVinculados,
    PlanilhaDiretorCogestor,
    Usuario,
    Vinculo,
)
from .models.usuario import (
    ImportacaoPlanilhaUsuarioExternoCoreSSO,
    ImportacaoPlanilhaUsuarioServidorCoreSSO,
    ImportacaoPlanilhaUsuarioUEParceiraCoreSSO,
)


class BaseUserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "email",
                    "tipo_email",
                    "password",
                    "cpf",
                    "registro_funcional",
                    "nome",
                    "cargo",
                    "crn_numero",
                    "aceitou_termos",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "cpf",
                    "registro_funcional",
                    "nome",
                    "cargo",
                ),
            },
        ),
    )
    list_display = (
        "email",
        "username",
        "nome",
        "registro_funcional",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "nome")
    ordering = ("username",)
    actions = ("carga_dados", "atualiza_username_servidores")

    def carga_dados(self, request, queryset):
        return call_command("carga_dados")

    def atualiza_username_servidores(self, request, queryset):
        return call_command("atualiza_username_servidores")


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("nome", "super_usuario", "ativo")
    search_fields = ("nome",)


@admin.register(PerfisVinculados)
class PerfisVinculadosAdmin(admin.ModelAdmin):
    list_display = ("perfil_master",)
    search_fields = ("perfil_master",)


class InputFilter(admin.SimpleListFilter):
    template = "admin/textinput_filter.html"

    def lookups(self, request, model_admin):
        return ((),)

    def choices(self, changelist):
        all_choice = next(super().choices(changelist))
        all_choice["query_parts"] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class IDFilter(InputFilter):
    parameter_name = "object_id"
    title = _("Object_id")

    def queryset(self, request, queryset):
        if self.value() is not None:
            object_id = self.value()

            return queryset.filter(object_id=object_id)


class CodigoEOLFilter(InputFilter):
    parameter_name = "codigo_eol"
    title = _("Código EOL")

    def queryset(self, request, queryset):
        if self.value() is not None:
            codigo_eol = self.value()

            content_type_escola = ContentType.objects.get_for_model(Escola)
            vinculos_escolas = Vinculo.objects.filter(content_type=content_type_escola)
            escola = Escola.objects.filter(
                id__in=vinculos_escolas.values("object_id"), codigo_eol=codigo_eol
            ).first()

            if escola:
                return Vinculo.objects.filter(
                    content_type=content_type_escola, object_id=escola.id
                )
            return Vinculo.objects.none()


class NomeUEFilter(InputFilter):
    parameter_name = "nome_ue"
    title = _("Nome da UE")

    def queryset(self, request, queryset):
        if self.value() is not None:
            nome_ue = self.value()

            content_type_escola = ContentType.objects.get_for_model(Escola)
            vinculos_escolas = Vinculo.objects.filter(content_type=content_type_escola)
            escolas = Escola.objects.filter(
                id__in=vinculos_escolas.values("object_id"), nome__icontains=nome_ue
            ).values_list("id", flat=True)
            if escolas:
                return Vinculo.objects.filter(
                    content_type=content_type_escola, object_id__in=escolas
                )
            return Vinculo.objects.none()


@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "perfil", "content_type", "instituicao")
    search_fields = (
        "usuario__nome",
        "usuario__username",
        "usuario__email",
        "usuario__registro_funcional",
        "usuario__cpf",
    )
    search_help_text = "Pesquisa por: nome do usuário, username, email, CPF ou RF"
    list_filter = (
        "ativo",
        "content_type",
        IDFilter,
        CodigoEOLFilter,
        NomeUEFilter,
        "perfil__nome",
    )
    raw_id_fields = ("usuario",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "perfil":
            kwargs["queryset"] = Perfil.objects.order_by("nome")
        return super(VinculoAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    def get_content_type(self, value):  # noqa
        if value == "CODAE":
            return "CODAE"
        elif value == "EMPRESA":
            return "Terceirizada"
        elif value == "DRE":
            return "Diretoria regional"
        elif value == "ESCOLA":
            return "Escola"

    def save_model(self, request, obj, form, change):
        content = obj.perfil.visao
        if self.get_content_type(content) not in str(obj.content_type):
            return messages.error(
                request, "A visão do perfil e o content type devem ser equivalentes!"
            )
        else:
            super(VinculoAdmin, self).save_model(request, obj, form, change)


@admin.register(PlanilhaDiretorCogestor)
class PlanilhaDiretorCogestorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "criado_em")

    def save_model(self, request, obj, form, change):
        # Lendo arquivo InMemoryUploadedFile
        arquivo = request.FILES.get("arquivo")
        items = cria_usuario_diretor(arquivo, in_memory=True)
        cria_usuario_cogestor(items)
        super(PlanilhaDiretorCogestorAdmin, self).save_model(
            request, obj, form, change
        )  # noqa


@admin.register(ImportacaoPlanilhaUsuarioPerfilEscola)
class ImportacaoPlanilhaUsuarioPerfilEscolaAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/perfil/importacao_usuarios_perfil_escola.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_usuarios_perfil_escola/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_usuarios_perfil_escola(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_usuarios_perfil_escola(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos usuários perfil Escola"
    )


@admin.register(ImportacaoPlanilhaUsuarioPerfilCodae)
class ImportacaoPlanilhaUsuarioPerfilCodaeAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/perfil/importacao_usuarios_perfil_codae.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_usuarios_perfil_codae/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_usuarios_perfil_codae(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_usuarios_perfil_codae(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos usuários perfil Codae"
    )


@admin.register(ImportacaoPlanilhaUsuarioPerfilDre)
class ImportacaoPlanilhaUsuarioPerfilDreAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/perfil/importacao_usuarios_perfil_dre.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_usuarios_perfil_dre/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_usuarios_perfil_dre(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_usuarios_perfil_dre(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos usuários perfil Dre"
    )


@admin.register(ImportacaoPlanilhaUsuarioServidorCoreSSO)
class ImportacaoPlanilhaUsuarioServidorCoreSSOAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/perfil/importacao_usuarios_servidor_coresso.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_usuarios_servidor_coresso/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_usuarios_servidor_coresso(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_usuarios_servidores_coresso(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos usuários perfil servidor CoreSSO"
    )


@admin.register(ImportacaoPlanilhaUsuarioExternoCoreSSO)
class ImportacaoPlanilhaUsuarioExternoCoreSSOAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/perfil/importacao_usuarios_externos_coresso.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_usuarios_externos_coresso/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_usuarios_externos_coresso(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_usuarios_externos_coresso(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos usuários perfil externo CoreSSO"
    )


@admin.register(ImportacaoPlanilhaUsuarioUEParceiraCoreSSO)
class ImportacaoPlanilhaUsuarioUEParceiraCoreSSOAdmin(admin.ModelAdmin):
    list_display = ("id", "uuid", "__str__", "criado_em", "status")
    readonly_fields = ("resultado", "status", "log")
    list_filter = ("status",)
    actions = ("processa_planilha",)
    change_list_template = "admin/perfil/importacao_usuarios_ue_parceira_coresso.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "exportar_planilha_importacao_usuarios_ue_parceira_coresso/",
                self.admin_site.admin_view(self.exporta_planilha, cacheable=True),
            ),
        ]
        return my_urls + urls

    def exporta_planilha(self, request):
        return exportar_planilha_importacao_usuarios_ue_parceira_coresso(request)

    def processa_planilha(self, request, queryset):
        arquivo = queryset.first()

        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
            return
        if not valida_arquivo_importacao_usuarios(arquivo=arquivo):
            self.message_user(request, "Arquivo não suportado.", messages.ERROR)
            return

        importa_usuarios_ues_parceiras_coresso(request.user, arquivo)

        self.message_user(
            request,
            f"Processo Terminado. Verifique o status do processo: {arquivo.uuid}",
        )

    processa_planilha.short_description = (
        "Realizar a importação dos usuários perfil servidor CoreSSO"
    )


admin.site.register(Usuario, BaseUserAdmin)
admin.site.register(Cargo)
