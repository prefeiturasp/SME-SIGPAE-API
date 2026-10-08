import datetime

import pytest
from model_bakery import baker

from src.dados_comuns.constants import GRUPO_INFANTIL_INTEGRAL
from src.dieta_especial.logs_models.models import LogQuantidadeDietasAutorizadas
from src.dieta_especial.solicitacao_dieta_especial.models import ClassificacaoDieta
from src.inclusao_alimentacao.models import InclusaoDeAlimentacaoCEMEI
from src.medicao_inicial.models import CategoriaMedicao
from src.medicao_inicial.validators import (
    validate_lancamento_dietas_emei_cemei,
    validate_lancamento_inclusoes_dietas_emei_cemei,
)

pytestmark = pytest.mark.django_db

DATA_INCLUSAO = datetime.date(2026, 9, 19)


def _criar_inclusao(escola, periodo, alimentacoes, data):
    inclusao = baker.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        rastro_escola=escola,
        status=InclusaoDeAlimentacaoCEMEI.workflow_class.CODAE_AUTORIZADO,
    )
    motivo = baker.make("MotivoInclusaoNormal", nome="Reposição de aula")
    baker.make(
        "DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        data=data,
        motivo=motivo,
        cancelado=False,
    )
    quantidade = baker.make(
        "QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        periodo_escolar=periodo,
        quantidade_alunos=68,
    )
    quantidade.tipos_alimentacao.set(alimentacoes)
    return inclusao, quantidade


def _criar_valores(cenario, nomes_campos, dia=DATA_INCLUSAO.day):
    for nome_campo in nomes_campos:
        baker.make(
            "ValorMedicao",
            medicao=cenario["medicao"],
            categoria_medicao=cenario["categoria"],
            nome_campo=nome_campo,
            dia=f"{dia:02d}",
            valor="2",
        )


def _obter_logs(cenario):
    return list(
        LogQuantidadeDietasAutorizadas.objects.filter(
            escola=cenario["escola"],
            data__month=DATA_INCLUSAO.month,
            data__year=DATA_INCLUSAO.year,
            cei_ou_emei="EMEI",
        ).values_list("data", "periodo_escolar_id", "quantidade", "classificacao_id")
    )


def _validar_inclusoes(cenario, dias=None):
    inclusoes = InclusaoDeAlimentacaoCEMEI.objects.filter(
        escola=cenario["escola"],
        status=InclusaoDeAlimentacaoCEMEI.workflow_class.CODAE_AUTORIZADO,
    )
    return validate_lancamento_inclusoes_dietas_emei_cemei(
        lista_erros=[],
        inclusoes=inclusoes,
        categorias=[cenario["categoria"]],
        dias_nao_letivos=dias if dias is not None else [DATA_INCLUSAO.day],
        mes=DATA_INCLUSAO.month,
        ano=DATA_INCLUSAO.year,
        logs=_obter_logs(cenario),
        medicao=cenario["medicao"],
    )


def _erro_dietas(cenario):
    return [
        {
            "periodo_escolar": cenario["medicao"].nome_periodo_grupo,
            "erro": "Restam dias a serem lançados nas dietas.",
        }
    ]


@pytest.fixture(
    params=[
        (ClassificacaoDieta.TIPO_A, CategoriaMedicao.DIETA_ESPECIAL_TIPO_A),
        (ClassificacaoDieta.TIPO_B, CategoriaMedicao.DIETA_ESPECIAL_TIPO_B),
    ],
    ids=["tipo_a", "tipo_b"],
)
def dieta_cemei(request):
    nome_classificacao, nome_categoria = request.param
    return (
        baker.make("ClassificacaoDieta", nome=nome_classificacao),
        baker.make("CategoriaMedicao", nome=nome_categoria),
    )


@pytest.fixture
def cenario_dietas_cemei(
    request,
    dieta_cemei,
    tipo_unidade_escolar_emei,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_sobremesa,
):
    escola = request.getfixturevalue(getattr(request, "param", "escola_cemei"))
    periodo = baker.make("PeriodoEscolar", nome="INTEGRAL")
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        mes=f"{DATA_INCLUSAO.month:02d}",
        ano=str(DATA_INCLUSAO.year),
    )
    grupo = baker.make("GrupoMedicao", nome=GRUPO_INFANTIL_INTEGRAL)
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        grupo=grupo,
        periodo_escolar=None,
    )
    vinculo = baker.make(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=tipo_unidade_escolar_emei,
        periodo_escolar=periodo,
    )
    vinculo.tipos_alimentacao.set(
        [
            tipo_alimentacao_lanche,
            tipo_alimentacao_lanche_4h,
            tipo_alimentacao_refeicao,
            tipo_alimentacao_sobremesa,
        ]
    )
    inclusao, quantidade = _criar_inclusao(
        escola,
        periodo,
        [tipo_alimentacao_lanche, tipo_alimentacao_refeicao],
        DATA_INCLUSAO,
    )
    classificacao, categoria = dieta_cemei
    log = baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=escola,
        periodo_escolar=periodo,
        classificacao=classificacao,
        cei_ou_emei="EMEI",
        data=DATA_INCLUSAO,
        quantidade=2,
    )
    cenario = {
        "escola": escola,
        "periodo": periodo,
        "medicao": medicao,
        "categoria": categoria,
        "classificacao": classificacao,
        "inclusao": inclusao,
        "quantidade": quantidade,
        "log": log,
        "vinculo": vinculo,
        "lanche": tipo_alimentacao_lanche,
        "lanche_4h": tipo_alimentacao_lanche_4h,
        "refeicao": tipo_alimentacao_refeicao,
    }
    _criar_valores(cenario, ["frequencia", "lanche"])
    return cenario


@pytest.mark.parametrize(
    "cenario_dietas_cemei",
    ["escola_cemei", "escola_ceu_cemei"],
    indirect=True,
)
def test_inclusao_sem_lanche_4h_nao_exige_campo_bloqueado(cenario_dietas_cemei):
    cenario = cenario_dietas_cemei

    assert not cenario["medicao"].valores_medicao.filter(nome_campo="lanche_4h").exists()
    assert _validar_inclusoes(cenario) == []


@pytest.mark.parametrize("nome_campo", ["frequencia", "lanche"])
def test_inclusao_sem_campo_obrigatorio_continua_bloqueada(cenario_dietas_cemei, nome_campo):
    cenario = cenario_dietas_cemei
    cenario["medicao"].valores_medicao.filter(nome_campo=nome_campo).delete()

    assert _validar_inclusoes(cenario) == _erro_dietas(cenario)


def test_inclusao_com_lanche_4h_exige_preenchimento(cenario_dietas_cemei):
    cenario = cenario_dietas_cemei
    cenario["quantidade"].tipos_alimentacao.add(cenario["lanche_4h"])

    assert _validar_inclusoes(cenario) == _erro_dietas(cenario)

    _criar_valores(cenario, ["lanche_4h"])

    assert _validar_inclusoes(cenario) == []


def test_inclusao_sem_lanche_nao_exige_seu_lancamento(cenario_dietas_cemei):
    cenario = cenario_dietas_cemei
    cenario["quantidade"].tipos_alimentacao.remove(cenario["lanche"])
    cenario["medicao"].valores_medicao.filter(nome_campo="lanche").delete()

    assert _validar_inclusoes(cenario) == []


def test_alimentacao_sem_vinculo_com_periodo_nao_e_exigida(
    cenario_dietas_cemei,
):
    cenario = cenario_dietas_cemei
    cenario["vinculo"].tipos_alimentacao.remove(cenario["lanche_4h"])
    cenario["quantidade"].tipos_alimentacao.add(cenario["lanche_4h"])

    assert _validar_inclusoes(cenario) == []


def test_inclusao_de_outro_dia_nao_exige_lanche_4h_no_dia_19(
    cenario_dietas_cemei,
):
    cenario = cenario_dietas_cemei
    data_segunda_inclusao = DATA_INCLUSAO.replace(day=26)
    _criar_inclusao(
        cenario["escola"],
        cenario["periodo"],
        [cenario["lanche"], cenario["lanche_4h"]],
        data_segunda_inclusao,
    )
    baker.make(
        "LogQuantidadeDietasAutorizadas",
        escola=cenario["escola"],
        periodo_escolar=cenario["periodo"],
        classificacao=cenario["classificacao"],
        cei_ou_emei="EMEI",
        data=data_segunda_inclusao,
        quantidade=2,
    )
    _criar_valores(cenario, ["frequencia", "lanche"], dia=26)

    assert _validar_inclusoes(cenario) == []
    assert _validar_inclusoes(cenario, dias=[19, 26]) == _erro_dietas(cenario)

    _criar_valores(cenario, ["lanche_4h"], dia=26)

    assert _validar_inclusoes(cenario, dias=[19, 26]) == []


def test_alimentacao_de_outro_periodo_nao_e_exigida_no_integral(
    cenario_dietas_cemei,
):
    cenario = cenario_dietas_cemei
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
    quantidade_tarde = baker.make(
        "QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=cenario["inclusao"],
        periodo_escolar=periodo_tarde,
        quantidade_alunos=10,
    )
    quantidade_tarde.tipos_alimentacao.add(cenario["lanche_4h"])

    assert _validar_inclusoes(cenario) == []


def test_inclusao_sem_dietas_autorizadas_nao_exige_valores(cenario_dietas_cemei):
    cenario = cenario_dietas_cemei
    cenario["log"].quantidade = 0
    cenario["log"].save()
    cenario["medicao"].valores_medicao.all().delete()

    assert _validar_inclusoes(cenario) == []


def test_dia_regular_continua_exigindo_lanche_4h_do_vinculo(cenario_dietas_cemei):
    cenario = cenario_dietas_cemei
    cenario["log"].data = DATA_INCLUSAO.replace(day=18)
    cenario["log"].save()
    _criar_valores(cenario, ["frequencia", "lanche"], dia=18)

    erros = validate_lancamento_dietas_emei_cemei(
        [],
        DATA_INCLUSAO.month,
        DATA_INCLUSAO.year,
        [cenario["categoria"]],
        [18],
        _obter_logs(cenario),
        cenario["medicao"],
    )

    assert erros == _erro_dietas(cenario)

    _criar_valores(cenario, ["lanche_4h"], dia=18)

    assert (
        validate_lancamento_dietas_emei_cemei(
            [],
            DATA_INCLUSAO.month,
            DATA_INCLUSAO.year,
            [cenario["categoria"]],
            [18],
            _obter_logs(cenario),
            cenario["medicao"],
        )
        == []
    )


@pytest.mark.parametrize(
    "dieta_cemei",
    [
        (
            ClassificacaoDieta.TIPO_A_ENTERAL,
            CategoriaMedicao.DIETA_ESPECIAL_TIPO_A_ENTERAL_RESTRICAO_AMINOACIDOS,
        )
    ],
    indirect=True,
    ids=["enteral"],
)
@pytest.mark.parametrize("autoriza_refeicao", [True, False])
def test_dieta_enteral_exige_refeicao_somente_quando_autorizada(cenario_dietas_cemei, autoriza_refeicao):
    cenario = cenario_dietas_cemei
    if not autoriza_refeicao:
        cenario["quantidade"].tipos_alimentacao.remove(cenario["refeicao"])

    erros_esperados = _erro_dietas(cenario) if autoriza_refeicao else []

    assert _validar_inclusoes(cenario) == erros_esperados

    if autoriza_refeicao:
        _criar_valores(cenario, ["refeicao"])

        assert _validar_inclusoes(cenario) == []
