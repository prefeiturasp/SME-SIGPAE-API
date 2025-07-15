import pytest
from rest_framework.serializers import ValidationError

from ..cronograma_entrega.api.validators import contrato_pertence_a_empresa, valida_parametros_calendario

pytestmark = pytest.mark.django_db


def test_contrato_pertence_a_empresa_validator(contrato, empresa):
    """Deve retornar True caso o contrato pertença à empresa ou lançar um ValidationError caso contrário."""
    assert contrato_pertence_a_empresa(contrato, empresa)

    empresa.contratos.clear()

    with pytest.raises(
        ValidationError, match="Contrato deve pertencer a empresa selecionada"
    ):
        contrato_pertence_a_empresa(contrato, empresa)


def test_valida_parametros_calendario_validator():
    with pytest.raises(ValidationError):
        valida_parametros_calendario(None, "2023")

    with pytest.raises(ValidationError):
        valida_parametros_calendario("a", "2023")

    with pytest.raises(ValidationError):
        valida_parametros_calendario("0", "2023")

    with pytest.raises(ValidationError):
        valida_parametros_calendario("13", "2023")

    with pytest.raises(ValidationError):
        valida_parametros_calendario("5", "23")
