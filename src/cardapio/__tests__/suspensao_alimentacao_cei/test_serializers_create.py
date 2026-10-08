import pytest
import datetime
from model_bakery import baker
from unittest.mock import patch

from src.cardapio.suspensao_alimentacao_cei.api.serializers_create import (
    SuspensaoAlimentacaodeCEICreateSerializer,
)
from src.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)
from src.dados_comuns.constants import StringsCaminhoModelos
from src.cardapio.suspensao_alimentacao_cei.api.serializers_create import (
    STATUS_QUE_LIBERAM_DUPLICIDADE,
)

pytestmark = pytest.mark.django_db
MODULO = "src.cardapio.suspensao_alimentacao_cei.api.serializers_create"


def test_suspensao_alimentacao_cei_creators(suspensao_alimentacao_cei_params, escola):
    class FakeObject(object):
        user = baker.make(StringsCaminhoModelos.MODEL_USUARIO.value)

    motivo, data_create, data_update = suspensao_alimentacao_cei_params

    serializer_obj = SuspensaoAlimentacaodeCEICreateSerializer(
        context={"request": FakeObject}
    )

    validated_data_create = {
        "escola": escola,
        "motivo": motivo,
        "outro_motivo": "xxx",
        "data": data_create,
    }

    resp_create = serializer_obj.create(validated_data=validated_data_create)

    assert isinstance(resp_create, SuspensaoAlimentacaoDaCEI)
    assert resp_create.periodos_escolares.count() == 0
    assert resp_create.criado_por == FakeObject.user
    assert resp_create.data == data_create
    assert resp_create.motivo.nome == "outro"

    motivo = baker.make("cardapio.MotivoSuspensao", nome="motivo")

    validated_data_update = {
        "escola": escola,
        "motivo": motivo,
        "outro_motivo": "",
        "data": data_update,
    }

    resp_update = serializer_obj.update(
        instance=resp_create, validated_data=validated_data_update
    )

    assert isinstance(resp_update, SuspensaoAlimentacaoDaCEI)
    assert resp_create.periodos_escolares.count() == 0
    assert resp_create.criado_por == FakeObject.user
    assert resp_create.data == data_update
    assert resp_create.motivo.nome == "motivo"


def test_validate_aceita_sem_duplicidade(monta_payload_cei, serializer_cei):
    ser = serializer_cei(monta_payload_cei())
    assert ser.is_valid(), ser.errors


def test_validate_bloqueia_duplicidade(
    cria_suspensao_cei, monta_payload_cei, serializer_cei
):
    cria_suspensao_cei(status="INFORMADO")

    ser = serializer_cei(monta_payload_cei())

    assert not ser.is_valid()
    assert ser.errors["message"][0] == "Já existe uma Solicitação de Suspensão de Alimentação para a data selecionada. Verifique os dados informados."
    assert ser.errors["conflitos"][0]["data"] == "2026-10-30"


@pytest.mark.parametrize("status", STATUS_QUE_LIBERAM_DUPLICIDADE)
def test_validate_libera_status_que_liberam_duplicidade(
    status, cria_suspensao_cei, monta_payload_cei, serializer_cei
):
    cria_suspensao_cei(status=status)

    ser = serializer_cei(monta_payload_cei())

    assert ser.is_valid(), ser.errors


def test_validate_libera_outra_data(
    cria_suspensao_cei, monta_payload_cei, serializer_cei
):
    cria_suspensao_cei(status="INFORMADO")

    ser = serializer_cei(monta_payload_cei(data=datetime.date(2026, 10, 31)))

    assert ser.is_valid(), ser.errors


def test_validate_libera_outra_escola(
    cria_suspensao_cei, monta_payload_cei, serializer_cei
):
    cria_suspensao_cei(status="INFORMADO")
    outra_escola = baker.make("escola.Escola")

    ser = serializer_cei(monta_payload_cei(escola=outra_escola))

    assert ser.is_valid(), ser.errors


def test_validate_update_ignora_o_proprio_registro(
    cria_suspensao_cei, monta_payload_cei, serializer_cei
):
    existente = cria_suspensao_cei(status="INFORMADO")

    ser = serializer_cei(monta_payload_cei(), instance=existente)

    assert ser.is_valid(), ser.errors


def test_validate_chama_regras_de_data(monta_payload_cei, serializer_cei):
    with patch(f"{MODULO}.nao_pode_ser_no_passado") as passado, patch(
        f"{MODULO}.deve_pedir_com_antecedencia"
    ) as antecedencia, patch(
        f"{MODULO}.deve_ser_no_mesmo_ano_corrente"
    ) as ano_corrente:
        ser = serializer_cei(monta_payload_cei())
        assert ser.is_valid(), ser.errors

    passado.assert_called_once_with(datetime.date(2026, 10, 30))
    antecedencia.assert_called_once_with(datetime.date(2026, 10, 30))
    ano_corrente.assert_called_once_with(datetime.date(2026, 10, 30))
