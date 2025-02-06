import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest
from openpyxl import Workbook

from sme_sigpae_api.escola.models import (
    Escola,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
)
from sme_sigpae_api.escola.utils_escola import (
    PATH,
    ajustes_no_arquivo,
    atualiza_codigo_codae_das_escolas,
    create_tempfile,
    dict_codigos_escolas,
    escreve_escolas_json,
    gera_dict_codigo_aluno_por_codigo_escola,
    gera_dict_codigos_escolas,
    get_codigo_eol_aluno,
    get_codigo_eol_escola,
    get_escolas,
    get_escolas_unicas,
    grava_codescola_nao_existentes,
)

pytestmark = pytest.mark.django_db


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


@pytest.mark.parametrize("valor", ["12345", "67890"])
def test_grava_codescola_nao_existentes(valor):
    caminho_do_arquivo = Path(f"{PATH}/codescola_nao_existentes.txt")
    grava_codescola_nao_existentes(valor)
    assert caminho_do_arquivo.exists()
    with open(caminho_do_arquivo, "r") as f:
        linhas = f.readlines()
    assert f"{valor}\n" in linhas

    if os.path.exists(caminho_do_arquivo):
        os.remove(caminho_do_arquivo)


def test_gera_dict_codigo_aluno_por_codigo_escola(variaveis_globais_escola):
    items = [
        {"CodEscola": "1001", "CodEOLAluno": "20001"},
        {"CodEscola": "1002", "CodEOLAluno": "20002"},
    ]
    gera_dict_codigo_aluno_por_codigo_escola(items)
    esperado = {"0020001": "123456789", "0020002": "987654321"}
    assert esperado.items() <= variaveis_globais_escola[1].items()


def test_gera_dict_codigo_aluno_por_codigo_escola_exception():
    items = [
        {"CodEscola": "1001", "CodEOLAluno": "20001"},
        {"CodEscola": "1002", "CodEOLAluno": "20002"},
        {"CodEscola": "9999", "CodEOLAluno": "20003"},
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


def test_escreve_escolas_json():
    caminho_do_arquivo = Path(f"/tmp/{uuid.uuid4()}.json")
    escolas_data = {
        "escolas": [{"id": 1, "nome": "Escola A"}, {"id": 2, "nome": "Escola B"}]
    }
    texto = json.dumps(escolas_data, ensure_ascii=False)

    escreve_escolas_json(caminho_do_arquivo, texto)
    assert caminho_do_arquivo.exists()
    with open(caminho_do_arquivo, "r") as f:
        conteudo = f.read()
    assert conteudo == texto

    if os.path.exists(caminho_do_arquivo):
        os.remove(caminho_do_arquivo)


def test_ajustes_no_arquivo(tmp_path):
    caminho_do_arquivo = Path(f"/tmp/{uuid.uuid4()}.json")
    conteudo_inicial = (
        """{'nome': "Escola A"}\n{'codigo_EOL': '454353464'}\n{'id': '6'}"""
    )

    with open(caminho_do_arquivo, "w") as f:
        f.write(conteudo_inicial)

    ajustes_no_arquivo(caminho_do_arquivo)
    with open(caminho_do_arquivo, "r") as f:
        conteudo_modificado = f.readlines()

    conteudo_esperado = [
        '{"nome": "Escola A"}\n',
        '{"codigo_EOL": "454353464"},\n',
        '{"id": "6"}',
    ]
    assert conteudo_modificado == conteudo_esperado
    if os.path.exists(caminho_do_arquivo):
        os.remove(caminho_do_arquivo)


def test_get_informacoes_escola_turma_aluno():
    pass


def test_create_tempfile():
    arquivo = create_tempfile()
    assert arquivo.startswith("/tmp/")
    assert arquivo.endswith(".json")


def test_main():
    pass


def create_excel_file(data):
    """Cria um arquivo Excel temporário com os dados fornecidos."""
    wb = Workbook()
    ws = wb.active

    for row in data:
        ws.append(row)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(temp_file.name)
    return temp_file.name


def create_excel_file(file_path, data):
    wb = Workbook()
    ws = wb.active
    ws.append(list(data[0].keys()))
    for row in data:
        ws.append(list(row.values()))
    wb.save(file_path)


def test_get_escolas(variaveis_globais_escola):
    with tempfile.TemporaryDirectory() as temp_dir:
        arquivo_path = Path(temp_dir) / "escolas.xlsx"
        arquivo_codigos_escolas_path = Path(temp_dir) / "codigos_escolas.xlsx"
        tempfile_output_path = Path(temp_dir) / "output.json"
        create_excel_file(
            arquivo_path,
            [
                {"CodEscola": "12345", "CodEOLAluno": "1111"},
                {"CodEscola": "67890", "CodEOLAluno": "2222"},
            ],
        )
        create_excel_file(
            arquivo_codigos_escolas_path,
            [
                {"CÓDIGO UNIDADE": "12345", "CODIGO EOL": "54321"},
                {"CÓDIGO UNIDADE": "67890", "CODIGO EOL": "98765"},
            ],
        )
        resultado = get_escolas(
            arquivo_path,
            arquivo_codigos_escolas_path,
            tempfile_output_path,
            in_memory=False,
        )
        assert Path(resultado).exists()
        with open(resultado, "r") as f:
            conteudo = f.read()
            assert "}" in conteudo


def test_atualiza_codigo_codae_das_escolas(planilha_de_para_eol_codae):
    with tempfile.TemporaryDirectory() as temp_dir:
        arquivo_path = Path(temp_dir) / "escolas.xlsx"

        # Criar arquivo Excel de teste
        create_excel_file(
            arquivo_path,
            [
                {"codigo_eol": 123456, "codigo_unidade": 54321},
                {"codigo_eol": 789012, "codigo_unidade": 98765},
            ],
        )

        # Criar escolas no banco de dados
        escola1 = Escola.objects.create(codigo_eol="123456", codigo_codae="00000")
        escola2 = Escola.objects.create(codigo_eol="789012", codigo_codae="00000")

        # Criar planilha no banco de dados
        planilha = PlanilhaEscolaDeParaCodigoEolCodigoCoade.objects.create(
            id=1, codigos_codae_vinculados=False
        )

        # Executar a função
        atualiza_codigo_codae_das_escolas(arquivo_path, planilha.id)

        # Recarregar objetos do banco
        escola1.refresh_from_db()
        escola2.refresh_from_db()
        planilha.refresh_from_db()

        # Verificar se os códigos foram atualizados corretamente
        assert (
            escola1.codigo_codae == "54321"
        ), "Código CODAE da escola1 não foi atualizado corretamente."
        assert (
            escola2.codigo_codae == "98765"
        ), "Código CODAE da escola2 não foi atualizado corretamente."

        # Verificar se a flag foi atualizada na planilha
        assert (
            planilha.codigos_codae_vinculados
        ), "A flag de codigos_codae_vinculados não foi atualizada."


def test_atualiza_tipo_gestao_das_escolas():
    pass
