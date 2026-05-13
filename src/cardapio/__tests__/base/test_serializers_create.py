import pytest

from src.cardapio.base.api.serializers_create import (
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate,
)

pytestmark = pytest.mark.django_db


def test_horario_do_combo_tipo_alimentacao_serializer_validators(
    horarios_combos_tipo_alimentacao_validos, escola
):
    hora_inicial, hora_final, _ = horarios_combos_tipo_alimentacao_validos
    serializer_obj = (
        HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate()
    )
    attrs = dict(hora_inicial=hora_inicial, hora_final=hora_final, escola=escola)

    response_geral = serializer_obj.validate(attrs=attrs)
    assert response_geral == attrs
