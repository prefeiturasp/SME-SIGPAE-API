import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from sme_sigpae_api.escola.models import (
    Escola,
    LogAlunosMatriculadosPeriodoEscola,
    PeriodoEscolar,
    TipoTurma,
)


@pytest.fixture
def label_tipos_alimentacao():
    model = baker.make("SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE")
    tipo_vegetariano = baker.make("TipoAlimentacao", nome="Vegetariano")
    tipo_vegano = baker.make("TipoAlimentacao", nome="Vegano")
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
    alimentacao1 = baker.make("cardapio.TipoAlimentacao", nome="tp_alimentacao1")
    alimentacao2 = baker.make("cardapio.TipoAlimentacao", nome="tp_alimentacao2")
    alimentacao3 = baker.make("cardapio.TipoAlimentacao", nome="tp_alimentacao3")
    periodo_escolar = baker.make("escola.PeriodoEscolar", nome="MANHA")
    tipo_unidade_escolar = baker.make("escola.TipoUnidadeEscolar", iniciais="EMEF")
    vinculo = baker.make(
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
    tipos_alimentacao = baker.make("TipoAlimentacao", _quantity=5)
    tipo_unidade_escolar = baker.make("TipoUnidadeEscolar", iniciais=nome_ue)
    periodo_escolar = baker.make("PeriodoEscolar", nome=nome_periodo)
    return baker.make(
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
    tipo_alimentacao = baker.make(
        "TipoAlimentacao",
        nome="Lanche",
        posicao=2,
        uuid="c42a24bb-14f8-4871-9ee8-05bc42cf3061",
    )
    periodo_escolar = baker.make(
        "PeriodoEscolar", nome="TARDE", uuid="22596464-271e-448d-bcb3-adaba43fffc8"
    )

    return baker.make(
        "HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar",
        hora_inicial=hora_inicio,
        hora_final=hora_fim,
        escola=escola,
        tipo_alimentacao=tipo_alimentacao,
        periodo_escolar=periodo_escolar,
    )


@pytest.fixture
def periodos_escolares():
    for nome_periodo in [
        "MANHA",
        "TARDE",
        "INTEGRAL",
        "NOITE",
        "PARCIAL",
        "INTERMEDIARIO",
        "VESPERTINO",
    ]:
        baker.make("PeriodoEscolar", nome=nome_periodo)


@pytest.fixture
def escolas():
    for iniciais_unidade in [
        "EMEI",
        "EMEF",
        "CEI",
        "CEI DIRET",
        "CEMEI",
        "CIEJA",
        "CEU GESTAO",
        "EMEBS",
    ]:
        tipo_unidade_escolar = baker.make(
            "TipoUnidadeEscolar", iniciais=iniciais_unidade
        )
        baker.make(
            "Escola",
            nome=f"{iniciais_unidade} JOAO MENDES",
            tipo_unidade=tipo_unidade_escolar,
        )


def _cria_vinculos(iniciais_unidade: str, periodos: list[str]):
    tipos_alimentacao = baker.make("TipoAlimentacao", _quantity=5)
    escola = Escola.objects.get(tipo_unidade__iniciais=iniciais_unidade)
    for pe in periodos:
        periodo_escolar = PeriodoEscolar.objects.get(nome=pe)
        baker.make(
            "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
            tipos_alimentacao=tipos_alimentacao,
            tipo_unidade_escolar=escola.tipo_unidade,
            periodo_escolar=periodo_escolar,
        )
        log = baker.make(
            LogAlunosMatriculadosPeriodoEscola,
            escola=escola,
            periodo_escolar=periodo_escolar,
            quantidade_alunos=50,
            tipo_turma=TipoTurma.REGULAR.name,
            criado_em=datetime.datetime.now(),
        )
        log.criado_em = datetime.date(2025, 5, 5)
        log.save()
    return escola


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_emef(escolas, periodos_escolares):
    return _cria_vinculos("EMEF", ["NOITE", "MANHA", "TARDE", "INTEGRAL"])


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_emei(escolas, periodos_escolares):
    return _cria_vinculos("EMEI", ["TARDE", "MANHA", "INTEGRAL"])


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_cei(escolas, periodos_escolares):
    return _cria_vinculos("CEI", ["PARCIAL", "INTEGRAL", "MANHA", "TARDE"])


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_cemei(escolas, periodos_escolares):
    _cria_vinculos("CEI DIRET", ["PARCIAL", "INTEGRAL"])
    _cria_vinculos("EMEI", ["INTEGRAL", "TARDE", "MANHA"])
    return _cria_vinculos("CEMEI", [])


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_cieja(escolas, periodos_escolares):
    return _cria_vinculos(
        "CIEJA", ["VESPERTINO", "MANHA", "INTERMEDIARIO", "TARDE", "NOITE"]
    )


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_ceu_gestao(escolas, periodos_escolares):
    return _cria_vinculos("CEU GESTAO", ["INTEGRAL", "MANHA", "TARDE", "NOITE"])


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_emebs(escolas, periodos_escolares):
    return _cria_vinculos("EMEBS", ["NOITE", "MANHA", "TARDE", "INTEGRAL"])
