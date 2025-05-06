import pytest
from freezegun.api import freeze_time

from sme_sigpae_api.medicao_inicial.validators import (
    valida_medicoes_inexistentes_cei,
    valida_medicoes_inexistentes_ceu_gestao,
    valida_medicoes_inexistentes_emebs,
    validate_lancamento_alimentacoes_inclusoes_ceu_gestao,
    validate_lancamento_alimentacoes_medicao_cei,
    validate_lancamento_alimentacoes_medicao_emebs,
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
    assert len(lista_erros) == 1
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


def test_valida_medicoes_inexistentes_ceu_gestao(
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
):
    lista_erros = []
    lista_erros = valida_medicoes_inexistentes_ceu_gestao(
        solicitacao_medicao_inicial_varios_valores_ceu_gestao, lista_erros
    )
    assert len(lista_erros) == 1
    assert (
        next((erro for erro in lista_erros if erro["periodo_escolar"] == "TARDE"), None)
        is not None
    )


def test_validate_lancamento_alimentacoes_inclusoes_ceu_gestao(
    solicitacao_medicao_inicial_varios_valores_ceu_gestao,
):
    lista_erros = []
    lista_erros = validate_lancamento_alimentacoes_inclusoes_ceu_gestao(
        solicitacao_medicao_inicial_varios_valores_ceu_gestao, lista_erros
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
    dia = 1
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
