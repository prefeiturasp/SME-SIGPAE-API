import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from ....dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR
from ...models import (
    AlunosMatriculadosPeriodoEscola,
    DiaCalendario,
    DiretoriaRegional,
    EscolaPeriodoEscolar,
    LogAlunosMatriculadosPeriodoEscola,
    PeriodoEscolar,
    TipoGestao,
    TipoUnidadeEscolar,
)

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-11")
def test_tipo_unidade_escolar(tipo_unidade_escolar):
    assert isinstance(str(tipo_unidade_escolar), str)
    assert tipo_unidade_escolar.iniciais is not None
    assert tipo_unidade_escolar.periodos_escolares.all() is not None


def test_tipo_gestao(tipo_gestao):
    assert isinstance(str(tipo_gestao), str)
    assert tipo_gestao.nome is not None


def test_escola(escola):
    assert isinstance(str(escola), str)
    assert escola.nome is not None
    assert escola.codigo_eol is not None
    assert isinstance(escola.diretoria_regional, DiretoriaRegional)
    assert isinstance(escola.tipo_unidade, TipoUnidadeEscolar)
    assert isinstance(escola.tipo_gestao, TipoGestao)
    assert escola.lote is not None
    assert escola.periodos_escolares().all() is not None

    assert escola.grupos_inclusoes is not None
    assert escola.inclusoes_continuas is not None


def test_periodo_escolar(periodo_escolar):
    assert isinstance(str(periodo_escolar), str)


def test_escola_periodo_escolar_alunos_por_faixa_etaria(
    faixas_etarias,
    escola_periodo_escolar,
    eolservicosgp_get_lista_alunos,
):
    faixas_alunos = escola_periodo_escolar.alunos_por_faixa_etaria(
        datetime.date(2020, 10, 25)
    )
    assert [i for i in faixas_alunos.values()] == [2, 1]


def test_ordem(periodo_escolar):
    assert ("posicao",) == periodo_escolar._meta.ordering


def test_modelo_alunos_matriculados_periodo_escola_regular(
    alunos_matriculados_periodo_escola_regular,
):
    model = alunos_matriculados_periodo_escola_regular
    assert isinstance(model, AlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "REGULAR"


def test_modelo_alunos_matriculados_periodo_escola_programas(
    alunos_matriculados_periodo_escola_programas,
):
    model = alunos_matriculados_periodo_escola_programas
    assert isinstance(model, AlunosMatriculadosPeriodoEscola)
    assert model.criado_em is not None
    assert model.escola is not None
    assert model.periodo_escolar is not None
    assert model.quantidade_alunos == 50
    assert model.tipo_turma == "PROGRAMAS"


def test_criar_alunos_matriculados_periodo_escola_regular(escola, periodo_escolar):
    assert AlunosMatriculadosPeriodoEscola.objects.count() == 0
    AlunosMatriculadosPeriodoEscola.criar(
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=32,
        tipo_turma="REGULAR",
    )
    assert AlunosMatriculadosPeriodoEscola.objects.count() == 1
    assert AlunosMatriculadosPeriodoEscola.objects.first().tipo_turma == "REGULAR"
    AlunosMatriculadosPeriodoEscola.criar(
        escola=escola,
        periodo_escolar=periodo_escolar,
        quantidade_alunos=40,
        tipo_turma="REGULAR",
    )
    obj = AlunosMatriculadosPeriodoEscola.objects.all()[0]
    assert f"tem {obj.quantidade_alunos} alunos" in obj.__str__()


def test_dia_calendario_e_dia_letivo(dia_calendario_letivo):
    model = dia_calendario_letivo
    assert isinstance(model, DiaCalendario)
    assert model.criado_em is not None
    assert model.data is not None
    assert model.escola is not None
    assert model.dia_letivo
    assert "é dia letivo" in dia_calendario_letivo.__str__()


def test_dia_calendario_nao_e_dia_letivo(dia_calendario_nao_letivo):
    model = dia_calendario_nao_letivo
    assert isinstance(model, DiaCalendario)
    assert model.criado_em is not None
    assert model.data is not None
    assert model.escola is not None
    assert not model.dia_letivo
    assert "não é dia letivo" in dia_calendario_nao_letivo.__str__()


def test_dia_suspensao_atividades_model(dia_suspensao_atividades):
    assert (
        dia_suspensao_atividades.__str__()
        == "08/08/2022 - EMEF - Edital Edital de Pregão nº 13/SME/2020"
    )


def test_possui_alunos_regulares_retorna_false(
    alunos_matriculados_periodo_escola_programas,
):
    assert (
        alunos_matriculados_periodo_escola_programas.escola.possui_alunos_regulares
        is False
    )


def test_possui_alunos_regulares_retorna_true(
    alunos_matriculados_periodo_escola_regular,
):
    assert (
        alunos_matriculados_periodo_escola_regular.escola.possui_alunos_regulares
        is True
    )


@freeze_time("2025-05-05")
def test_periodos_escolares_escola_cei(
    escola_cei,
    periodo_escolar,
    log_aluno_integral_cei,
    log_alunos_matriculados_integral_cei,
):
    periodos = escola_cei.periodos_escolares(2025)
    assert periodos.count() == 1
    assert isinstance(periodos[0], PeriodoEscolar)
    assert periodos[0].nome == periodo_escolar.nome


def test_periodos_escolares_escola_cemei(escola_cemei):
    periodos = escola_cemei.periodos_escolares()
    assert periodos.count() == 0


def test_periodos_escolares_escola_emebs(escola_emebs):
    periodos = escola_emebs.periodos_escolares()
    assert periodos.count() == 0


def test_periodos_escolares_escola_cmct(escola_cmct):
    assert escola_cmct.possui_alunos_regulares is False
    periodos = escola_cmct.periodos_escolares().order_by("nome")
    assert periodos.count() == 2
    esperado = [("MANHA", PeriodoEscolar), ("NOITE", PeriodoEscolar)]
    for periodo, (nome_esperado, tipo_esperado) in zip(periodos, esperado):
        assert isinstance(periodo, tipo_esperado)
        assert periodo.nome == nome_esperado


def test_periodos_escolares_pega_atualmente_retorna_apenas_periodos_com_alunos(
    escola,
):
    escola.tipo_unidade.tem_somente_integral_e_parcial = False
    escola.tipo_unidade.save()

    manha = PeriodoEscolar.objects.create(nome="MANHA")
    tarde = PeriodoEscolar.objects.create(nome="TARDE")

    AlunosMatriculadosPeriodoEscola.objects.create(
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=1,
        tipo_turma="REGULAR",
    )

    EscolaPeriodoEscolar.objects.create(
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=10,
    )
    EscolaPeriodoEscolar.objects.create(
        escola=escola,
        periodo_escolar=tarde,
        quantidade_alunos=0,
    )

    periodos = escola.periodos_escolares(pega_atualmente=True).order_by("nome")

    assert periodos.count() == 1
    assert periodos[0].nome == "MANHA"
    assert isinstance(periodos[0], PeriodoEscolar)


@freeze_time("2025-05-05")
def test_periodos_escolares_pega_atualmente_false_retorna_periodos_com_logs_antigos(
    escola,
):
    escola.tipo_unidade.tem_somente_integral_e_parcial = False
    escola.tipo_unidade.save()

    ano_atual = datetime.date.today().year

    manha = PeriodoEscolar.objects.create(nome="MANHA")
    tarde = PeriodoEscolar.objects.create(nome="TARDE")

    AlunosMatriculadosPeriodoEscola.objects.create(
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=1,
        tipo_turma="REGULAR",
    )

    LogAlunosMatriculadosPeriodoEscola.objects.create(
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=30,
        tipo_turma="REGULAR",
        criado_em=datetime.date(ano_atual, 3, 15),
    )

    LogAlunosMatriculadosPeriodoEscola.objects.create(
        escola=escola,
        periodo_escolar=tarde,
        quantidade_alunos=25,
        tipo_turma="REGULAR",
        criado_em=datetime.date(ano_atual, 3, 20),
    )

    EscolaPeriodoEscolar.objects.create(
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=28,
    )
    EscolaPeriodoEscolar.objects.create(
        escola=escola,
        periodo_escolar=tarde,
        quantidade_alunos=0,
    )

    # ===== COMPORTAMENTO BUG =====
    # Sem a flag, retorna AMBOS os períodos
    # porque ambos têm logs do ano atual, mesmo que TARDE tenha 0 alunos agora
    periodos_com_bug = escola.periodos_escolares(
        ano=ano_atual, pega_atualmente=False
    ).order_by("nome")

    assert periodos_com_bug.count() == 2  # BUG: retorna MANHA e TARDE
    assert set(periodos_com_bug.values_list("nome", flat=True)) == {"MANHA", "TARDE"}

    # ===== COMPORTAMENTO CORRETO (COM A FLAG) =====
    # Com pega_atualmente=True, retorna apenas períodos com alunos AGORA
    periodos_correto = escola.periodos_escolares(pega_atualmente=True).order_by("nome")

    assert periodos_correto.count() == 1  # Retorna apenas MANHA
    assert periodos_correto[0].nome == "MANHA"


@freeze_time("2025-05-05")
def test_periodos_escolares_pega_atualmente_false_mantem_comportamento_legado(
    escola,
):
    escola.tipo_unidade.tem_somente_integral_e_parcial = False
    escola.tipo_unidade.save()

    ano_atual = datetime.date.today().year

    manha = PeriodoEscolar.objects.create(nome="MANHA")

    AlunosMatriculadosPeriodoEscola.objects.create(
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=1,
        tipo_turma="REGULAR",
    )

    # Log de janeiro
    LogAlunosMatriculadosPeriodoEscola.objects.create(
        escola=escola,
        periodo_escolar=manha,
        quantidade_alunos=30,
        tipo_turma="REGULAR",
        criado_em=datetime.date(ano_atual, 1, 15),
    )

    # Comportamento legado: busca por logs do ano
    periodos = escola.periodos_escolares(ano=ano_atual, pega_atualmente=False)

    assert periodos.count() == 1
    assert periodos[0].nome == "MANHA"


def test_dia_calendario_com_perido(
    dia_calendario_noturno, escola, periodo_escolar_noite
):
    assert dia_calendario_noturno.pk is not None
    assert dia_calendario_noturno.dia_letivo is False
    assert dia_calendario_noturno.escola == escola
    assert dia_calendario_noturno.periodo_escolar == periodo_escolar_noite
    assert dia_calendario_noturno.data == datetime.date(2024, 5, 15)


def test_dia_calendario_sem_perido(dia_calendario_diurno, escola):
    assert dia_calendario_diurno.pk is not None
    assert dia_calendario_diurno.dia_letivo is True
    assert dia_calendario_diurno.escola == escola
    assert dia_calendario_diurno.periodo_escolar is None
    assert dia_calendario_diurno.data == datetime.date(2024, 5, 15)


@pytest.mark.django_db
class TestEscolaQuantidadeAlunosPorCeiEmei:

    @pytest.mark.django_db
    def test_cemei_sem_alunos_nao_gera_keyerror(
        self, escola_cemei_sem_alunos, faixas_etarias_ativas
    ):
        """
        Este teste força a entrada no loop de períodos mesmo sem alunos matriculados.
        Sem o seu ajuste (usando .get() ou try/except), isso daria KeyError: 'INTEGRAL'
        """
        from src.core.constants import PERIODOS_ESPECIAIS_CEMEI

        for nome_periodo in PERIODOS_ESPECIAIS_CEMEI:
            baker.make("PeriodoEscolar", nome=nome_periodo)

        resultado = escola_cemei_sem_alunos.quantidade_alunos_por_cei_emei(
            manha_e_tarde_sempre=True
        )

        assert resultado is not None
        assert len(resultado) > 0
        for item in resultado:
            assert item[TIPOS_UNIDADE_ESCOLAR.CEI.value] == []

    def test_cemei_com_alunos_retorna_dados_corretos(
        self, escola_cemei, faixas_etarias_ativas
    ):
        resultado = escola_cemei.quantidade_alunos_por_cei_emei()

        assert resultado is not None
        assert isinstance(resultado, list)
        assert len(resultado) > 0

        primeiro_periodo = resultado[0]
        assert "nome" in primeiro_periodo
        assert TIPOS_UNIDADE_ESCOLAR.CEI.value in primeiro_periodo
        assert TIPOS_UNIDADE_ESCOLAR.EMEI.value in primeiro_periodo
