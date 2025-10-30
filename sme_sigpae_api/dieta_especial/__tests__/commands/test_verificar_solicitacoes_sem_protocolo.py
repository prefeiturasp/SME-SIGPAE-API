from datetime import datetime
from unittest import mock

import pytest
from django.core.management import call_command

from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial


@pytest.mark.django_db
def test_handle_sem_solicitacoes(monkeypatch, capsys):
    """
    Deve exibir mensagem informando ausência de registros.
    """
    SolicitacaoDietaEspecial.objects.all().delete()

    monkeypatch.setattr("os.makedirs", lambda path, exist_ok=True: None)
    monkeypatch.setattr("openpyxl.Workbook.save", lambda self, path: None)

    call_command("verificar_solicitacoes_sem_protocolo")

    captured = capsys.readouterr()
    assert "Nenhuma solicitação sem protocolo encontrada" in captured.out


@pytest.mark.django_db
def test_handle_com_solicitacoes(monkeypatch, capsys):
    """
    Deve gerar planilha e exibir mensagens de sucesso.
    """
    SolicitacaoDietaEspecialFactory(
        protocolo_padrao=None,
        ativo=True,
        status="CODAE_AUTORIZADO",
        criado_em=datetime(2025, 10, 14, 12, 0),
    )

    monkeypatch.setattr("os.makedirs", lambda path, exist_ok=True: None)
    mock_save = mock.MagicMock()
    monkeypatch.setattr("openpyxl.Workbook.save", mock_save)

    call_command("verificar_solicitacoes_sem_protocolo")

    assert mock_save.called
    args, kwargs = mock_save.call_args
    assert "solicitacoes_sem_protocolo" in args[0]

    captured = capsys.readouterr()
    assert "Planilha gerada com sucesso" in captured.out
    assert "1 solicitações encontradas" in captured.out
