from datetime import datetime, timedelta

from django_filters import rest_framework as filters

from sme_sigpae_api.escola.models import Aluno, HistoricoMatriculaAluno


class DiretoriaRegionalFilter(filters.FilterSet):
    dre = filters.CharFilter(
        field_name="diretoria_regional__uuid", lookup_expr="iexact"
    )


class AlunoFilter(filters.FilterSet):
    codigo_eol = filters.CharFilter(field_name="codigo_eol", lookup_expr="iexact")
    dre = filters.CharFilter(
        field_name="escola__diretoria_regional__uuid", lookup_expr="iexact"
    )
    escola = filters.CharFilter(field_name="escola__uuid", method="filter_escola")
    nao_tem_dieta_especial = filters.BooleanFilter(
        field_name="dietas_especiais", lookup_expr="isnull"
    )
    periodo_escolar_nome = filters.CharFilter(
        field_name="periodo_escolar__nome", lookup_expr="iexact"
    )

    def filter_escola(self, queryset, name, value):
        _filter = {name: value}

        alunos_atualmente_na_escola = queryset.filter(**_filter)

        if self.request.query_params.get("inclui_alunos_egressos") != "true":
            return alunos_atualmente_na_escola

        historicos_da_escola = HistoricoMatriculaAluno.objects.filter(**_filter)

        mes = self.request.query_params.get("mes")
        ano = self.request.query_params.get("ano")
        if mes is not None and ano is not None:
            ultimo_dia_do_mes = datetime(
                int(ano), min(int(mes) + 1, 12), 1
            ) - timedelta(days=1)
            primeiro_dia_do_mes = datetime(int(ano), int(mes), 1)

            historicos_da_escola_ativos = historicos_da_escola.filter(
                data_inicio__lte=ultimo_dia_do_mes, data_fim__isnull=True
            )
            historicos_da_escola_concluidos = historicos_da_escola.filter(
                data_inicio__lte=ultimo_dia_do_mes, data_fim__gte=primeiro_dia_do_mes
            )
            historicos_da_escola = (
                historicos_da_escola_ativos | historicos_da_escola_concluidos
            )

        alunos_com_historico_na_escola = Aluno.objects.filter(
            id__in=historicos_da_escola.values_list("aluno_id", flat=True)
        )

        return alunos_com_historico_na_escola


class LogAlunosMatriculadosFaixaEtariaDiaFilter(filters.FilterSet):
    escola_uuid = filters.UUIDFilter(field_name="escola__uuid")
    nome_periodo_escolar = filters.CharFilter(field_name="periodo_escolar__nome")
    mes = filters.CharFilter(field_name="data__month", lookup_expr="exact")
    ano = filters.CharFilter(field_name="data__year", lookup_expr="iexact")
    dias = filters.BaseInFilter(field_name="data__day", lookup_expr="in")
