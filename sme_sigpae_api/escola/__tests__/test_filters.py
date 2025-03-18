from unittest.mock import Mock

import pytest

from sme_sigpae_api.escola.api.filters import (
    AlunoFilter,
    DiretoriaRegionalFilter,
    LogAlunosMatriculadosFaixaEtariaDiaFilter,
)
from sme_sigpae_api.escola.models import (
    Aluno,
    Escola,
    LogAlunosMatriculadosFaixaEtariaDia,
)

pytestmark = pytest.mark.django_db


def test_diretoria_regional_filter(diretoria_regional):
    filtro_dre = DiretoriaRegionalFilter(
        data={"dre": diretoria_regional.uuid},
        queryset=Escola.objects.all().prefetch_related("diretoria_regional"),
    )
    assert filtro_dre.qs.count() == 3
    for escola in filtro_dre.qs:
        assert escola.diretoria_regional.nome == diretoria_regional.nome
        assert str(escola.diretoria_regional.uuid) == diretoria_regional.uuid


def test_aluno_filter_codigo_eol(aluno):
    filtro_codigo_eol = AlunoFilter(
        data={"codigo_eol": aluno.codigo_eol}, queryset=Aluno.objects.all()
    )
    assert filtro_codigo_eol.qs.count() == 1
    assert filtro_codigo_eol.qs[0].nome == aluno.nome
    assert filtro_codigo_eol.qs[0].codigo_eol == aluno.codigo_eol

    filtro = AlunoFilter(data={"codigo_eol": aluno.nome}, queryset=Aluno.objects.all())
    assert filtro.qs.count() == 0


def test_aluno_filter_dre(aluno):
    diretoria_regional = aluno.escola.diretoria_regional

    filtro_dre = AlunoFilter(
        data={"dre": diretoria_regional.uuid}, queryset=Aluno.objects.all()
    )
    assert filtro_dre.qs.count() == 1
    assert filtro_dre.qs[0].nome == aluno.nome
    assert (
        str(filtro_dre.qs[0].escola.diretoria_regional.uuid) == diretoria_regional.uuid
    )

    filtro = AlunoFilter(
        data={"dre": diretoria_regional.nome}, queryset=Aluno.objects.all()
    )
    assert filtro.qs.count() == 0


def test_aluno_filter_dieta_especial(dieta_codae_autorizou, dieta_cancelada):
    assert dieta_codae_autorizou.aluno == dieta_cancelada.aluno
    aluno = dieta_cancelada.aluno

    filtro_nao_tem_dieta_especial = AlunoFilter(
        data={"nao_tem_dieta_especial": True}, queryset=Aluno.objects.all()
    )
    assert filtro_nao_tem_dieta_especial.qs.count() == 0

    filtro_nao_tem_dieta_especial = AlunoFilter(
        data={"nao_tem_dieta_especial": False}, queryset=Aluno.objects.all()
    )
    assert filtro_nao_tem_dieta_especial.qs.count() == 2
    aluno_dieta = filtro_nao_tem_dieta_especial.qs.distinct()[0]
    assert aluno_dieta.dietas_especiais.count() == 2
    for dieta in aluno_dieta.dietas_especiais.all():
        assert dieta.aluno.nome == aluno.nome


def test_aluno_filter_periodo_escola(aluno):
    periodo_escolar = aluno.periodo_escolar

    filtro_periodo_escola = AlunoFilter(
        data={"periodo_escolar_nome": "TARDE"}, queryset=Aluno.objects.all()
    )
    assert filtro_periodo_escola.qs.count() == 0

    filtro_periodo_escola = AlunoFilter(
        data={"periodo_escolar_nome": periodo_escolar.nome},
        queryset=Aluno.objects.all(),
    )
    assert filtro_periodo_escola.qs.count() == 1
    assert filtro_periodo_escola.qs[0].nome == aluno.nome


def test_aluno_filter_escola_egressos_false(aluno):
    escola = aluno.escola

    mock_request = Mock()
    mock_request.query_params = {"inclui_alunos_egressos": "false"}
    filtro_escola = AlunoFilter(
        data={"escola": escola.uuid}, queryset=Aluno.objects.all(), request=mock_request
    )
    assert filtro_escola.qs.count() == 1
    assert filtro_escola.qs[0].nome == aluno.nome
    assert filtro_escola.qs[0].escola == escola


def test_aluno_filter_escola_egressos_true(aluno):
    escola = aluno.escola
    mock_request = Mock()
    mock_request.query_params = {
        "inclui_alunos_egressos": "true",
        "mes": "5",
        "ano": "2023",
    }
    filtro_escola = AlunoFilter(
        data={"escola": escola.uuid}, queryset=Aluno.objects.all(), request=mock_request
    )
    assert filtro_escola.qs.count() == 0


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
