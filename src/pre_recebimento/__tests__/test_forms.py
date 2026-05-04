import pytest

from src.pre_recebimento.base.models import UnidadeMedida
from src.pre_recebimento.forms import CaixaAltaNomeForm

pytestmark = pytest.mark.django_db


def test_caixa_alta_nome_form_validation():
    class CaixaAltaNomeFormComModelo(CaixaAltaNomeForm):
        class Meta:
            model = UnidadeMedida
            fields = ["nome", "abreviacao"]

    form = CaixaAltaNomeFormComModelo(data={"nome": "teste", "abreviacao": "t"})
    assert form.is_valid()
    assert form.cleaned_data["nome"] == "TESTE"
