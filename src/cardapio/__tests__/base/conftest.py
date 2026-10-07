import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker

from src.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.dados_comuns.constants import (
    TIPO_UNIDADE_CEI_DIRET,
    TIPOS_ALIMENTACAO,
    TIPOS_UNIDADE_ESCOLAR,
    StringsCaminhoModelos,
)
from src.escola.models import (
    AlunosMatriculadosPeriodoEscola,
    Escola,
    LogAlunosMatriculadosPeriodoEscola,
    PeriodoEscolar,
    TipoTurma,
)


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
    alimentacao1 = baker.make(
        StringsCaminhoModelos.MODEL_TIPOALIMENTACAO.value, nome="tp_alimentacao1"
    )
    alimentacao2 = baker.make(
        StringsCaminhoModelos.MODEL_TIPOALIMENTACAO.value, nome="tp_alimentacao2"
    )
    alimentacao3 = baker.make(
        StringsCaminhoModelos.MODEL_TIPOALIMENTACAO.value, nome="tp_alimentacao3"
    )
    periodo_escolar = baker.make(
        StringsCaminhoModelos.MODEL_PERIODOESCOLAR.value, nome="MANHA"
    )
    tipo_unidade_escolar = baker.make(
        "escola.TipoUnidadeEscolar", iniciais=TIPOS_UNIDADE_ESCOLAR.EMEF.value
    )
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
        ("MANHA", TIPOS_UNIDADE_ESCOLAR.EMEF.value),
        ("MANHA", TIPOS_UNIDADE_ESCOLAR.CIEJA.value),
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
        nome=TIPOS_ALIMENTACAO.LANCHE.value,
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
        TIPOS_UNIDADE_ESCOLAR.EMEI.value,
        TIPOS_UNIDADE_ESCOLAR.EMEF.value,
        TIPOS_UNIDADE_ESCOLAR.CEI.value,
        TIPO_UNIDADE_CEI_DIRET,
        TIPOS_UNIDADE_ESCOLAR.CEMEI.value,
        TIPOS_UNIDADE_ESCOLAR.CIEJA.value,
        TIPOS_UNIDADE_ESCOLAR.CEU_GESTAO.value,
        TIPOS_UNIDADE_ESCOLAR.EMEBS.value,
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
    return _cria_vinculos(
        TIPOS_UNIDADE_ESCOLAR.EMEF.value, ["NOITE", "MANHA", "TARDE", "INTEGRAL"]
    )


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_emei(escolas, periodos_escolares):
    return _cria_vinculos(
        TIPOS_UNIDADE_ESCOLAR.EMEI.value, ["TARDE", "MANHA", "INTEGRAL"]
    )


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_cei(escolas, periodos_escolares):
    return _cria_vinculos(
        TIPOS_UNIDADE_ESCOLAR.CEI.value, ["PARCIAL", "INTEGRAL", "MANHA", "TARDE"]
    )


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_cemei(escolas, periodos_escolares):
    _cria_vinculos(TIPO_UNIDADE_CEI_DIRET, ["PARCIAL", "INTEGRAL"])
    _cria_vinculos(TIPOS_UNIDADE_ESCOLAR.EMEI.value, ["INTEGRAL", "TARDE", "MANHA"])
    return _cria_vinculos(TIPOS_UNIDADE_ESCOLAR.CEMEI.value, [])


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_cieja(escolas, periodos_escolares):
    return _cria_vinculos(
        TIPOS_UNIDADE_ESCOLAR.CIEJA.value,
        ["VESPERTINO", "MANHA", "INTERMEDIARIO", "TARDE", "NOITE"],
    )


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_ceu_gestao(escolas, periodos_escolares):
    return _cria_vinculos(
        TIPOS_UNIDADE_ESCOLAR.CEU_GESTAO.value,
        ["INTEGRAL", "MANHA", "TARDE", "NOITE"],
    )


@pytest.fixture
def vinculo_alimentacao_periodo_escolar_emebs(escolas, periodos_escolares):
    return _cria_vinculos(
        TIPOS_UNIDADE_ESCOLAR.EMEBS.value, ["NOITE", "MANHA", "TARDE", "INTEGRAL"]
    )


@pytest.fixture
def vinculos_cemei_medicao(vinculo_alimentacao_periodo_escolar_cemei, escola):
    escola_cemei = vinculo_alimentacao_periodo_escolar_cemei
    escola_cemei.diretoria_regional = escola.diretoria_regional
    escola_cemei.save(update_fields=["diretoria_regional"])
    periodo_integral = PeriodoEscolar.objects.get(nome="INTEGRAL")
    baker.make(
        AlunosMatriculadosPeriodoEscola,
        escola=escola_cemei,
        periodo_escolar=periodo_integral,
        quantidade_alunos=50,
        tipo_turma=TipoTurma.REGULAR.name,
    )
    log = baker.make(
        LogAlunosMatriculadosPeriodoEscola,
        escola=escola_cemei,
        periodo_escolar=periodo_integral,
        quantidade_alunos=50,
        tipo_turma=TipoTurma.REGULAR.name,
    )
    LogAlunosMatriculadosPeriodoEscola.objects.filter(pk=log.pk).update(
        criado_em=datetime.datetime(2025, 5, 5, 12, tzinfo=datetime.timezone.utc)
    )
    periodo_noite = PeriodoEscolar.objects.get(nome="NOITE")
    tipo_unidade_emei = Escola.objects.get(
        tipo_unidade__iniciais=TIPOS_UNIDADE_ESCOLAR.EMEI.value
    ).tipo_unidade
    lanche = baker.make("TipoAlimentacao", nome=TIPOS_ALIMENTACAO.LANCHE_4H.value)
    vinculo_noite = baker.make(
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
        periodo_escolar=periodo_noite,
        tipo_unidade_escolar=tipo_unidade_emei,
        tipos_alimentacao=[lanche],
        ativo=True,
    )
    baker.make(
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
        periodo_escolar=periodo_noite,
        tipo_unidade_escolar=escola.tipo_unidade,
        tipos_alimentacao=[lanche],
        ativo=True,
    )
    vinculos_regulares = [
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(
            tipo_unidade_escolar__iniciais=iniciais,
            periodo_escolar__nome=nome,
        )
        for iniciais, nome in [
            (TIPO_UNIDADE_CEI_DIRET, "INTEGRAL"),
            (TIPOS_UNIDADE_ESCOLAR.EMEI.value, "MANHA"),
            (TIPOS_UNIDADE_ESCOLAR.EMEI.value, "TARDE"),
            (TIPOS_UNIDADE_ESCOLAR.EMEI.value, "INTEGRAL"),
        ]
    ]
    return {
        "escola": escola_cemei,
        "vinculo_noite": vinculo_noite,
        "vinculos_regulares": vinculos_regulares,
    }


@pytest.fixture
def inclusao_continua_cemei_medicao(vinculos_cemei_medicao):
    escola = vinculos_cemei_medicao["escola"]
    vinculo = vinculos_cemei_medicao["vinculo_noite"]
    motivo = baker.make(
        "MotivoInclusaoContinua", nome="Programas/Projetos Específicos"
    )
    inclusao = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        motivo=motivo,
        status="CODAE_AUTORIZADO",
        data_inicial=datetime.date(2025, 5, 5),
        data_final=datetime.date(2025, 5, 9),
    )
    return baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao,
        periodo_escolar=vinculo.periodo_escolar,
        tipos_alimentacao=list(vinculo.tipos_alimentacao.all()),
        numero_alunos=10,
        dias_semana=[0, 1, 2, 3, 4],
        cancelado=False,
        encerrado_a_partir_de=None,
    )
