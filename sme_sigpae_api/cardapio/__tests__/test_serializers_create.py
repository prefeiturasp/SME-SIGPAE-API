import pytest
from freezegun import freeze_time
from model_mommy import mommy

from ..api.serializers.serializers_create import (
    GrupoSuspensaoAlimentacaoCreateSerializer,
    HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate,
    InversaoCardapioSerializerCreate,
    SuspensaoAlimentacaodeCEICreateSerializer,
)
from ..inversao_dia_cardapio.models import InversaoCardapio
from ..suspensao_alimentacao.models import GrupoSuspensaoAlimentacao
from ..suspensao_alimentacao_cei.models import SuspensaoAlimentacaoDaCEI

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


def test_horario_do_combo_tipo_alimentacao_serializer_validators(
    horarios_combos_tipo_alimentacao_validos, escola
):
    hora_inicial, hora_final, _ = horarios_combos_tipo_alimentacao_validos
    serializer_obj = (
        HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolarSerializerCreate()
    )
    combo = mommy.make(
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


def test_grupo_suspensao_alimentacao_serializer(grupo_suspensao_alimentacao_params):
    class FakeObject(object):
        user = mommy.make("perfil.Usuario")

    serializer_obj = GrupoSuspensaoAlimentacaoCreateSerializer(
        context={"request": FakeObject}
    )
    quantidades_por_periodo = []
    quantidades_periodo = mommy.make(
        "QuantidadePorPeriodoSuspensaoAlimentacao", _quantity=3
    )
    for quantidade_periodo in quantidades_periodo:
        quantidades_por_periodo.append(
            dict(
                numero_alunos=quantidade_periodo.numero_alunos,
                periodo_escolar=quantidade_periodo.periodo_escolar,
            )
        )

    suspensoes_alimentacao = []
    suspensoes = mommy.make("SuspensaoAlimentacao", _quantity=3)
    for suspensao in suspensoes:
        suspensoes_alimentacao.append(
            dict(
                prioritario=suspensao.prioritario,
                motivo=suspensao.motivo,
                data=suspensao.data,
                outro_motivo=suspensao.outro_motivo,
            )
        )
    validated_data_create = dict(
        quantidades_por_periodo=quantidades_por_periodo,
        suspensoes_alimentacao=suspensoes_alimentacao,
        escola=mommy.make("Escola"),
    )
    grupo_suspensao_created = serializer_obj.create(
        validated_data=validated_data_create
    )

    assert grupo_suspensao_created.criado_por == FakeObject().user
    assert grupo_suspensao_created.quantidades_por_periodo.count() == 3
    assert grupo_suspensao_created.suspensoes_alimentacao.count() == 3
    assert isinstance(grupo_suspensao_created, GrupoSuspensaoAlimentacao)

    validated_data_update = dict(
        quantidades_por_periodo=quantidades_por_periodo[:2],
        suspensoes_alimentacao=suspensoes_alimentacao[:1],
        escola=mommy.make("Escola"),
    )
    grupo_suspensao_updated = serializer_obj.update(
        instance=grupo_suspensao_created, validated_data=validated_data_update
    )
    assert grupo_suspensao_updated.criado_por == FakeObject().user
    assert grupo_suspensao_updated.quantidades_por_periodo.count() == 2
    assert grupo_suspensao_updated.suspensoes_alimentacao.count() == 1
    assert isinstance(grupo_suspensao_updated, GrupoSuspensaoAlimentacao)
