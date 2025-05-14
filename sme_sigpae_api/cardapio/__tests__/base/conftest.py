import pytest
from model_mommy import mommy


@pytest.fixture
def label_tipos_alimentacao():
    model = mommy.make("SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE")
    tipo_vegetariano = mommy.make("TipoAlimentacao", nome="Vegetariano")
    tipo_vegano = mommy.make("TipoAlimentacao", nome="Vegano")
    return model, tipo_vegetariano, tipo_vegano
