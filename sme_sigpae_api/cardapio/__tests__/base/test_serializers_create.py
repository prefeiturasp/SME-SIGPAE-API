import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.base.api.serializers_create import (
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
    combo = baker.make(
        "ComboDoVinculoTipoAlimentacaoPeriodoTipoUE",
        uuid="9fe31f4a-716b-4677-9d7d-2868557cf954",
    )
    attrs = dict(
        hora_inicial=hora_inicial,
        hora_final=hora_final,
        escola=escola,
        combo_tipos_alimentacao=combo,
    )

    response_geral = serializer_obj.validate(attrs=attrs)
    assert response_geral == attrs
