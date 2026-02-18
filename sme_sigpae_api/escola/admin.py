import logging

import magic
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from rangefilter.filters import DateRangeFilter

from .api.viewsets import exportar_planilha_importacao_tipo_gestao_escola
from .models import (
    Aluno,
    AlunoPeriodoParcial,
    AlunosMatriculadosPeriodoEscola,
    Codae,
    DiaCalendario,
    DiretoriaRegional,
    Escola,
    EscolaPeriodoEscolar,
    FaixaIdadeEscolar,
    GrupoUnidadeEscolar,
    HistoricoEscola,
    HistoricoMatriculaAluno,
    LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
    LogAlunoPorDia,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    LogAtualizaDadosAluno,
    LogRotinaDiariaAlunos,
    Lote,
    PeriodoEscolar,
    PlanilhaAtualizacaoTipoGestaoEscola,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
    Responsavel,
    Subprefeitura,
    TipoGestao,
    TipoUnidadeEscolar,
)
from .tasks import (
    atualiza_codigo_codae_das_escolas_task,
    atualiza_tipo_gestao_das_escolas_task,
)

logger = logging.getLogger("sigpae.escola")


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


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ("iniciais", "__str__")
    list_display_links = ("__str__",)
    search_fields = ("iniciais", "nome", "diretoria_regional__nome")


@admin.register(DiretoriaRegional)
class DiretoriaRegionalAdmin(admin.ModelAdmin):
    list_display = ("iniciais", "__str__")
    list_display_links = ("__str__",)
    search_fields = ("codigo_eol", "nome")
    list_filter = ("acesso_modulo_medicao_inicial",)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "escola")
    list_filter = ("periodo_escolar",)
    search_fields = ("nome", "escola__nome", "codigo_eol", "escola__codigo_eol")


@admin.register(PlanilhaEscolaDeParaCodigoEolCodigoCoade)
class PlanilhaEscolaDeParaCodigoEolCodigoCoadeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "criado_em", "codigos_codae_vinculados")
    actions = ("vincular_codigos_codae_da_planilha",)

    def vincular_codigos_codae_da_planilha(self, request, queryset):
        if len(queryset) > 1:
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
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
            self.message_user(request, "Escolha somente uma planilha.", messages.ERROR)
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


@admin.register(AlunosMatriculadosPeriodoEscola)
class AlunosMatriculadosPeriodoEscolaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "alterado_em", "tipo_turma")
    search_fields = ("escola__nome", "periodo_escolar__nome")
    list_filter = ("alterado_em", "tipo_turma")


@admin.register(LogAtualizaDadosAluno)
class LogErroAtualizaDadosAlunoAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "codigo_eol", "status", "msg_erro")
    search_fields = ("criado_em", "codigo_eol", "status", "msg_erro")


@admin.register(LogAlunosMatriculadosPeriodoEscola)
class LogAlunosMatriculadosPeriodoEscolaAdmin(admin.ModelAdmin):
    list_display = (
        "escola",
        "periodo_escolar",
        "cei_ou_emei",
        "get_tipo_turma",
        "quantidade_alunos",
        "criado_em",
        "infantil_ou_fundamental",
    )
    search_fields = ("escola__nome", "escola__codigo_eol", "periodo_escolar__nome")
    list_filter = (
        ("criado_em", DateRangeFilter),
        "periodo_escolar__nome",
        "tipo_turma",
        "escola__diretoria_regional",
        "cei_ou_emei",
        "infantil_ou_fundamental",
    )

    @admin.display(description="Tipo Turma")
    def get_tipo_turma(self, obj):
        return obj.tipo_turma


@admin.register(LogAlunosMatriculadosFaixaEtariaDia)
class LogAlunosMatriculadosFaixaEtariaDiaAdmin(admin.ModelAdmin):
    list_display = (
        "escola",
        "periodo_escolar",
        "faixa_etaria",
        "quantidade",
        "data",
        "criado_em",
    )
    search_fields = ("escola__nome", "periodo_escolar__nome")
    list_filter = (
        ("data", DateRangeFilter),
        "periodo_escolar__nome",
        "escola__tipo_unidade",
    )
    ordering = ("-criado_em", "escola__nome")


@admin.register(LogAlunoPorDia)
class LogAlunoPorDiaAdmin(admin.ModelAdmin):
    list_display = (
        "aluno",
        "get_escola",
        "get_periodo",
        "get_faixa_etaria",
        "get_data",
        "criado_em",
    )
    search_fields = (
        "aluno__nome",
        "aluno__codigo_eol",
        "log_alunos_matriculados_faixa_dia__escola__nome",
    )
    list_filter = (("log_alunos_matriculados_faixa_dia__data", DateRangeFilter),)
    ordering = ("-criado_em",)

    @admin.display(description="Escola")
    def get_escola(self, obj):
        return obj.log_alunos_matriculados_faixa_dia.escola.nome

    @admin.display(description="Período")
    def get_periodo(self, obj):
        return obj.log_alunos_matriculados_faixa_dia.periodo_escolar.nome

    @admin.display(description="Faixa Etária")
    def get_faixa_etaria(self, obj):
        return obj.log_alunos_matriculados_faixa_dia.faixa_etaria

    @admin.display(description="Data")
    def get_data(self, obj):
        return obj.log_alunos_matriculados_faixa_dia.data


@admin.register(DiaCalendario)
class DiaCalendarioAdmin(admin.ModelAdmin):
    list_display = ("escola", "data", "dia_letivo", "periodo_escolar", "__str__")
    search_fields = ("escola__nome", "escola__codigo_eol")
    search_help_text = "Pesquise por: nome da escola, código eol da escola"
    list_filter = (("data", DateRangeFilter), "periodo_escolar", "dia_letivo")
    ordering = ("-data",)


@admin.register(PeriodoEscolar)
class PeriodoEscolarAdmin(admin.ModelAdmin):
    list_display = ("nome", "posicao")
    search_fields = ("nome",)
    readonly_fields = ("uuid",)


@admin.register(HistoricoMatriculaAluno)
class HistoricoMatriculaAlunoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "escola", "data_inicio", "data_fim", "situacao")
    search_fields = ("aluno__nome", "escola__nome", "aluno__codigo_eol")
    list_filter = (
        "situacao",
        "escola__diretoria_regional",
        ("data_inicio", DateRangeFilter),
        ("data_fim", DateRangeFilter),
    )
    readonly_fields = ("aluno", "escola")


@admin.register(AlunoPeriodoParcial)
class AlunoPeriodoParcialAdmin(admin.ModelAdmin):
    list_display = ("aluno", "escola", "solicitacao_medicao_inicial")


admin.site.register(Codae)
admin.site.register(EscolaPeriodoEscolar, EscolaPeriodoEscolarAdmin)
admin.site.register(FaixaIdadeEscolar)
admin.site.register(LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar)
admin.site.register(LogRotinaDiariaAlunos)
admin.site.register(Responsavel)
admin.site.register(Subprefeitura)
admin.site.register(TipoGestao)
admin.site.register(TipoUnidadeEscolar)
admin.site.register(GrupoUnidadeEscolar)
admin.site.register(HistoricoEscola)
