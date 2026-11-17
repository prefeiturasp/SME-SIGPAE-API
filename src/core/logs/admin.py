from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.dados_comuns.constants import StringsSearchHelpText

from ..models import (
    LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
    LogAlunoPorDia,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    LogAtualizaDadosAluno,
    LogRotinaDiariaAlunos,
)


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
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA_OU_PERIODO_ESCOLAR.value
    )
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
    search_fields = ("escola__nome", "escola__codigo_eol", "periodo_escolar__nome")
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA_OU_PERIODO_ESCOLAR.value
    )
    list_filter = (
        ("data", DateRangeFilter),
        "periodo_escolar__nome",
        "escola__tipo_unidade",
        "faixa_etaria",
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
        "log_alunos_matriculados_faixa_dia__escola__codigo_eol",
    )
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DO_ALUNO_CODIGO_EOL_DO_ALUNO_NOME_DA_ESCOLA_OU_CODIGO_EOL_DA_ESCOLA.value
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


admin.site.register(LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar)


admin.site.register(LogRotinaDiariaAlunos)
