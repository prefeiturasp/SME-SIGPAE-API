import datetime

import pytest
from freezegun.api import freeze_time
from model_bakery import baker

from src.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.escola.models import TipoTurma
from src.medicao_inicial.validators import (
    _validate_solicitacoes_programas_e_projetos_emei_cemei,
    get_lista_dias_letivos,
    obter_periodos_corretos,
    valida_medicoes_inexistentes_cei,
    valida_medicoes_inexistentes_emebs,
    valida_medicoes_inexistentes_escola_sem_alunos_regulares,
    validate_lancamento_alimentacoes_inclusoes_escola_sem_alunos_regulares,
    validate_lancamento_alimentacoes_medicao_cei,
    validate_lancamento_alimentacoes_medicao_emebs,
    validate_lancamento_dietas_inclusoes_escola_sem_alunos_regulares,
    validate_lancamento_inclusoes_cei,
    validate_lancamento_inclusoes_dietas_emef_emebs,
    validate_medicao_cemei,
    validate_solicitacoes_etec,
    validate_solicitacoes_programas_e_projetos,
    validate_solicitacoes_programas_e_projetos_emebs,
)

pytestmark = pytest.mark.django_db


@freeze_time("2025-05-05")
def test_valida_medicoes_inexistentes_cei(
    solicitacao_medicao_inicial_cei,
    log_aluno_integral_cei,
    log_alunos_matriculados_integral_cei,
):
    lista_erros = []
    lista_erros = valida_medicoes_inexistentes_cei(
        solicitacao_medicao_inicial_cei, lista_erros
    )
    assert len(lista_erros) == 2
    assert (
        next(
            (erro for erro in lista_erros if erro["periodo_escolar"] == "PARCIAL"), None
        )
        is not None
    )


def test_validate_lancamento_alimentacoes_medicao_cei(solicitacao_medicao_inicial_cei):
    lista_erros = []
    lista_erros = validate_lancamento_alimentacoes_medicao_cei(
        solicitacao_medicao_inicial_cei, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_inclusoes_cei(solicitacao_medicao_inicial_cei):
    lista_erros = []
    lista_erros = validate_lancamento_inclusoes_cei(
        solicitacao_medicao_inicial_cei, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_inclusoes_dietas_emef(
    solicitacao_medicao_inicial_teste_salvar_logs,
):
    lista_erros = []
    lista_erros = validate_lancamento_inclusoes_dietas_emef_emebs(
        solicitacao_medicao_inicial_teste_salvar_logs, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_solicitacoes_etec(
    solicitacao_medicao_inicial_teste_salvar_logs,
):
    lista_erros = []
    lista_erros = validate_solicitacoes_etec(
        solicitacao_medicao_inicial_teste_salvar_logs, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_solicitacoes_programas_e_projetos(
    solicitacao_medicao_inicial_teste_salvar_logs,
):
    lista_erros = []
    lista_erros = validate_solicitacoes_programas_e_projetos(
        solicitacao_medicao_inicial_teste_salvar_logs, lista_erros
    )
    assert len(lista_erros) == 0


def test_valida_medicoes_inexistentes_escola_sem_alunos_regulares(
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
):
    lista_erros = []
    lista_erros = valida_medicoes_inexistentes_escola_sem_alunos_regulares(
        solicitacao_medicao_inicial_varios_valores_ceu_gestao, lista_erros
    )
    assert len(lista_erros) == 1
    assert (
        next((erro for erro in lista_erros if erro["periodo_escolar"] == "TARDE"), None)
        is not None
    )


def test_validate_lancamento_alimentacoes_inclusoes_escola_sem_alunos_regulares(
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
):
    lista_erros = []
    lista_erros = (
        validate_lancamento_alimentacoes_inclusoes_escola_sem_alunos_regulares(
            solicitacao_medicao_inicial_varios_valores_ceu_gestao, lista_erros
        )
    )
    assert len(lista_erros) == 1
    assert (
        next((erro for erro in lista_erros if erro["periodo_escolar"] == "TARDE"), None)
        is not None
    )


def test_validate_medicao_cei_cemei_periodo_integral_dia_letivo_preenchido(
    escola_cemei,
    solicitacao_medicao_inicial_cemei_simples,
    make_dia_letivo,
    make_periodo_escolar,
    make_medicao,
    make_log_matriculados_faixa_etaria_dia,
    make_valor_medicao_faixa_etaria,
):
    # arrange
    dia = 1
    periodo_integral = make_periodo_escolar("INTEGRAL")
    medicao = make_medicao(solicitacao_medicao_inicial_cemei_simples, periodo_integral)
    make_dia_letivo(
        dia,
        int(solicitacao_medicao_inicial_cemei_simples.mes),
        int(solicitacao_medicao_inicial_cemei_simples.ano),
        escola_cemei,
    )
    make_log_matriculados_faixa_etaria_dia(
        dia, escola_cemei, solicitacao_medicao_inicial_cemei_simples, periodo_integral
    )
    make_valor_medicao_faixa_etaria(medicao, "1", dia)

    # act
    lista_erros = validate_medicao_cemei(solicitacao_medicao_inicial_cemei_simples)

    # assert
    assert len(lista_erros) == 0


def test_validate_medicao_cei_cemei_periodo_integral_dia_letivo_nao_preenchido(
    escola_cemei,
    solicitacao_medicao_inicial_cemei_simples,
    make_dia_letivo,
    make_periodo_escolar,
    make_medicao,
    make_log_matriculados_faixa_etaria_dia,
    categoria_medicao,
):
    # arrange
    dia = 3
    periodo_integral = make_periodo_escolar("INTEGRAL")
    make_medicao(solicitacao_medicao_inicial_cemei_simples, periodo_integral)
    make_dia_letivo(
        dia,
        int(solicitacao_medicao_inicial_cemei_simples.mes),
        int(solicitacao_medicao_inicial_cemei_simples.ano),
        escola_cemei,
    )
    make_log_matriculados_faixa_etaria_dia(
        dia, escola_cemei, solicitacao_medicao_inicial_cemei_simples, periodo_integral
    )

    # act
    lista_erros = validate_medicao_cemei(solicitacao_medicao_inicial_cemei_simples)

    # assert
    assert len(lista_erros) == 1


def test_valida_medicoes_inexistentes_emebs(
    solicitacao_medicao_inicial_varios_valores_emebs,
):
    lista_erros = []
    lista_erros = valida_medicoes_inexistentes_emebs(
        solicitacao_medicao_inicial_varios_valores_emebs, lista_erros
    )
    assert len(lista_erros) == 0


def test_validate_lancamento_alimentacoes_medicao_emebs(
    solicitacao_medicao_inicial_varios_valores_emebs,
):
    lista_erros = []
    lista_erros = validate_lancamento_alimentacoes_medicao_emebs(
        solicitacao_medicao_inicial_varios_valores_emebs, lista_erros
    )
    assert len(lista_erros) == 0


def test_get_lista_dias_letivos_diurno(
    solicitacao_dias_letivos_escola, escola, periodo_escolar_integral
):
    dias_letivos = get_lista_dias_letivos(
        solicitacao_dias_letivos_escola,
        escola,
        periodo_escolar=periodo_escolar_integral,
    )
    assert len(dias_letivos) == 19
    assert dias_letivos == [
        "03",
        "04",
        "05",
        "06",
        "07",
        "10",
        "11",
        "12",
        "13",
        "14",
        "17",
        "18",
        "19",
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]


def test_get_lista_dias_letivos_noturno(
    solicitacao_dias_letivos_escola, escola, periodo_escolar_noite
):
    dias_letivos = get_lista_dias_letivos(
        solicitacao_dias_letivos_escola, escola, periodo_escolar=periodo_escolar_noite
    )
    assert len(dias_letivos) == 17
    assert dias_letivos == [
        "03",
        "04",
        "05",
        "06",
        "07",
        "10",
        "13",
        "14",
        "17",
        "18",
        "19",
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]


def test_obter_periodos_corretos_com_periodo_notuno(
    solicitacao_dias_letivos_escola,
    escola,
    vinculo_alimentacao_noturno,
    vinculo_alimentacao_integral,
    periodo_escolar_integral,
):
    periodos = obter_periodos_corretos(
        solicitacao_dias_letivos_escola, escola, periodo_escolar_integral
    )
    assert isinstance(periodos, dict)
    assert len(periodos) == 2

    assert "default" in periodos
    assert periodos["default"] == [
        "03",
        "04",
        "05",
        "06",
        "07",
        "10",
        "11",
        "12",
        "13",
        "14",
        "17",
        "18",
        "19",
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]

    assert "noite" in periodos
    assert periodos["noite"] == [
        "03",
        "04",
        "05",
        "06",
        "07",
        "10",
        "13",
        "14",
        "17",
        "18",
        "19",
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]


def test_obter_periodos_corretos_sem_periodo_notuno(
    solicitacao_dias_letivos_escola,
    escola,
    vinculo_alimentacao_integral,
    periodo_escolar_integral,
):
    periodos = obter_periodos_corretos(
        solicitacao_dias_letivos_escola, escola, periodo_escolar_integral
    )
    assert isinstance(periodos, dict)
    assert len(periodos) == 2

    assert "default" in periodos
    assert periodos["default"] == [
        "03",
        "04",
        "05",
        "06",
        "07",
        "10",
        "11",
        "12",
        "13",
        "14",
        "17",
        "18",
        "19",
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]

    assert "noite" in periodos
    assert periodos["noite"] == periodos["default"]


def _make_solicitacao(escola, mes="11", ano="2025"):
    return baker.make("SolicitacaoMedicaoInicial", mes=mes, ano=ano, escola=escola)


def _make_dia_letivo(escola, dia, mes=11, ano=2025, periodo_escolar=None):
    baker.make(
        "DiaCalendario",
        escola=escola,
        periodo_escolar=periodo_escolar,
        data=datetime.date(ano, mes, dia),
        dia_letivo=True,
    )


def _make_log(
    escola, periodo_escolar, dia, mes=11, ano=2025, quantidade=25, tipo_turma=None
):
    log = baker.make(
        "LogAlunosMatriculadosPeriodoEscola",
        escola=escola,
        periodo_escolar=periodo_escolar,
        tipo_turma=tipo_turma or TipoTurma.REGULAR.name,
        quantidade_alunos=quantidade,
    )
    log.criado_em = datetime.datetime(ano, mes, dia, 12, 0)
    log.save()
    return log


def test_get_lista_dias_letivos_dia_com_log_valido_incluido(
    escola, periodo_escolar_noite
):
    """Dia letivo com log REGULAR, quantidade > 0 e periodo_escolar preenchido é retornado."""
    solicitacao = _make_solicitacao(escola)
    _make_dia_letivo(escola, 3, periodo_escolar=periodo_escolar_noite)
    _make_log(escola, periodo_escolar_noite, 3)

    dias = get_lista_dias_letivos(solicitacao, escola, periodo_escolar_noite)

    assert "03" in dias


def test_get_lista_dias_letivos_dia_sem_log_excluido(escola):
    """Dia letivo sem log correspondente não é retornado."""
    solicitacao = _make_solicitacao(escola)
    _make_dia_letivo(escola, 3)

    dias = get_lista_dias_letivos(solicitacao, escola)

    assert "03" not in dias


def test_get_lista_dias_letivos_log_quantidade_zero_excluido(
    escola, periodo_escolar_noite
):
    """Dia letivo com log de quantidade_alunos=0 não é retornado."""
    solicitacao = _make_solicitacao(escola)
    _make_dia_letivo(escola, 3)
    _make_log(escola, periodo_escolar_noite, 3, quantidade=0)

    dias = get_lista_dias_letivos(solicitacao, escola)

    assert "03" not in dias


def test_get_lista_dias_letivos_log_tipo_turma_nao_regular_excluido(
    escola, periodo_escolar_noite
):
    """Dia letivo com log de tipo_turma != REGULAR não é retornado."""
    solicitacao = _make_solicitacao(escola)
    _make_dia_letivo(escola, 3)
    _make_log(escola, periodo_escolar_noite, 3, tipo_turma="PROGRAMAS")

    dias = get_lista_dias_letivos(solicitacao, escola)

    assert "03" not in dias


def test_get_lista_dias_letivos_log_de_outra_escola_excluido(
    escola, periodo_escolar_noite
):
    """Dia letivo com log de outra escola não é retornado."""
    outra_escola = baker.make("Escola")
    solicitacao = _make_solicitacao(escola)
    _make_dia_letivo(escola, 3)
    _make_log(outra_escola, periodo_escolar_noite, 3)

    dias = get_lista_dias_letivos(solicitacao, escola)

    assert "03" not in dias


def test_get_lista_dias_letivos_log_de_outro_mes_excluido(
    escola, periodo_escolar_noite
):
    """Log do mesmo dia mas de mês diferente não conta."""
    solicitacao = _make_solicitacao(escola)
    _make_dia_letivo(escola, 3)
    # Log existe para Outubro, para Novembro não
    _make_log(escola, periodo_escolar_noite, 3, mes=10)

    dias = get_lista_dias_letivos(solicitacao, escola)

    assert "03" not in dias
