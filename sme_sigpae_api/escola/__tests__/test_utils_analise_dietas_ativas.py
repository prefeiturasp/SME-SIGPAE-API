import json
import tempfile

import pytest
from openpyxl import load_workbook

from sme_sigpae_api.escola.utils_analise_dietas_ativas import (
    dict_codigos_escolas,
    escreve_xlsx,
    escreve_xlsx_primeira_aba,
    gera_dict_codigo_aluno_por_codigo_escola,
    gera_dict_codigos_escolas,
    get_codigo_eol_aluno,
    get_codigo_eol_escola,
    get_escolas_json,
    get_escolas_unicas,
    retorna_codigo_eol_escolas_nao_identificadas,
)


def test_get_codigo_eol_escola():
    assert get_codigo_eol_escola("123") == "000123"
    assert get_codigo_eol_escola(" 45 ") == "000045"
    assert get_codigo_eol_escola("123456") == "123456"
    assert get_codigo_eol_escola("1234567") == "1234567"
    assert get_codigo_eol_escola("") == "000000"


def test_get_codigo_eol_aluno():
    assert get_codigo_eol_aluno(1234) == "0001234"
    assert get_codigo_eol_aluno(" 789 ") == "0000789"
    assert get_codigo_eol_aluno("1234567") == "1234567"
    assert get_codigo_eol_aluno("12345678") == "12345678"
    assert get_codigo_eol_aluno("") == "0000000"


def test_gera_dict_codigos_escolas():
    items_codigos_escolas = [
        {"CÓDIGO UNIDADE": 123, "CODIGO EOL": 456},
        {"CÓDIGO UNIDADE": 789, "CODIGO EOL": 101112},
        {"CÓDIGO UNIDADE": 345, "CODIGO EOL": 6789},
    ]
    dict_codigos_escolas.clear()

    gera_dict_codigos_escolas(items_codigos_escolas)
    assert dict_codigos_escolas == {
        "123": "456",
        "789": "101112",
        "345": "6789",
    }


def test_gera_dict_codigo_aluno_por_codigo_escola_exception():
    items = [
        {"CodEscola": "101", "CodEOLAluno": "55"},
        {"CodEscola": "102", "CodEOLAluno": "999"},
    ]
    with pytest.raises(Exception):
        gera_dict_codigo_aluno_por_codigo_escola(items)


def test_get_escolas_unicas():
    items = [
        {"CodEscola": "101", "CodEOLAluno": "55"},
        {"CodEscola": "102", "CodEOLAluno": "997"},
        {"CodEscola": "102", "CodEOLAluno": "998"},
        {"CodEscola": "102", "CodEOLAluno": "999"},
    ]

    escolas = get_escolas_unicas(items)
    assert isinstance(escolas, set)
    assert len(escolas) == 2


def test_escreve_xlsx():
    codigo = set([111, 215, 433])
    output, nome_excel = escreve_xlsx(codigo)
    assert isinstance(nome_excel, str)
    assert nome_excel.lower().endswith(".xlsx")
    assert len(nome_excel.strip()) > 0  # Verifica se não é vazio

    workbook = load_workbook(output)
    nome_aba = "Código EOL das Escolas não identificadas no SIGPAE"
    assert nome_aba in workbook.sheetnames

    worksheet = workbook[nome_aba]
    rows = list(worksheet.iter_rows(values_only=True))
    assert rows[0] == ("codigo_eol_escola",)
    assert rows[1] == ("433",)
    assert rows[2] == ("215",)
    assert rows[3] == ("111",)


def test_escreve_xlsx_primeira_aba(resultado, arquivo_saida):
    escreve_xlsx_primeira_aba(resultado, arquivo_saida)


def test_get_escolas_json():
    escolas_data = {
        "escolas": [{"id": 1, "nome": "Escola A"}, {"id": 2, "nome": "Escola B"}]
    }

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".json", delete=True
    ) as temp_file:
        json.dump(escolas_data, temp_file)
        temp_file.seek(0)
        result = get_escolas_json(temp_file.name)
        assert result == escolas_data


def test_retorna_codigo_eol_escolas_nao_identificadas_exception():
    items_codigos_escolas = [
        {"CodEscola": "123", "CODIGO EOL": 456},
        {"CodEscola": "789", "CODIGO EOL": 101112},
        {"CodEscola": "345", "CODIGO EOL": 6789},
    ]

    with pytest.raises(Exception):
        retorna_codigo_eol_escolas_nao_identificadas(items_codigos_escolas)
