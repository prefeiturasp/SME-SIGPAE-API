import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.api.serializers_create import (
    SuspensaoAlimentacaodeCEICreateSerializer,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao_cei.models import (
    SuspensaoAlimentacaoDaCEI,
)

pytestmark = pytest.mark.django_db


def test_suspensao_alimentacao_cei_creators(suspensao_alimentacao_cei_params, escola):
    class FakeObject(object):
        user = mommy.make("perfil.Usuario")

    motivo, data_create, data_update = suspensao_alimentacao_cei_params

    serializer_obj = SuspensaoAlimentacaodeCEICreateSerializer(
        context={"request": FakeObject}
    )

    validated_data_create = dict(
        escola=escola, motivo=motivo, outro_motivo="xxx", data=data_create
    )

    resp_create = serializer_obj.create(validated_data=validated_data_create)

    assert isinstance(resp_create, SuspensaoAlimentacaoDaCEI)
    assert resp_create.periodos_escolares.count() == 0
    assert resp_create.criado_por == FakeObject.user
    assert resp_create.data == data_create
    assert resp_create.motivo.nome == "outro"

    motivo = mommy.make("cardapio.MotivoSuspensao", nome="motivo")

    validated_data_update = dict(
        escola=escola, motivo=motivo, outro_motivo="", data=data_update
    )

    resp_update = serializer_obj.update(
        instance=resp_create, validated_data=validated_data_update
    )

    assert isinstance(resp_update, SuspensaoAlimentacaoDaCEI)
    assert resp_create.periodos_escolares.count() == 0
    assert resp_create.criado_por == FakeObject.user
    assert resp_create.data == data_update
    assert resp_create.motivo.nome == "motivo"
