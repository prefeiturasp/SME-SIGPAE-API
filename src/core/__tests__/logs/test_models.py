import datetime

import pytest

from ....dados_comuns.constants import TIPO_UNIDADE_CEI_DIRET, TIPOS_UNIDADE_ESCOLAR
from ...models import (
    AlunosMatriculadosPeriodoEscola,
    LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    LogAtualizaDadosAluno,
    LogRotinaDiariaAlunos,
)

pytestmark = pytest.mark.django_db


def test_modelo_log_alunos_matriculados_periodo_escola_regular(
    log_alunos_matriculados_periodo_escola_regular,
):
    model = log_alunos_matriculados_periodo_escola_regular
    assert isinstance(model, LogAlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "REGULAR"


def test_modelo_log_alunos_matriculados_periodo_escola_programas(
    log_alunos_matriculados_periodo_escola_programas,
):
    model = log_alunos_matriculados_periodo_escola_programas
    assert isinstance(model, LogAlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "PROGRAMAS"


def test_criar_log_alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    hoje = datetime.date.today()
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 0
    LogAlunosMatriculadosPeriodoEscola.criar(
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        data=hoje,
        tipo_turma="REGULAR",
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 1
    assert LogAlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    log = LogAlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {log.quantidade_alunos} alunos" in log.__str__()


def test_criar_log_alunos_matriculados_periodo_escola_cemei_regular(
    escola_cemei, periodo_escolar
):
    hoje = datetime.date.today()
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 0
    LogAlunosMatriculadosPeriodoEscola.criar(
        escola=escola_cemei,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        data=hoje,
        tipo_turma="REGULAR",
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 3
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            cei_ou_emei=TIPOS_UNIDADE_ESCOLAR.CEI.value
        ).exists()
        is True
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            cei_ou_emei=TIPOS_UNIDADE_ESCOLAR.EMEI.value
        ).exists()
        is True
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    log = LogAlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {log.quantidade_alunos} alunos" in log.__str__()


def test_criar_log_alunos_matriculados_periodo_escola_emebs_regular(
    escola_emebs, periodo_escolar
):
    hoje = datetime.date.today()
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 0
    LogAlunosMatriculadosPeriodoEscola.criar(
        escola=escola_emebs,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        data=hoje,
        tipo_turma="REGULAR",
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.count() == 3
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            infantil_ou_fundamental="INFANTIL", quantidade_alunos=1
        ).exists()
        is True
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            infantil_ou_fundamental="FUNDAMENTAL", quantidade_alunos=1
        ).exists()
        is True
    )
    assert LogAlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    log = LogAlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {log.quantidade_alunos} alunos" in log.__str__()


def test_log_alunos_matriculados_faixa_etaria_dia(
    log_alunos_matriculados_faixa_etaria_dia,
):
    model = log_alunos_matriculados_faixa_etaria_dia
    quantidade = model.quantidade
    faixa_etaria = model.faixa_etaria
    assert isinstance(model, LogAlunosMatriculadosFaixaEtariaDia)
    assert model.criado_em is not None
    assert model.data is not None
    assert f"{quantidade} aluno(s)" in model.__str__()
    assert f"faixa etária {faixa_etaria}" in model.__str__()


def test_log_atualiza_dados_aluno(log_atualiza_dados_aluno):
    model = log_atualiza_dados_aluno
    codigo_eol = model.codigo_eol
    criado_em = model.criado_em
    assert isinstance(model, LogAtualizaDadosAluno)
    assert model.criado_em is not None
    assert model.status == 200
    assert (
        model.__str__()
        == f'Requisicao para Escola: "#{codigo_eol}" na data de: "{criado_em}"'
    )


def test_log_rotina_diaria_alunos(log_rotina_diaria_alunos):
    model = log_rotina_diaria_alunos
    criado_em = model.criado_em.strftime("%Y-%m-%d %H:%M:%S")
    quant_antes = model.quantidade_alunos_antes
    quant_atual = model.quantidade_alunos_atual
    string_model = (
        f"Criado em {criado_em} - Quant. de alunos antes: {quant_antes}. "
        f"Quant. de alunos atual: {quant_atual}"
    )
    assert isinstance(model, LogRotinaDiariaAlunos)
    assert model.criado_em is not None
    assert model.__str__() == string_model


def test_log_alteracao_quantidade_alunos_por_escola_periodo(
    log_alteracao_quantidade_alunos_por_escola_periodo,
):
    model = log_alteracao_quantidade_alunos_por_escola_periodo
    quantidade_anterior = model.quantidade_alunos_de
    quantidade_atual = model.quantidade_alunos_para
    escola = model.escola.nome
    string_model = f"Alteração de: {quantidade_anterior} alunos, para: {quantidade_atual} alunos na escola: {escola}"
    assert isinstance(model, LogAlteracaoQuantidadeAlunosPorEscolaEPeriodoEscolar)
    assert model.criado_em is not None
    assert model.__str__() == string_model


def test_formata_para_relatorio_verifica_periodo(log_alunos_matriculados_cei):
    alunos_matriculados_manha = AlunosMatriculadosPeriodoEscola.objects.get(
        periodo_escolar__nome="MANHA",
        escola__tipo_unidade__iniciais=TIPO_UNIDADE_CEI_DIRET,
    )
    data = alunos_matriculados_manha.formata_para_relatorio()
    assert data["periodo_escolar"] == "Infantil Manhã"
    assert data["eh_cei"] is True

    alunos_matriculados_tarde = AlunosMatriculadosPeriodoEscola.objects.get(
        periodo_escolar__nome="TARDE",
        escola__tipo_unidade__iniciais=TIPO_UNIDADE_CEI_DIRET,
    )
    data = alunos_matriculados_tarde.formata_para_relatorio()
    assert data["periodo_escolar"] == "Infantil Tarde"
    assert data["eh_cei"] is True

    alunos_matriculados_integral = AlunosMatriculadosPeriodoEscola.objects.get(
        periodo_escolar__nome="INTEGRAL",
        escola__tipo_unidade__iniciais=TIPO_UNIDADE_CEI_DIRET,
    )
    data = alunos_matriculados_integral.formata_para_relatorio()
    assert data["periodo_escolar"] == "INTEGRAL"
    assert data["eh_cei"] is True
