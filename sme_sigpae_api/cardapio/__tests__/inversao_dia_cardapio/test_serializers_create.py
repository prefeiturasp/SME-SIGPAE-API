import pytest
from freezegun import freeze_time
from model_mommy import mommy

from sme_sigpae_api.cardapio.inversao_dia_cardapio.api.serializers_create import (
    InversaoCardapioSerializerCreate,
)
from sme_sigpae_api.cardapio.inversao_dia_cardapio.models import InversaoCardapio

pytestmark = pytest.mark.django_db


@freeze_time("2019-10-14")
def test_inversao_serializer_validators(inversao_card_params, tipo_alimentacao):
    data_de, data_para, _, _ = inversao_card_params
    serializer_obj = InversaoCardapioSerializerCreate()
    cardapio_de = mommy.make("cardapio.Cardapio", data=data_de)
    cardapio_para = mommy.make("cardapio.Cardapio", data=data_para)
    tipo_ue = mommy.make(
        "escola.TipoUnidadeEscolar", cardapios=[cardapio_de, cardapio_para]
    )
    lote = mommy.make("Lote")
    escola = mommy.make("escola.Escola", tipo_unidade=tipo_ue, lote=lote)
    mommy.make("escola.DiaCalendario", escola=escola, data=data_de, dia_letivo=True)
    mommy.make("escola.DiaCalendario", escola=escola, data=data_para, dia_letivo=True)
    attrs = dict(
        data_de=data_de,
        data_para=data_para,
        escola=escola,
        tipos_alimentacao=[tipo_alimentacao],
    )

    response_de = serializer_obj.validate_data_de(data_de=data_de)
    response_para = serializer_obj.validate_data_para(data_para=data_para)
    response_geral = serializer_obj.validate(attrs=attrs)
    assert response_de == data_de
    assert response_para == data_para
    assert response_geral == attrs


@freeze_time("2019-10-15")
def test_inversao_serializer_creators(inversao_card_params):
    class FakeObject(object):
        user = mommy.make("perfil.Usuario")

    data_de_cria, data_para, data_de_atualiza, data_para_atualiza = inversao_card_params
    serializer_obj = InversaoCardapioSerializerCreate(context={"request": FakeObject})

    cardapio1 = mommy.make("cardapio.Cardapio", data=data_de_cria)
    cardapio2 = mommy.make("cardapio.Cardapio", data=data_para)
    cardapio3 = mommy.make("cardapio.Cardapio", data=data_de_atualiza)
    cardapio4 = mommy.make("cardapio.Cardapio", data=data_para_atualiza)

    tipo_ue = mommy.make(
        "escola.TipoUnidadeEscolar",
        cardapios=[cardapio1, cardapio2, cardapio3, cardapio4],
    )
    lote = mommy.make("Lote")
    escola1 = mommy.make("escola.Escola", tipo_unidade=tipo_ue, lote=lote)
    escola2 = mommy.make("escola.Escola", tipo_unidade=tipo_ue, lote=lote)

    validated_data_create = dict(
        data_de=data_de_cria, data_para=data_para, escola=escola1
    )
    validated_data_update = dict(
        data_de=data_de_atualiza, data_para=data_para_atualiza, escola=escola2
    )

    inversao_cardapio = serializer_obj.create(validated_data=validated_data_create)
    assert isinstance(inversao_cardapio, InversaoCardapio)

    assert inversao_cardapio.data_de_inversao == data_de_cria
    assert inversao_cardapio.data_para_inversao == data_para
    assert inversao_cardapio.escola == escola1

    instance = serializer_obj.update(
        instance=inversao_cardapio, validated_data=validated_data_update
    )
    assert isinstance(instance, InversaoCardapio)
    assert inversao_cardapio.data_de_inversao == data_de_atualiza
    assert inversao_cardapio.data_para_inversao == data_para_atualiza
    assert inversao_cardapio.escola == escola2
