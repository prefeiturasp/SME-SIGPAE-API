import pytest

from sme_sigpae_api.dados_comuns.constants import StatusProcessamentoArquivo
from sme_sigpae_api.dieta_especial.models import (
    ArquivoCargaAlimentosSubstitutos,
    ArquivoCargaDietaEspecial,
)

pytestmark = pytest.mark.django_db


def test_model_arquivo_carga_dieta_especial(arquivo_carga_dieta_especial):
    model = arquivo_carga_dieta_especial
    assert isinstance(model, ArquivoCargaDietaEspecial)
    assert model.status == StatusProcessamentoArquivo.PENDENTE.value


def test_model_arquivo_carga_alimentos_e_substitutos(
    arquivo_carga_alimentos_e_substitutos,
):
    model = arquivo_carga_alimentos_e_substitutos
    assert isinstance(model, ArquivoCargaAlimentosSubstitutos)
    assert model.status == StatusProcessamentoArquivo.PENDENTE.value
