import json
import os

from ..helper import (
    calcula_total_alunos_por_escola,
    calcula_total_alunos_por_escola_por_periodo,
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def test_calcula_total_alunos_por_escola(escola_total_params):
    cod_eol, total_esperado = escola_total_params
    with open(f"{CURRENT_DIR}/total_alunos.json") as f:
        request_data = json.loads(f.read())

    json_data = calcula_total_alunos_por_escola(request_data)
    assert json_data[cod_eol] == total_esperado


def test_calcula_total_alunos_por_escola_por_periodo(escola_total_por_periodo_params):
    cod_eol, resultado_esperado = escola_total_por_periodo_params
    with open(f"{CURRENT_DIR}/total_alunos.json") as f:
        request_data = json.loads(f.read())

    json_data = calcula_total_alunos_por_escola_por_periodo(request_data)
    assert json_data[cod_eol] == resultado_esperado
