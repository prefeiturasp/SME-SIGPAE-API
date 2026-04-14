import pytest

from sme_sigpae_api.dieta_especial.logs_models.api.serializers import (
    LogQuantidadeDietasAutorizadasRecreioNasFeriasSerializer,
)
from sme_sigpae_api.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadasRecreioNasFerias,
)

pytestmark = pytest.mark.django_db


def test_log_dietas_recreio_nas_ferias_serializer(
    logs_dieta_recreio_nas_ferias,
):
    log_recreio = LogQuantidadeDietasAutorizadasRecreioNasFerias.objects.first()
    log = LogQuantidadeDietasAutorizadasRecreioNasFeriasSerializer(log_recreio)
    data = log.data
    assert data is not None
    assert "escola" in data
    assert "classificacao" in data
    assert "dia" in data
    assert "criado_em" in data
    assert "data" in data
    assert "quantidade" in data
