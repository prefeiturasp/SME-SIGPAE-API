import datetime

import pytest
from model_mommy import mommy


@pytest.fixture
def label_tipos_alimentacao():
    model = mommy.make("SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE")
    tipo_vegetariano = mommy.make("TipoAlimentacao", nome="Vegetariano")
    tipo_vegano = mommy.make("TipoAlimentacao", nome="Vegano")
    return model, tipo_vegetariano, tipo_vegano


@pytest.fixture(
    params=[
        # data inicio, data fim, esperado
        (datetime.time(10, 29), datetime.time(11, 29), True),
        (datetime.time(7, 10), datetime.time(7, 30), True),
        (datetime.time(6, 0), datetime.time(6, 10), True),
        (datetime.time(23, 30), datetime.time(23, 59), True),
        (datetime.time(20, 0), datetime.time(20, 22), True),
        (datetime.time(11, 0), datetime.time(13, 0), True),
        (datetime.time(15, 3), datetime.time(15, 21), True),
    ]
)
def horarios_combos_tipo_alimentacao_validos(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicio, data fim, esperado
        (
            datetime.time(10, 29),
            datetime.time(9, 29),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(7, 10),
            datetime.time(6, 30),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(6, 0),
            datetime.time(5, 59),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(23, 30),
            datetime.time(22, 59),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(20, 0),
            datetime.time(19, 22),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(11, 0),
            datetime.time(11, 0),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(15, 3),
            datetime.time(12, 21),
            "Hora Inicio não pode ser maior do que hora final",
        ),
    ]
)
def horarios_combos_tipo_alimentacao_invalidos(request):
    return request.param


@pytest.fixture()
def alterar_tipos_alimentacao_data():
    alimentacao1 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao1")
    alimentacao2 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao2")
    alimentacao3 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao3")
    periodo_escolar = mommy.make("escola.PeriodoEscolar", nome="MANHA")
    tipo_unidade_escolar = mommy.make("escola.TipoUnidadeEscolar", iniciais="EMEF")
    vinculo = mommy.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=periodo_escolar,
        tipo_unidade_escolar=tipo_unidade_escolar,
        tipos_alimentacao=[alimentacao1],
    )
    return {"vinculo": vinculo, "tipos_alimentacao": [alimentacao2, alimentacao3]}


@pytest.fixture(
    params=[
        # periodo escolar, tipo unidade escolar
        ("MANHA", "EMEF"),
        ("MANHA", "CIEJA"),
    ]
)
def vinculo_tipo_alimentacao(request):
    nome_periodo, nome_ue = request.param
    tipos_alimentacao = mommy.make("TipoAlimentacao", _quantity=5)
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais=nome_ue)
    periodo_escolar = mommy.make("PeriodoEscolar", nome=nome_periodo)
    return mommy.make(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipos_alimentacao=tipos_alimentacao,
        uuid="3bdf8144-9b17-495a-8387-5ce0d2a6120a",
        tipo_unidade_escolar=tipo_unidade_escolar,
        periodo_escolar=periodo_escolar,
    )


@pytest.fixture(
    params=[
        # hora inicio, hora fim
        ("07:00:00", "07:30:00"),
    ]
)
def horario_tipo_alimentacao(
    request, vinculo_tipo_alimentacao, escola_com_periodos_e_horarios_combos
):
    hora_inicio, hora_fim = request.param
    escola = escola_com_periodos_e_horarios_combos
    tipo_alimentacao = mommy.make(
        "TipoAlimentacao",
        nome="Lanche",
        posicao=2,
        uuid="c42a24bb-14f8-4871-9ee8-05bc42cf3061",
    )
    periodo_escolar = mommy.make(
        "PeriodoEscolar", nome="TARDE", uuid="22596464-271e-448d-bcb3-adaba43fffc8"
    )

    return mommy.make(
        "HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar",
        hora_inicial=hora_inicio,
        hora_final=hora_fim,
        escola=escola,
        tipo_alimentacao=tipo_alimentacao,
        periodo_escolar=periodo_escolar,
    )
