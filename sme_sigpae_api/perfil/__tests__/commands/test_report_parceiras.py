from unittest.mock import MagicMock, patch

import pytest

from sme_sigpae_api.perfil.management.commands.report_parceiras import Command


@pytest.fixture
def command():
    cmd = Command()
    cmd.stdout = MagicMock()
    cmd.style = MagicMock()
    cmd.style.SUCCESS = lambda x: x
    return cmd


def test_normaliza_unidade(command):
    assert command.normaliza_unidade("CEI TESTE") == "TESTE"
    assert command.normaliza_unidade("Cei TESTE") == "TESTE"
    assert command.normaliza_unidade("CR.P.CONV. TESTE") == " TESTE"
    assert command.normaliza_unidade("EMEF TESTE") == "EMEF TESTE"


@patch("pdfplumber.open")
def test_get_array_diretores(mock_pdf, command):
    fake_pdf = MagicMock()
    fake_pdf.pages = [MagicMock()]
    fake_pdf.pages[0].extract_tables.return_value = [
        [["10/01", "Unidade X", "Maria", "123.456.789-00"]]
    ]
    mock_pdf.return_value.__enter__.return_value = fake_pdf

    result = command.get_array_diretores()

    assert len(result) == 1
    assert result[0]["cpf"] == "12345678900"
    assert result[0]["unidade"] == "Unidade X"


def test_processar_usuarios_encontra(command):
    ws = MagicMock()
    ws.iter_rows.return_value = [
        ("erro", "12345678900", "", '[{"codigoCargo": 1}]'),
    ]
    lista_diretores = [{"unidade": "Unidade A", "nome": "João", "cpf": "12345678900"}]
    command.processar_usuarios(
        ws, lista_diretores, cond=lambda row: True, titulo="Teste"
    )
    command.stdout.write.assert_any_call("Unidade A - João - 12345678900")


def test_processar_usuarios_nao_encontra(command, capsys):
    ws = MagicMock()
    ws.iter_rows.return_value = [
        ("erro", "00000000000", "", '[{"codigoCargo": 1}]'),
    ]
    lista_diretores = []
    command.processar_usuarios(
        ws, lista_diretores, cond=lambda row: True, titulo="Teste"
    )
    captured = capsys.readouterr()
    assert "nao achou" in captured.out


def test_usuarios_escola_diferente(command):
    ws = MagicMock()
    ws.iter_rows.return_value = [
        ("", "12345678900", "", '[{"descricaoUnidade": "CEI INDIR - Outra Escola"}]'),
    ]
    lista_diretores = [{"unidade": "CEI TESTE", "nome": "Maria", "cpf": "12345678900"}]
    command.usuarios_escola_diferente(ws, lista_diretores)
    command.stdout.write.assert_any_call("CEI TESTE - Maria - 12345678900")


@patch("openpyxl.load_workbook")
@patch.object(Command, "get_array_diretores")
def test_handle_completo(mock_get_diretores, mock_wb, command):
    mock_get_diretores.return_value = [
        {"unidade": "Unidade A", "nome": "João", "cpf": "12345678900"},
    ]

    fake_ws = MagicMock()
    fake_ws.iter_rows.return_value = [
        # erro
        ("erro", "12345678900", "email@dominio.com", '[{"codigoCargo": 1}]'),
        # sem email
        ("", "12345678900", "", '[{"codigoCargo": 1}]'),
        # email inválido
        ("", "12345678900", "teste@", '[{"codigoCargo": 1}]'),
        # sem cargo
        ("", "12345678900", "alguem@ok.com", ""),
        # cargo não é diretor
        ("", "12345678900", "alguem@ok.com", '[{"codigoCargo": 2}]'),
    ]

    fake_wb = MagicMock()
    fake_wb.active = fake_ws
    mock_wb.return_value = fake_wb

    command.handle()

    chamadas = [c[0][0] for c in command.stdout.write.call_args_list]
    assert any("Usuários não encontrados" in c for c in chamadas)
    assert any("Usuários sem e-mail" in c for c in chamadas)
    assert any("Usuários com e-mail incorreto" in c for c in chamadas)
    assert any("Usuários sem cargo" in c for c in chamadas)
    assert any("Usuários não são diretores" in c for c in chamadas)
