from unittest.mock import Mock

import pytest
from rest_framework import status

from src.escola.api import viewsets
from src.escola.models import Aluno
from src.escola.services import NovoSGPServicoLogadoException


@pytest.mark.django_db
@pytest.mark.parametrize(
    "metodo, rota",
    [
        ("get", "ver-foto"),
        ("post", "atualizar-foto"),
        ("delete", "deletar-foto"),
    ],
)
def test_foto_aluno_inexistente_nao_acessa_sgp(
    client_autenticado_da_escola, monkeypatch, metodo, rota
):
    assert not Aluno.objects.filter(codigo_eol="0").exists()
    servico = Mock(
        side_effect=NovoSGPServicoLogadoException("SGP indisponivel")
    )
    monkeypatch.setattr(viewsets, "NovoSGPServicoLogado", servico)

    response = getattr(client_autenticado_da_escola, metodo)(
        f"/alunos/0/{rota}/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    servico.assert_not_called()
