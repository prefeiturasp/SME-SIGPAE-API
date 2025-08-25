import argparse
import os
from unittest.mock import MagicMock, patch

import pandas as pd

from sme_sigpae_api.perfil.management.commands import verifica_parceiras as vp


def test_normalizar_cpf():
    assert vp.normalizar_cpf("123.456.789-00") == "12345678900"
    assert vp.normalizar_cpf("11122233344") == "11122233344"
    assert vp.normalizar_cpf("abc123") == "123"
    assert vp.normalizar_cpf("") == ""


def test_extrair_cpf_de_linha_valido():
    row = ["nome", "123.456.789-00"]
    assert vp.extrair_cpf_de_linha(row) == "12345678900"


def test_extrair_cpf_de_linha_invalido():
    assert vp.extrair_cpf_de_linha([]) is None
    assert vp.extrair_cpf_de_linha(["teste", None]) is None
    assert vp.extrair_cpf_de_linha(["teste", "123"]) is None


@patch("pdfplumber.open")
def test_extrair_cpfs_pdf(mock_pdfplumber):
    fake_page = MagicMock()
    fake_page.extract_tables.return_value = [
        [["Nome", "123.456.789-00"], ["Outro", "111.222.333-44"]]
    ]
    mock_pdfplumber.return_value.__enter__.return_value.pages = [fake_page]

    cpfs = vp.extrair_cpfs_pdf("fake.pdf")
    assert cpfs == ["12345678900", "11122233344"]


@patch("requests.get")
def test_consultar_api_sucesso(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"cpf": "12345678900", "nome": "João"}
    mock_get.return_value = mock_resp

    result = vp.consultar_api("12345678900")
    assert result["cpf"] == "12345678900"
    assert result["nome"] == "João"


@patch("requests.get")
def test_consultar_api_falha(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    result = vp.consultar_api("12345678900")
    assert result == {"cpf": "12345678900", "erro": 404}


def test_salvar_excel(tmp_path):
    dados = [{"cpf": "12345678900", "nome": "Maria"}]
    output_file = tmp_path / "saida.xlsx"

    vp.salvar_excel(dados, str(output_file))
    assert os.path.exists(output_file)

    df = pd.read_excel(output_file)
    assert str(df.iloc[0]["cpf"]) == "12345678900"
    assert df.iloc[0]["nome"] == "Maria"


@patch("sme_sigpae_api.perfil.management.commands.verifica_parceiras.consultar_api")
@patch("sme_sigpae_api.perfil.management.commands.verifica_parceiras.extrair_cpfs_pdf")
@patch("sme_sigpae_api.perfil.management.commands.verifica_parceiras.salvar_excel")
def test_command_handle(mock_salvar, mock_extrair, mock_consultar, capsys):
    mock_extrair.return_value = ["12345678900", "11122233344"]
    mock_consultar.side_effect = [
        {"cpf": "12345678900", "nome": "A"},
        {"cpf": "11122233344", "nome": "B"},
    ]

    cmd = vp.Command()
    cmd.handle(pdf_entrada="fake.pdf", saida="saida.xlsx")

    captured = capsys.readouterr()
    assert "Extraindo CPFs" in captured.out
    assert "Consultando 12345678900" in captured.out
    assert "Salvando resultados" in captured.out
    assert "Concluído!" in captured.out

    mock_salvar.assert_called_once()


def test_add_arguments():
    parser = argparse.ArgumentParser()
    cmd = vp.Command()
    cmd.add_arguments(parser)

    args = parser.parse_args(["meu.pdf", "--saida", "out.xlsx"])
    assert args.pdf_entrada == "meu.pdf"
    assert args.saida == "out.xlsx"
