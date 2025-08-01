import asyncio
import json
import os
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings

from sme_sigpae_api.dados_comuns.constants import StatusProcessamentoArquivo
from sme_sigpae_api.escola.utils import cria_arquivo_excel
from sme_sigpae_api.escola.utils_escola import (
    EOLException,
    ajustes_no_arquivo,
    atualiza_codigo_codae_das_escolas,
    atualiza_tipo_gestao_das_escolas,
    create_tempfile,
    dict_codigos_escolas,
    escreve_escolas_json,
    gera_dict_codigo_aluno_por_codigo_escola,
    gera_dict_codigos_escolas,
    get_codigo_eol_aluno,
    get_codigo_eol_escola,
    get_escolas,
    get_escolas_unicas,
    get_informacoes_escola_turma_aluno,
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
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    caminho_do_arquivo = os.path.join(
        settings.MEDIA_ROOT, "codescola_nao_existentes.txt"
    )
    grava_codescola_nao_existentes(valor)
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
    with pytest.raises(Exception, match="'1001'"):
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


def test_ajustes_no_arquivo():
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
    caminho_do_arquivo = Path(f"/tmp/{uuid.uuid4()}.json")
    codigo_eol = "123456"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": [{"turma": "A", "aluno": "João"}]}

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        resultado = asyncio.run(
            get_informacoes_escola_turma_aluno(caminho_do_arquivo, codigo_eol)
        )

    assert resultado == [{"turma": "A", "aluno": "João"}]
    with open(caminho_do_arquivo, "r") as f:
        conteudo = f.readlines()

    assert conteudo == ["\"123456\": [{'turma': 'A', 'aluno': 'João'}]\n"]

    if os.path.exists(caminho_do_arquivo):
        os.remove(caminho_do_arquivo)


def test_get_informacoes_escola_turma_aluno_vazio():
    caminho_do_arquivo = Path(f"/tmp/{uuid.uuid4()}.json")
    codigo_eol = "654321"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}  # Resposta vazia

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        with pytest.raises(
            EOLException, match=f"Resultados para o código: {codigo_eol} vazios"
        ):
            asyncio.run(
                get_informacoes_escola_turma_aluno(caminho_do_arquivo, codigo_eol)
            )

    if os.path.exists(caminho_do_arquivo):
        os.remove(caminho_do_arquivo)


def test_get_informacoes_escola_turma_aluno_api_erro():
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    caminho_do_arquivo = Path(f"/tmp/{uuid.uuid4()}.json")
    caminho_arquiro_erro_api = os.path.join(
        settings.MEDIA_ROOT, "codigo_eol_erro_da_api_eol.txt"
    )
    codigo_eol = "9999995991919"

    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        resultado = asyncio.run(
            get_informacoes_escola_turma_aluno(caminho_do_arquivo, codigo_eol)
        )

    assert resultado is None
    with open(caminho_arquiro_erro_api, "r") as f:
        conteudo = f.readlines()

    assert f"{codigo_eol}\n" in conteudo

    for caminho in [caminho_do_arquivo, caminho_arquiro_erro_api]:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_create_tempfile():
    arquivo = create_tempfile()
    assert arquivo.startswith("/tmp/")
    assert arquivo.endswith(".json")


def test_get_escolas(variaveis_globais_escola):
    caminho_arquivo_escola = Path(f"/tmp/{uuid.uuid4()}.xlsx")
    caminho_arquivo_codigos = Path(f"/tmp/{uuid.uuid4()}.xlsx")
    caminho_arquivo_final = Path(f"/tmp/{uuid.uuid4()}.json")

    cria_arquivo_excel(
        caminho_arquivo_escola,
        [
            {"CodEscola": "12345", "CodEOLAluno": "1111"},
            {"CodEscola": "67890", "CodEOLAluno": "2222"},
        ],
    )
    cria_arquivo_excel(
        caminho_arquivo_codigos,
        [
            {"CÓDIGO UNIDADE": "12345", "CODIGO EOL": "54321"},
            {"CÓDIGO UNIDADE": "67890", "CODIGO EOL": "98765"},
        ],
    )
    caminho_arquivo = get_escolas(
        caminho_arquivo_escola,
        caminho_arquivo_codigos,
        caminho_arquivo_final,
        in_memory=False,
    )

    assert Path(caminho_arquivo).exists()
    with open(caminho_arquivo, "r") as f:
        conteudo = f.read()
        assert "}" in conteudo

    for caminho in [
        caminho_arquivo_escola,
        caminho_arquivo_codigos,
        caminho_arquivo_final,
    ]:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_get_escolas_erro_cod_escola(variaveis_globais_escola):
    caminho_arquivo_escola = Path(f"/tmp/{uuid.uuid4()}.xlsx")
    caminho_arquivo_codigos = Path(f"/tmp/{uuid.uuid4()}.xlsx")
    caminho_arquivo_final = Path(f"/tmp/{uuid.uuid4()}.json")

    cod_escola = "22345"
    cria_arquivo_excel(
        caminho_arquivo_escola,
        [
            {"CodEscola": cod_escola, "CodEOLAluno": "1111"},
        ],
    )
    cria_arquivo_excel(
        caminho_arquivo_codigos,
        [
            {"CÓDIGO UNIDADE": "12345", "CODIGO EOL": "54321"},
            {"CÓDIGO UNIDADE": "67890", "CODIGO EOL": "98765"},
        ],
    )
    with pytest.raises(KeyError, match=f"'{cod_escola}'"):
        get_escolas(
            caminho_arquivo_escola,
            caminho_arquivo_codigos,
            caminho_arquivo_final,
            in_memory=False,
        )

    for caminho in [
        caminho_arquivo_escola,
        caminho_arquivo_codigos,
        caminho_arquivo_final,
    ]:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_atualiza_codigo_codae_das_escolas(codigo_codae_das_escolas):
    escola1, escola2, planilha = codigo_codae_das_escolas
    caminho_arquivo_escola = Path(f"/tmp/{uuid.uuid4()}.xlsx")
    cria_arquivo_excel(
        caminho_arquivo_escola,
        [
            {"codigo_eol": 123456, "codigo_unidade": 54321},
            {"codigo_eol": 789012, "codigo_unidade": 98765},
        ],
    )
    atualiza_codigo_codae_das_escolas(caminho_arquivo_escola, planilha.id)

    escola1.refresh_from_db()
    escola2.refresh_from_db()
    planilha.refresh_from_db()

    assert escola1.codigo_codae == "54321"
    assert escola2.codigo_codae == "98765"
    assert planilha.codigos_codae_vinculados is True

    if os.path.exists(caminho_arquivo_escola):
        os.remove(caminho_arquivo_escola)


def test_atualiza_codigo_codae_das_escolas_erro(codigo_codae_das_escolas, tmp_path):
    escola1, escola2, planilha = codigo_codae_das_escolas
    caminho_arquivo_escola = tmp_path / f"{uuid.uuid4()}.xlsx"

    cria_arquivo_excel(
        caminho_arquivo_escola,
        [
            {"codigo_eol": 123456, "codigo_unidade": 54321},
            {"codigo_eol": 789012, "codigo_unidade": 98765},
        ],
    )
    atualiza_codigo_codae_das_escolas(caminho_arquivo_escola, planilha.id + 1)

    escola1.refresh_from_db()
    escola2.refresh_from_db()
    planilha.refresh_from_db()

    assert escola1.codigo_codae == "54321"
    assert escola2.codigo_codae == "98765"
    assert planilha.codigos_codae_vinculados is False

    if os.path.exists(caminho_arquivo_escola):
        os.remove(caminho_arquivo_escola)


def test_atualiza_tipo_gestao_das_escolas(tipo_gestao_das_escolas):
    (
        escola1,
        escola2,
        planilha_atualizacao_tipo_gestao,
        caminho_arquivo_escola,
        parceira,
        direta,
    ) = tipo_gestao_das_escolas

    atualiza_tipo_gestao_das_escolas(
        caminho_arquivo_escola, planilha_atualizacao_tipo_gestao.id
    )

    escola1.refresh_from_db()
    escola2.refresh_from_db()
    planilha_atualizacao_tipo_gestao.refresh_from_db()

    assert escola1.tipo_gestao == parceira
    assert escola2.tipo_gestao == direta
    assert (
        planilha_atualizacao_tipo_gestao.status
        == StatusProcessamentoArquivo.SUCESSO.value
    )

    if os.path.exists(caminho_arquivo_escola):
        os.remove(caminho_arquivo_escola)


def test_atualiza_tipo_gestao_das_escolas_erro(tipo_gestao_das_escolas):
    (
        escola1,
        escola2,
        planilha_atualizacao_tipo_gestao,
        caminho_arquivo_escola,
        parceira,
        direta,
    ) = tipo_gestao_das_escolas
    escola2.codigo_eol = "989012"
    escola2.save()

    atualiza_tipo_gestao_das_escolas(
        caminho_arquivo_escola, planilha_atualizacao_tipo_gestao.id + 1
    )

    escola1.refresh_from_db()
    escola2.refresh_from_db()
    planilha_atualizacao_tipo_gestao.refresh_from_db()

    assert escola1.tipo_gestao == parceira
    assert escola2.tipo_gestao is None
    assert (
        planilha_atualizacao_tipo_gestao.status
        == StatusProcessamentoArquivo.PENDENTE.value
    )

    if os.path.exists(caminho_arquivo_escola):
        os.remove(caminho_arquivo_escola)
