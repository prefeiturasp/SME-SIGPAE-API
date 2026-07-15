import pytest
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_logs_dieta_recreio_nas_ferias(
    client_autenticado_vinculo_codae_gestao_alimentacao_dieta,
    escola,
    logs_dieta_recreio_nas_ferias,
):
    client, user = client_autenticado_vinculo_codae_gestao_alimentacao_dieta
    response = client.get(
        f"/log-quantidade-dietas-autorizadas-recreio-nas-ferias/?escola_uuid={str(escola.uuid)}&mes=12&ano=2025"
    )

    assert response.status_code == status.HTTP_200_OK
    logs = response.json()
    assert len(logs) == 3
    assert any(log["classificacao"] == "Tipo B" for log in logs)
    assert any(log["classificacao"] == "Tipo A" for log in logs)
    assert any(log["classificacao"] == "Tipo A Enteral" for log in logs)

    for log in logs:
        assert log["dia"] == "22"
        assert log["data"] == "22/12/2025"
        assert log["quantidade"] == 5
        assert log["escola"] == str(escola.uuid)
