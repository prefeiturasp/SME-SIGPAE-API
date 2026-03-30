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
        "21",
        "24",
        "25",
        "26",
        "27",
        "28",
    ]

    assert "noite" in periodos
    assert periodos["noite"] == periodos["default"]


def test_validate_solicitacoes_programas_e_projetos_periodos_zero_alimentacao_exige_observacao(
    solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao
):
    solicitacao = solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao
    lista_erros = []
    lista_erros = validate_solicitacoes_programas_e_projetos(solicitacao, lista_erros)
    assert len(lista_erros) == 1
    assert any(
        "Avaliar lançamentos de dias sem frequencia nos demais períodos." in erro["erro"] and erro["periodo_escolar"] == "Programas e Projetos"
        for erro in lista_erros
    )

def test_validate_solicitacoes_programas_e_projetos_periodos_zero_dietas_exige_observacao(
    solicitacao_medicao_finaliza_programas_projetos_zerados_dietas
):
    solicitacao = solicitacao_medicao_finaliza_programas_projetos_zerados_dietas
    lista_erros = []
    lista_erros = validate_solicitacoes_programas_e_projetos(solicitacao, lista_erros)

    assert len(lista_erros) == 1
    assert any(
        "Avaliar lançamentos de dias sem frequencia nos demais períodos." in erro["erro"]
        and erro["periodo_escolar"] == "Programas e Projetos"
        for erro in lista_erros
    )

def test_validate_solicitacoes_programas_e_projetos_periodos_zero_alimentacao_com_observacao_ok(
    solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao, categoria_medicao
):
    solicitacao = solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao
    medicao_programas = solicitacao.get_medicao_programas_e_projetos

    program_valor = medicao_programas.valores_medicao.filter(
        nome_campo="frequencia", dia="14", categoria_medicao=categoria_medicao
    ).first()
    medicao_programas.valores_medicao.create(
        nome_campo="observacoes",
        dia="14",
        categoria_medicao=program_valor.categoria_medicao,
        valor="justificativa",
    )

    lista_erros = []
    lista_erros = validate_solicitacoes_programas_e_projetos(solicitacao, lista_erros)

    assert all(
        erro["periodo_escolar"] != "Programas e Projetos" for erro in lista_erros
    )
    
def test_validate_solicitacoes_programas_e_projetos_periodos_zero_dieta_com_observacao_ok(
    solicitacao_medicao_finaliza_programas_projetos_zerados_dietas, categoria_medicao_dieta_a
):
    solicitacao = solicitacao_medicao_finaliza_programas_projetos_zerados_dietas
    medicao_programas = solicitacao.get_medicao_programas_e_projetos

    program_valor = medicao_programas.valores_medicao.filter(
        nome_campo="frequencia", dia="14", categoria_medicao=categoria_medicao_dieta_a
    ).first()
    medicao_programas.valores_medicao.create(
        nome_campo="observacoes",
        dia="14",
        categoria_medicao=program_valor.categoria_medicao,
        valor="justificativa",
    )

    lista_erros = []
    lista_erros = validate_solicitacoes_programas_e_projetos(solicitacao, lista_erros)

    assert all(
        erro["periodo_escolar"] != "Programas e Projetos" for erro in lista_erros
    )

def test_validate_solicitacoes_programas_e_projetos_periodos_altera_periodo_tarde_alimentacao(
    solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao, periodo_escolar_tarde, categoria_medicao
):
    solicitacao = solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao
    medicao_tarde = solicitacao.medicoes.filter(periodo_escolar=periodo_escolar_tarde).first()
    valor = medicao_tarde.valores_medicao.get(
        nome_campo="frequencia", dia="14", categoria_medicao=categoria_medicao
    )
    valor.valor = "40"
    valor.save()
    lista_erros = []
    lista_erros = validate_solicitacoes_programas_e_projetos(solicitacao, lista_erros)
    assert all(
        erro["periodo_escolar"] != "Programas e Projetos" for erro in lista_erros
    )
    
def test_validate_solicitacoes_programas_e_projetos_periodos_altera_periodo_tarde_dieta(
    solicitacao_medicao_finaliza_programas_projetos_zerados_dietas, periodo_escolar_tarde, categoria_medicao_dieta_a
):
    solicitacao = solicitacao_medicao_finaliza_programas_projetos_zerados_dietas
    medicao_tarde = solicitacao.medicoes.filter(periodo_escolar=periodo_escolar_tarde).first()
    valor = medicao_tarde.valores_medicao.get(
        nome_campo="frequencia", dia="14", categoria_medicao=categoria_medicao_dieta_a
    )
    valor.valor = "3"
    valor.save()
    lista_erros = []
    lista_erros = validate_solicitacoes_programas_e_projetos(solicitacao, lista_erros)
    assert all(
        erro["periodo_escolar"] != "Programas e Projetos" for erro in lista_erros
    )