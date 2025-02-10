import datetime
import os
from pathlib import Path

import pytest
from freezegun import freeze_time
from openpyxl import load_workbook

from sme_sigpae_api.escola.models import Escola, LogAlunosMatriculadosPeriodoEscola

from ..utils import (
    EscolaSimplissimaPagination,
    cria_arquivo_excel,
    faixa_to_string,
    meses_to_mes_e_ano_string,
    remove_acentos,
    string_to_faixa,
    string_to_meses,
    update_datetime_LogAlunosMatriculadosPeriodoEscola,
)

pytestmark = pytest.mark.django_db


def test_meses_para_mes_e_ano_string():
    assert meses_to_mes_e_ano_string(0) == "00 meses"
    assert meses_to_mes_e_ano_string(1) == "01 mês"
    assert meses_to_mes_e_ano_string(2) == "02 meses"
    assert meses_to_mes_e_ano_string(3) == "03 meses"
    assert meses_to_mes_e_ano_string(11) == "11 meses"
    assert meses_to_mes_e_ano_string(12) == "01 ano"
    assert meses_to_mes_e_ano_string(13) == "01 ano e 01 mês"
    assert meses_to_mes_e_ano_string(14) == "01 ano e 02 meses"
    assert meses_to_mes_e_ano_string(15) == "01 ano e 03 meses"
    assert meses_to_mes_e_ano_string(23) == "01 ano e 11 meses"
    assert meses_to_mes_e_ano_string(24) == "02 anos"
    assert meses_to_mes_e_ano_string(25) == "02 anos e 01 mês"
    assert meses_to_mes_e_ano_string(26) == "02 anos e 02 meses"
    assert meses_to_mes_e_ano_string(27) == "02 anos e 03 meses"
    assert meses_to_mes_e_ano_string(35) == "02 anos e 11 meses"
    assert meses_to_mes_e_ano_string(36) == "03 anos"


def test_faixa_to_string():
    assert faixa_to_string(0, 0) == "0 meses a 11 meses"
    assert faixa_to_string(12, 13) == "01 ano"

    assert faixa_to_string(2, 62) == "02 a 05 anos e 01 mês"
    assert faixa_to_string(24, 62) == "02 anos a 05 anos e 01 mês"

    assert faixa_to_string(36, 72) == "03 anos a 06 anos"

    assert faixa_to_string(16, 51) == "01 ano e 04 meses a 04 anos e 02 meses"


def test_string_to_faixa():
    assert string_to_faixa("0 meses a 11 meses") == (0, 12)
    assert string_to_faixa("1") == (1, 2)

    assert string_to_faixa("3 a 5") == (3, 6)
    assert string_to_faixa("3 anos  a 5 anos ") == (36, 61)

    assert string_to_faixa("02 a 05 ") == (2, 6)
    assert string_to_faixa("2 a 5 anos e 1 mês") == (2, 62)
    assert string_to_faixa("02 anos a 05 anos e 01 mês") == (24, 62)


def test_string_to_meses():
    assert string_to_meses("1 ano") == 12
    assert string_to_meses("2 ano") == 24
    assert string_to_meses("3 ano") == 36
    assert string_to_meses("4 ano") == 48
    assert string_to_meses("5 ano") == 60
    assert string_to_meses("6 ano") == 72

    assert string_to_meses("1") == 1

    assert string_to_meses("1 mês") == 1
    assert string_to_meses("2 meses") == 2
    assert string_to_meses("3 meses") == 3
    assert string_to_meses("7 meses") == 7
    assert string_to_meses("11 meses") == 11


def test_remove_acentos():
    assert remove_acentos("àáâãäå") == "aaaaaa"
    assert remove_acentos("èéêë") == "eeee"
    assert remove_acentos("ìíîï") == "iiii"
    assert remove_acentos("abc") == "abc"
    assert remove_acentos("") == ""
    assert remove_acentos("Olá, você está bem?") == "Ola, voce esta bem?"
    assert remove_acentos("voô") == "voô"


@freeze_time("2025-02-05")
def test_update_datetime_log_alunos_matriculados_periodo_escola(
    update_log_alunos_matriculados,
):
    assert LogAlunosMatriculadosPeriodoEscola.objects.all().count() == 2
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            criado_em__date=datetime.date(2025, 2, 5)
        ).count()
        == 1
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            criado_em__date=datetime.date(2025, 2, 4)
        ).count()
        == 0
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            criado_em__date=datetime.date(2025, 2, 1)
        ).count()
        == 1
    )

    update_datetime_LogAlunosMatriculadosPeriodoEscola()
    assert LogAlunosMatriculadosPeriodoEscola.objects.all().count() == 2
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            criado_em__date=datetime.date(2025, 2, 5)
        ).count()
        == 0
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            criado_em__date=datetime.date(2025, 2, 4)
        ).count()
        == 1
    )
    assert (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            criado_em__date=datetime.date(2025, 2, 1)
        ).count()
        == 1
    )


def test_cria_arquivo_excel():
    dados = [
        {"Nome": "Alice", "Idade": "25", "Cidade": "São Paulo"},
        {"Nome": "Bob", "Idade": "30", "Cidade": "Rio de Janeiro"},
    ]
    caminho_arquivo = Path("/tmp/teste.xlsx")
    cria_arquivo_excel(caminho_arquivo, dados)
    assert caminho_arquivo.exists(), "O arquivo Excel não foi criado."

    wb = load_workbook(caminho_arquivo)
    ws = wb.active

    assert [cell.value for cell in ws[1]] == list(dados[0].keys())

    for idx, row in enumerate(dados, start=2):
        assert [cell.value for cell in ws[idx]] == list(row.values())

    if os.path.exists(caminho_arquivo):
        os.remove(caminho_arquivo)
