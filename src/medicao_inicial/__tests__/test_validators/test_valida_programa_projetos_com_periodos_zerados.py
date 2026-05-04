import pytest

from src.medicao_inicial.validators import (
    _validate_solicitacoes_programas_e_projetos_emei_cemei,
    validate_solicitacoes_programas_e_projetos,
    validate_solicitacoes_programas_e_projetos_emebs,
)

pytestmark = pytest.mark.django_db

MSG_ERRO = "Avaliar lançamentos de dias sem frequencia nos demais períodos."
PERIODO = "Programas e Projetos"


def assert_erro(lista_erros):
    assert len(lista_erros) == 1
    assert any(
        MSG_ERRO in erro["erro"] and erro["periodo_escolar"] == PERIODO
        for erro in lista_erros
    )


def assert_sem_erro(lista_erros):
    assert all(erro["periodo_escolar"] != PERIODO for erro in lista_erros)


def add_observacao(medicao_programas, program_valor, extra=None):
    payload = {
        "nome_campo": "observacoes",
        "dia": "14",
        "categoria_medicao": program_valor.categoria_medicao,
        "valor": "justificativa",
    }
    if extra:
        payload.update(extra)

    medicao_programas.valores_medicao.create(**payload)


def alterar_valor(medicao, filtros, novo_valor):
    valor = medicao.valores_medicao.get(**filtros)
    valor.valor = novo_valor
    valor.save()


def run_validator(validator, solicitacao):
    if validator == _validate_solicitacoes_programas_e_projetos_emei_cemei:
        medicao_programas = solicitacao.get_medicao_programas_e_projetos
        return validator(solicitacao, [], medicao_programas)

    return validator(solicitacao, [])


@pytest.mark.parametrize(
    "validator, fixture_name",
    [
        (
            validate_solicitacoes_programas_e_projetos,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao",
        ),
        (
            validate_solicitacoes_programas_e_projetos,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_dietas",
        ),
        (
            validate_solicitacoes_programas_e_projetos_emebs,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_emebs_alimentacao",
        ),
        (
            validate_solicitacoes_programas_e_projetos_emebs,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_emebs_dietas",
        ),
        (
            _validate_solicitacoes_programas_e_projetos_emei_cemei,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_cemei_alimentacao",
        ),
        (
            _validate_solicitacoes_programas_e_projetos_emei_cemei,
            "solicitacao_medicao_finaliza_programas_projetos_cemei_zerados_dietas",
        ),
    ],
)
def test_exige_observacao(request, validator, fixture_name):
    solicitacao = request.getfixturevalue(fixture_name)

    erros = run_validator(validator, solicitacao)

    assert_erro(erros)


@pytest.mark.parametrize(
    "validator, fixture_name, categoria_fixture, extra",
    [
        (
            validate_solicitacoes_programas_e_projetos,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao",
            "categoria_medicao",
            None,
        ),
        (
            validate_solicitacoes_programas_e_projetos,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_dietas",
            "categoria_medicao_dieta_a",
            None,
        ),
        (
            validate_solicitacoes_programas_e_projetos_emebs,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_emebs_alimentacao",
            "categoria_medicao",
            {"infantil_ou_fundamental": "FUNDAMENTAL"},
        ),
        (
            validate_solicitacoes_programas_e_projetos_emebs,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_emebs_dietas",
            "categoria_medicao_dieta_a",
            {"infantil_ou_fundamental": "FUNDAMENTAL"},
        ),
        (
            _validate_solicitacoes_programas_e_projetos_emei_cemei,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_cemei_alimentacao",
            "categoria_medicao",
            None,
        ),
        (
            _validate_solicitacoes_programas_e_projetos_emei_cemei,
            "solicitacao_medicao_finaliza_programas_projetos_cemei_zerados_dietas",
            "categoria_medicao_dieta_a",
            None,
        ),
    ],
)
def test_com_observacao_ok(request, validator, fixture_name, categoria_fixture, extra):
    solicitacao = request.getfixturevalue(fixture_name)
    categoria = request.getfixturevalue(categoria_fixture)

    medicao_programas = solicitacao.get_medicao_programas_e_projetos

    filtros = {
        "nome_campo": "frequencia",
        "dia": "14",
        "categoria_medicao": categoria,
    }
    if extra:
        filtros.update(extra)

    program_valor = medicao_programas.valores_medicao.filter(**filtros).first()

    add_observacao(medicao_programas, program_valor, extra)

    erros = run_validator(validator, solicitacao)

    assert_sem_erro(erros)


@pytest.mark.parametrize(
    "validator, fixture_name, categoria_fixture, periodo_nome, extra",
    [
        (
            validate_solicitacoes_programas_e_projetos,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_alimentacao",
            "categoria_medicao",
            "TARDE",
            None,
        ),
        (
            validate_solicitacoes_programas_e_projetos,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_dietas",
            "categoria_medicao_dieta_a",
            "TARDE",
            None,
        ),
        (
            validate_solicitacoes_programas_e_projetos_emebs,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_emebs_alimentacao",
            "categoria_medicao",
            "TARDE",
            {"infantil_ou_fundamental": "FUNDAMENTAL"},
        ),
        (
            validate_solicitacoes_programas_e_projetos_emebs,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_emebs_dietas",
            "categoria_medicao_dieta_a",
            "TARDE",
            {"infantil_ou_fundamental": "FUNDAMENTAL"},
        ),
        (
            _validate_solicitacoes_programas_e_projetos_emei_cemei,
            "solicitacao_medicao_finaliza_programas_projetos_zerados_cemei_alimentacao",
            "categoria_medicao",
            "Infantil TARDE",
            None,
        ),
        (
            _validate_solicitacoes_programas_e_projetos_emei_cemei,
            "solicitacao_medicao_finaliza_programas_projetos_cemei_zerados_dietas",
            "categoria_medicao_dieta_a",
            "Infantil TARDE",
            None,
        ),
    ],
)
def test_com_um_periodo_nao_zero_ok(
    request, validator, fixture_name, categoria_fixture, periodo_nome, extra
):
    solicitacao = request.getfixturevalue(fixture_name)
    categoria = request.getfixturevalue(categoria_fixture)

    if solicitacao.escola.eh_cemei:
        medicao_tarde = solicitacao.medicoes.filter(grupo__nome=periodo_nome).first()
    else:
        medicao_tarde = solicitacao.medicoes.filter(
            periodo_escolar__nome=periodo_nome
        ).first()

    filtros = {
        "nome_campo": "frequencia",
        "dia": "14",
        "categoria_medicao": categoria,
    }
    if extra:
        filtros.update(extra)
    alterar_valor(medicao_tarde, filtros, "20")

    erros = run_validator(validator, solicitacao)

    assert_sem_erro(erros)
