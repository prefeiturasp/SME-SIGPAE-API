from django.contrib import admin
from django.db.models import F

from ..dados_comuns.actions import export_as_xls
from .models import (
    Contrato,
    Edital,
    EmailTerceirizadaPorModulo,
    Modalidade,
    Modulo,
    Nutricionista,
    Terceirizada,
    VigenciaContrato,
)


class NutricionistasInline(admin.TabularInline):
    model = Nutricionista
    extra = 1


@admin.register(Terceirizada)
class TerceirizadaModelAdmin(admin.ModelAdmin):
    actions = ("export_usuarios_por_empresa",)
    list_filter = ("tipo_empresa", "tipo_servico")

    def export_usuarios_por_empresa(self, request, queryset):
        qs = queryset.filter(vinculos__content_type__model="terceirizada").annotate(
            perfil=F("vinculos__perfil__nome"),
            nome_usuario=F("vinculos__usuario__nome"),
            email_usuario=F("vinculos__usuario__email"),
        )
        field_names = [
            "nome_usuario",
            "email_usuario",
            "razao_social",
            "cnpj",
            "tipo_empresa",
            "perfil",
        ]
        return export_as_xls(self, request, qs, field_names)

    export_usuarios_por_empresa.short_description = (
        "Exportar Planilha com Usuários das Empresas"
    )


class GrupoSuspensaoAlimentacaoModelAdmin(admin.ModelAdmin):
    inlines = [NutricionistasInline]
    search_fields = ("nome_fantasia",)
    readonly_fields = ("contatos",)


class VigenciaContratoInline(admin.TabularInline):
    model = VigenciaContrato
    extra = 1


@admin.register(Contrato)
class ContratoModelAdmin(admin.ModelAdmin):
    inlines = [VigenciaContratoInline]

    search_fields = ("edital__numero",)


class ContratoInline(admin.TabularInline):
    model = Contrato
    extra = 1


@admin.register(Edital)
class EditalModelAdmin(admin.ModelAdmin):
    search_fields = ("numero",)
    inlines = [ContratoInline]
    readonly_fields = ("uuid",)


@admin.register(Modulo)
class ModuloModelAdmin(admin.ModelAdmin):
    model = Modulo


@admin.register(EmailTerceirizadaPorModulo)
class EmailTerceirizadaPorModuloModelAdmin(admin.ModelAdmin):
    model = EmailTerceirizadaPorModulo


@admin.register(Modalidade)
class ModalidadeModelAdmin(admin.ModelAdmin):
    model = Modalidade
