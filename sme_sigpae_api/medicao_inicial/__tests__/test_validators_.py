import datetime

import pytest
from freezegun.api import freeze_time

from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.medicao_inicial.validators import (
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


def test_get_lista_dias_letivos_diurno(solicitacao_dias_letivos_escola, escola):
    dias_letivos = get_lista_dias_letivos(
        solicitacao_dias_letivos_escola, escola, periodo_escolar=None
    )
    assert len(dias_letivos) == 20
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
        "20",
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
    assert len(dias_letivos) == 18
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
        "20",
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
):
    periodos = obter_periodos_corretos(solicitacao_dias_letivos_escola, escola)
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
        "20",
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
        "20",
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]


def test_obter_periodos_corretos_sem_periodo_notuno(
    solicitacao_dias_letivos_escola, escola, vinculo_alimentacao_integral
):
    periodos = obter_periodos_corretos(solicitacao_dias_letivos_escola, escola)
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
        "20",
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]

    assert "noite" in periodos
    assert periodos["noite"] == periodos["default"]
