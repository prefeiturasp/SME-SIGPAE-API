import pytest
from model_bakery import baker

from src.dados_comuns.constants import StringsCaminhoModelos
from src.terceirizada.models import Edital

pytestmark = pytest.mark.django_db


def test_manager_edital_check_name_alrady_in_edital_ok():
    edital_1 = baker.make(
        StringsCaminhoModelos.MODEL_EDITAL.value, numero="Edital Numero 1"
    )
    edital_2 = baker.make(
        StringsCaminhoModelos.MODEL_EDITAL.value, numero="Edital Numero 2"
    )
    editais = [edital_1.uuid, edital_2.uuid]
    baker.make(
        "dieta_especial.ProtocoloPadraoDietaEspecial",
        nome_protocolo="ALERGIA - ABACATE",
        editais=[edital_1],
    )
    assert (
        "Edital Numero 1"
        in Edital.objects.check_editais_already_has_nome_protocolo(
            editais, "ALERGIA - ABACATE"
        )[0]["numero"]
    )
