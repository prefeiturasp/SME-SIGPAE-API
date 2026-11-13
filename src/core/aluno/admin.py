from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.dados_comuns.constants import StringsSearchHelpText

from ..models import Aluno, AlunoPeriodoParcial, HistoricoMatriculaAluno, Responsavel


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "escola")
    list_filter = ("periodo_escolar",)
    search_fields = ("nome", "escola__nome", "codigo_eol", "escola__codigo_eol")


@admin.register(HistoricoMatriculaAluno)
class HistoricoMatriculaAlunoAdmin(admin.ModelAdmin):
    list_display = ("aluno", "escola", "data_inicio", "data_fim", "situacao")
    search_fields = ("aluno__nome", "escola__nome", "aluno__codigo_eol")
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DO_ALUNO_NOME_DA_ESCOLA_OU_CODIGO_EOL_DO_ALUNO.value
    )
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
    search_fields = (
        "aluno__nome",
        "aluno__codigo_eol",
        "escola__nome",
        "escola__codigo_eol",
    )
    search_help_text = (
        StringsSearchHelpText.PESQUISE_POR_NOME_DO_ALUNO_CODIGO_EOL_DO_ALUNO_NOME_DA_ESCOLA_OU_CODIGO_EOL_DA_ESCOLA.value
    )


admin.site.register(Responsavel)
