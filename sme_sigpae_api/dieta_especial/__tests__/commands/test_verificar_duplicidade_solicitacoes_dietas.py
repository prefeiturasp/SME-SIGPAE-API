import pytest
from django.core.management import call_command
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import SolicitacaoDietaEspecialFactory
from datetime import datetime
from unittest import mock


@pytest.mark.django_db
def test_handle_sem_duplicidades(monkeypatch, capsys):
    """
    Deve exibir mensagem de sucesso sem gerar planilha.
    """

    SolicitacaoDietaEspecialFactory(
        ativo=True,
        status="CODAE_AUTORIZADO",
        data_inicio=datetime(2024, 1, 1),
        data_termino=datetime(2024, 3, 1),
    )

    monkeypatch.setattr("os.makedirs", lambda *a, **kw: None)
    mock_save = mock.MagicMock()
    monkeypatch.setattr("openpyxl.Workbook.save", mock_save)

    call_command("verificar_duplicidade_solicitacoes_dietas")  # nome do comando

    captured = capsys.readouterr()
    assert "Nenhuma duplicidade encontrada" in captured.out
    mock_save.assert_not_called()


@pytest.mark.django_db
def test_handle_com_duplicidades(monkeypatch, capsys):
    """
    Deve gerar planilha e exibir mensagem com total encontrado.
    """
    aluno = SolicitacaoDietaEspecialFactory(
        ativo=True,
        status="CODAE_AUTORIZADO",
        data_inicio=datetime(2024, 1, 1),
        data_termino=datetime(2024, 3, 1),
    ).aluno

    SolicitacaoDietaEspecialFactory(
        aluno=aluno,
        ativo=True,
        status="CODAE_AUTORIZADO",
        data_inicio=datetime(2024, 2, 15),
        data_termino=datetime(2024, 5, 1),
    )

    monkeypatch.setattr("os.makedirs", lambda *a, **kw: None)
    mock_save = mock.MagicMock()
    monkeypatch.setattr("openpyxl.Workbook.save", mock_save)

    call_command("verificar_duplicidade_solicitacoes_dietas")

    mock_save.assert_called_once()

    captured = capsys.readouterr()
    assert "Planilha gerada com sucesso" in captured.out
    assert "solicitacoes_duplicadas" in captured.out
    assert "📄" in captured.out
