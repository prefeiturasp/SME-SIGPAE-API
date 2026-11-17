import pytest
from model_bakery import baker

from src.core.logs.api.filters import LogAlunosMatriculadosFaixaEtariaDiaFilter
from src.core.models import (
    Escola,
    LogAlunosMatriculadosFaixaEtariaDia,
    TipoUnidadeEscolar,
)
from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR

pytestmark = pytest.mark.django_db


@pytest.fixture
def escolas_para_filtros(tipo_gestao):
    dre = baker.make("DiretoriaRegional", nome="DRE FILTROS")
    tipo_emef = baker.make(
        TipoUnidadeEscolar, iniciais=TIPOS_UNIDADE_ESCOLAR.EMEF.value
    )
    tipo_cei = baker.make(TipoUnidadeEscolar, iniciais=TIPOS_UNIDADE_ESCOLAR.CEI.value)
    lote_a = baker.make("Lote", nome="LOTE A")
    lote_b = baker.make("Lote", nome="LOTE B")

    escola_emef_lote_a = baker.make(
        Escola,
        codigo_eol="000001",
        diretoria_regional=dre,
        tipo_unidade=tipo_emef,
        lote=lote_a,
        tipo_gestao=tipo_gestao,
    )
    escola_emef_lote_b = baker.make(
        Escola,
        codigo_eol="000002",
        diretoria_regional=dre,
        tipo_unidade=tipo_emef,
        lote=lote_b,
        tipo_gestao=tipo_gestao,
    )
    escola_cei_lote_a = baker.make(
        Escola,
        codigo_eol="000003",
        diretoria_regional=dre,
        tipo_unidade=tipo_cei,
        lote=lote_a,
        tipo_gestao=tipo_gestao,
    )

    return {
        "dre": dre,
        "tipo_emef": tipo_emef,
        "tipo_cei": tipo_cei,
        "lote_a": lote_a,
        "lote_b": lote_b,
        "escola_emef_lote_a": escola_emef_lote_a,
        "escola_emef_lote_b": escola_emef_lote_b,
        "escola_cei_lote_a": escola_cei_lote_a,
    }


def test_log_aluno_filter_escola(log_alunos_matriculados_faixa_etaria_dia):
    escola = log_alunos_matriculados_faixa_etaria_dia.escola
    filtro_escola = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"escola_uuid": escola.uuid},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_escola.qs.count() == 1
    assert filtro_escola.qs[0].escola == escola

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"escola_uuid": escola.diretoria_regional.uuid},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_periodo_escola(log_alunos_matriculados_faixa_etaria_dia):
    periodo_escolar = log_alunos_matriculados_faixa_etaria_dia.periodo_escolar

    filtro_periodo_escola = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"nome_periodo_escolar": periodo_escolar.nome},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_periodo_escola.qs.count() == 1
    assert filtro_periodo_escola.qs[0].periodo_escolar == periodo_escolar

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"nome_periodo_escolar": periodo_escolar.uuid},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_mes(log_alunos_matriculados_faixa_etaria_dia):
    data = log_alunos_matriculados_faixa_etaria_dia.data
    filtro_mes = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"mes": data.month},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_mes.qs.count() == 1
    assert filtro_mes.qs[0].data.month == data.month

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"mes": 0}, queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all()
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_ano(log_alunos_matriculados_faixa_etaria_dia):
    data = log_alunos_matriculados_faixa_etaria_dia.data
    filtro_ano = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"ano": data.year},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_ano.qs.count() == 1
    assert filtro_ano.qs[0].data.year == data.year

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"ano": "cinco"},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_dia(log_alunos_matriculados_faixa_etaria_dia):
    data = log_alunos_matriculados_faixa_etaria_dia.data
    filtro_dias = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"dias": [data.day]},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_dias.qs.count() == 1
    assert filtro_dias.qs[0].data.day == data.day

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"dias": [data.day + 1]},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0
