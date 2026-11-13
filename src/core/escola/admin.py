from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.dados_comuns.constants import StringsSearchHelpText

from ..models import (
    AlunosMatriculadosPeriodoEscola,
    DiaCalendario,
    Escola,
    EscolaPeriodoEscolar,
    GrupoUnidadeEscolar,
    HistoricoEscola,
    PeriodoEscolar,
    TipoGestao,
    TipoUnidadeEscolar,
)


class EscolaPeriodoEscolarAdmin(admin.ModelAdmin):
    search_fields = ("escola__nome", "periodo_escolar__nome")


@admin.register(Escola)
class EscolaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_eol",
        "codigo_codae",
        "nome",
        "diretoria_regional",
        "tipo_gestao",
        "tipo_unidade",
        "enviar_email_por_produto",
    )
    search_fields = (
        "codigo_eol",
        "codigo_codae",
        "nome",
        "diretoria_regional__nome",
        "tipo_unidade__iniciais",
    )
    list_filter = (
        "enviar_email_por_produto",
        "acesso_modulo_medicao_inicial",
        "diretoria_regional",
        "tipo_gestao",
        "tipo_unidade",
        "subprefeitura",
    )
    ordering = ("codigo_eol", "nome")
    actions = ("marcar_para_receber_email", "marcar_para_nao_receber_email")
    readonly_fields = ("uuid",)

    def marcar_para_receber_email(self, request, queryset):
        count = queryset.update(enviar_email_por_produto=True)

        if count == 1:
            msg = "{} escola foi marcada para receber e-mail dos produtos."  # noqa P103
        else:
            msg = "{} escolas foram marcadas para receber e-mail dos produtos."  # noqa P103

        self.message_user(request, msg.format(count))

    marcar_para_receber_email.short_description = (
        "Marcar para receber e-mail dos produtos"
    )

    def marcar_para_nao_receber_email(self, request, queryset):
        count = queryset.update(enviar_email_por_produto=False)

        if count == 1:
            msg = "{} escola foi marcada para não receber e-mail dos produtos."  # noqa P103
        else:
            msg = "{} escolas foram marcadas para não receber e-mail dos produtos."  # noqa P103

        self.message_user(request, msg.format(count))

    marcar_para_nao_receber_email.short_description = (
        "Marcar para não receber e-mail dos produtos"
    )


@admin.register(AlunosMatriculadosPeriodoEscola)
class AlunosMatriculadosPeriodoEscolaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "alterado_em", "tipo_turma")
    search_fields = ("escola__nome", "periodo_escolar__nome")
    list_filter = ("alterado_em", "tipo_turma")


@admin.register(DiaCalendario)
class DiaCalendarioAdmin(admin.ModelAdmin):
    list_display = ("escola", "data", "dia_letivo", "periodo_escolar", "__str__")
    search_fields = ("escola__nome", "escola__codigo_eol")
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA.value
    )
    list_filter = (("data", DateRangeFilter), "periodo_escolar", "dia_letivo")
    ordering = ("-data",)


@admin.register(PeriodoEscolar)
class PeriodoEscolarAdmin(admin.ModelAdmin):
    list_display = ("nome", "posicao")
    search_fields = ("nome",)
    readonly_fields = ("uuid",)


admin.site.register(EscolaPeriodoEscolar, EscolaPeriodoEscolarAdmin)


admin.site.register(GrupoUnidadeEscolar)


admin.site.register(HistoricoEscola)


admin.site.register(TipoGestao)


admin.site.register(TipoUnidadeEscolar)
