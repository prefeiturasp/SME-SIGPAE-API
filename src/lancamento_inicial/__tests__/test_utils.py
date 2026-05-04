from datetime import date

import pytest

from ..utils import (
    eh_feriado_ou_fds,
    matriculados_convencional_em_uma_data,
    mes_para_faixa,
)


def test_mes_para_faixa(faixas_de_data):
    mes, faixa_inicio, faixa_fim = faixas_de_data
    faixa = mes_para_faixa(mes)
    assert faixa[0] == faixa_inicio
    assert faixa[1] == faixa_fim


def test_eh_feriado_ou_fds():
    assert eh_feriado_ou_fds(date(2020, 10, 5)) is False
    assert eh_feriado_ou_fds(date(2020, 10, 6)) is False
    assert eh_feriado_ou_fds(date(2020, 10, 7)) is False
    assert eh_feriado_ou_fds(date(2020, 10, 8)) is False
    assert eh_feriado_ou_fds(date(2020, 10, 9)) is False
    assert eh_feriado_ou_fds(date(2020, 10, 10)) is True
    assert eh_feriado_ou_fds(date(2020, 10, 11)) is True
    assert eh_feriado_ou_fds(date(2020, 10, 12)) is True
    assert eh_feriado_ou_fds(date(2020, 10, 13)) is False
    assert eh_feriado_ou_fds(date(2020, 10, 14)) is False


@pytest.mark.django_db
def test_matriculados_convencional_em_uma_data_1(
    escola_periodo_escolar_com_quantidade_de_alunos, log_mudanca_qtde_1
):
    hoje = date.today()

    assert (
        matriculados_convencional_em_uma_data(
            escola_periodo_escolar_com_quantidade_de_alunos, hoje
        )
        == 123
    )


@pytest.mark.django_db
def test_matriculados_convencional_em_uma_data_2(
    escola_periodo_escolar_com_quantidade_de_alunos,
    log_mudanca_qtde_1,
    log_mudanca_qtde_2,
):
    data = date(2020, 12, 16)

    assert (
        matriculados_convencional_em_uma_data(
            escola_periodo_escolar_com_quantidade_de_alunos, data
        )
        == 121
    )


@pytest.mark.django_db
def test_matriculados_convencional_em_uma_data_3(
    escola_periodo_escolar_com_quantidade_de_alunos,
    log_mudanca_qtde_1,
    log_mudanca_qtde_2,
):
    data = date(2020, 12, 6)

    assert (
        matriculados_convencional_em_uma_data(
            escola_periodo_escolar_com_quantidade_de_alunos, data
        )
        == 119
    )
