import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from ...cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ...cardapio.alteracao_tipo_alimentacao_cei.models import AlteracaoCardapioCEI
from ...escola.dias_letivos.models import DiaLetivoSIGPAE
from ...inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from ..constants import FORMATO_DATA_BRASILEIRO, TIPOS_ALIMENTACAO
from ..validators import (
    campo_deve_ser_deste_tipo,
    campo_nao_pode_ser_nulo,
    deve_pedir_com_antecedencia,
    deve_ser_dia_letivo_e_dia_da_semana,
    deve_ser_no_mesmo_ano_corrente,
    deve_ser_no_passado,
    deve_ter_extensao_xls_xlsx_pdf,
    dia_util,
    escola_tem_dia_letivo_no_calendario,
    nao_pode_ser_feriado,
    nao_pode_ser_no_passado,
    objeto_nao_deve_ter_duplicidade,
    valida_dia_letivo_ou_inclusao_alimentacao_rpl,
    valida_duplicidade_solicitacoes,
    valida_duplicidade_solicitacoes_cei,
    verificar_se_existe,
)


@freeze_time("2019-05-22")  # qua
def test_deve_pedir_com_antecedencia(dias_teste_antecedencia):
    dia, dias_antec, esperado = dias_teste_antecedencia
    assert deve_pedir_com_antecedencia(dia, dias_antec) is esperado


@freeze_time("2019-05-22")  # qua
def test_deve_pedir_com_antecedencia_validation_error(dias_teste_antecedencia_erro):
    dia, dias_antec, esperado = dias_teste_antecedencia_erro
    with pytest.raises(ValidationError, match=esperado):
        deve_pedir_com_antecedencia(dia, dias_antec)


def test_dia_util(dias_uteis):
    dia, esperado = dias_uteis
    assert dia_util(dia) is esperado


def test_dia_nao_util(dias_nao_uteis):
    dia, esperado = dias_nao_uteis
    with pytest.raises(ValidationError, match=esperado):
        dia_util(dia)


@freeze_time("2019-05-22")
def test_nao_pode_ser_passado(dias_futuros):
    dia, esperado = dias_futuros
    assert nao_pode_ser_no_passado(dia) is esperado


@freeze_time("2019-05-22")
def test_nao_pode_ser_passado_raise_exception(dias_passados):
    dia, esperado = dias_passados
    with pytest.raises(ValidationError, match=esperado):
        nao_pode_ser_no_passado(dia)


def test_verificar_se_existe_return_false(validators_models_object):
    obj_model = validators_models_object.__class__
    assert verificar_se_existe(obj_model, email="TESTEXXX") is False


def test_verificar_se_existe_return_true(validators_models_object):
    obj_model = validators_models_object.__class__
    assert verificar_se_existe(obj_model, email="TESTE") is True


def test_verificar_se_existe_raise_exception(validators_models_object):
    with pytest.raises(TypeError, match='obj_model deve ser um "django models class"'):
        verificar_se_existe(validators_models_object)


def test_objeto_nao_deve_ter_duplicidade_return_none(validators_models_object):
    obj_model = validators_models_object.__class__
    assert objeto_nao_deve_ter_duplicidade(obj_model, email="TESTEXXX") is None


def test_objeto_nao_deve_ter_duplicidade_raise_error(validators_models_object):
    obj_model = validators_models_object.__class__
    with pytest.raises(ValidationError, match="Objeto já existe"):
        objeto_nao_deve_ter_duplicidade(obj_model, email="TESTE")


def test_nao_pode_ser_nulo_valor_none(validators_valor_str):
    with pytest.raises(ValidationError, match="Não pode ser nulo"):
        campo_nao_pode_ser_nulo(validators_valor_str["none"])


def test_nao_pode_ser_nulo_valor_valido(validators_valor_str):
    assert campo_nao_pode_ser_nulo(validators_valor_str["texto"]) is None


def test_deve_ser_deste_tipo_valor_rasie_error(validators_valor_str):
    with pytest.raises(ValidationError, match="Deve ser do tipo texto"):
        campo_deve_ser_deste_tipo(validators_valor_str["none"])


def test_deve_ser_deste_tipo_valor_valido(validators_valor_str):
    assert campo_deve_ser_deste_tipo(validators_valor_str["texto"]) is None


def test_nao_pode_ser_feriado_raise_error(dias_nao_uteis):
    dia, _ = dias_nao_uteis
    with pytest.raises(ValidationError, match="Não pode ser no feriado"):
        nao_pode_ser_feriado(dia)


def test_nao_pode_ser_feriado_valor_valido(dias_uteis):
    dia, _ = dias_uteis
    assert nao_pode_ser_feriado(dia) is None


@freeze_time("2025-01-01")  # Quarta-feira (feriado)
def test_deve_ser_dia_letivo_e_dia_da_semana_dia_util_sucesso(escola):
    # Segunda-feira: 2025-01-06 (não feriado)
    data = datetime.date(2025, 1, 6)
    assert deve_ser_dia_letivo_e_dia_da_semana(escola, data) is True


def test_deve_ser_dia_letivo_e_dia_da_semana_sabado_letivo_sucesso(escola):
    # Sábado: 2025-01-04
    data = datetime.date(2025, 1, 4)
    baker.make("escola.DiaCalendario", escola=escola, data=data, dia_letivo=True)
    assert deve_ser_dia_letivo_e_dia_da_semana(escola, data) is True


def test_deve_ser_dia_letivo_e_dia_da_semana_sabado_nao_letivo_falha(escola):
    # Sábado: 2025-01-04
    data = datetime.date(2025, 1, 4)
    baker.make("escola.DiaCalendario", escola=escola, data=data, dia_letivo=False)
    with pytest.raises(
        ValidationError,
        match=f"Dia {data.strftime(FORMATO_DATA_BRASILEIRO)} não é um dia letivo",
    ):
        deve_ser_dia_letivo_e_dia_da_semana(escola, data)


def test_deve_ser_dia_letivo_e_dia_da_semana_sabado_sem_registro_falha(escola):
    # Sábado: 2025-01-11
    data = datetime.date(2025, 1, 11)
    # Sem registro no DiaCalendario
    with pytest.raises(
        ValidationError,
        match=f"Dia {data.strftime(FORMATO_DATA_BRASILEIRO)} não é um dia letivo",
    ):
        deve_ser_dia_letivo_e_dia_da_semana(escola, data)


def test_deve_ser_dia_letivo_e_dia_da_semana_feriado_letivo_sucesso(escola):
    # Feriado: 2025-01-01 (Quarta-feira)
    data = datetime.date(2025, 1, 1)
    baker.make("escola.DiaCalendario", escola=escola, data=data, dia_letivo=True)
    assert deve_ser_dia_letivo_e_dia_da_semana(escola, data) is True


def test_deve_ser_dia_letivo_e_dia_da_semana_feriado_sem_registro_falha(escola):
    # Feriado: 2025-01-01 (Quarta-feira)
    data = datetime.date(2025, 1, 1)
    # Sem registro no DiaCalendario
    with pytest.raises(
        ValidationError,
        match=f"Dia {data.strftime(FORMATO_DATA_BRASILEIRO)} não é um dia letivo",
    ):
        deve_ser_dia_letivo_e_dia_da_semana(escola, data)


def test_deve_ser_dia_letivo_e_dia_da_semana_dia_letivo_sigpae_com_escola_sucesso(
    escola,
):
    # Sábado: 2025-01-04, sem registro de DiaCalendario no SGP
    data = datetime.date(2025, 1, 4)
    baker.make("escola.DiaLetivoSIGPAE", data=data, escolas=[escola])
    assert deve_ser_dia_letivo_e_dia_da_semana(escola, data) is True


def test_deve_ser_dia_letivo_e_dia_da_semana_dia_letivo_sigpae_sem_unidades_sucesso(
    escola,
):
    # Sábado: 2025-01-04, sem registro de DiaCalendario no SGP
    data = datetime.date(2025, 1, 4)
    baker.make(
        "escola.DiaLetivoSIGPAE",
        data=data,
        lotes=[escola.lote],
        tipos_unidade_escolar=[escola.tipo_unidade],
    )
    assert deve_ser_dia_letivo_e_dia_da_semana(escola, data) is True


@freeze_time("2019-07-10")
def test_valida_ano_diferente_exception(data_inversao_ano_diferente):
    data_inversao, esperado = data_inversao_ano_diferente
    with pytest.raises(serializers.ValidationError, match=esperado):
        deve_ser_no_mesmo_ano_corrente(data_inversao)


@freeze_time("2019-07-10")
def test_valida_mesmo_ano(data_inversao_mesmo_ano):
    data_inversao, esperado = data_inversao_mesmo_ano
    assert deve_ser_no_mesmo_ano_corrente(data_inversao) is esperado


def test_anexo_extensoes_validas(nomes_anexos_validos):
    nome = deve_ter_extensao_xls_xlsx_pdf(nomes_anexos_validos)
    assert type(nome) is str


def test_anexo_extensoes_invalidas(nomes_anexos_invalidos):
    with pytest.raises(ValidationError, match="Extensão inválida"):
        deve_ter_extensao_xls_xlsx_pdf(nomes_anexos_invalidos)


def test_data_deve_ser_no_passado_raise_error(data_maior_que_hoje):
    with pytest.raises(ValidationError, match="Deve ser data anterior a hoje"):
        deve_ser_no_passado(data_maior_que_hoje)


def test_valida_duplicidade_solicitacoes(solicitacao_substituicao_cardapio):
    solicitacao_substituicao_cardapio["data_inicial"] = datetime.date(2024, 4, 10)
    solicitacao_substituicao_cardapio["data_final"] = datetime.date(2024, 4, 30)
    assert valida_duplicidade_solicitacoes(solicitacao_substituicao_cardapio) is True


def test_valida_duplicidade_solicitacoes_duplicada(solicitacao_substituicao_cardapio):
    solicitacao_substituicao_cardapio["data_inicial"] = datetime.date(2024, 3, 10)
    solicitacao_substituicao_cardapio["data_final"] = datetime.date(2024, 3, 20)

    solicitacoes = AlteracaoCardapio.objects.filter(
        motivo=solicitacao_substituicao_cardapio["motivo"],
        escola=solicitacao_substituicao_cardapio["escola"],
    ).exclude(
        status__in=[
            "ESCOLA_CANCELOU",
            "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
            "CODAE_NEGOU_PEDIDO",
            "RASCUNHO",
        ]
    )

    assert solicitacoes.exists()
    with pytest.raises(
        ValidationError,
        match="Já existe uma solicitação de RPL para o mês e período selecionado!",
    ):
        valida_duplicidade_solicitacoes(solicitacao_substituicao_cardapio)


def test_valida_duplicidade_solicitacoes_cei(solicitacao_substituicao_cardapio_cei):
    data = datetime.date(2024, 4, 10)
    assert (
        valida_duplicidade_solicitacoes_cei(solicitacao_substituicao_cardapio_cei, data)
        is True
    )


def test_valida_duplicidade_solicitacoes_duplicada_cei(
    solicitacao_substituicao_cardapio_cei,
):
    data = datetime.date(2024, 3, 1)

    solicitacoes = AlteracaoCardapioCEI.objects.filter(
        motivo__uuid=solicitacao_substituicao_cardapio_cei["motivo"],
        escola__uuid=solicitacao_substituicao_cardapio_cei["escola"],
    ).exclude(
        status__in=[
            "ESCOLA_CANCELOU",
            "DRE_NAO_VALIDOU_PEDIDO_ESCOLA",
            "CODAE_NEGOU_PEDIDO",
            "RASCUNHO",
        ]
    )

    assert solicitacoes.exists()
    with pytest.raises(
        ValidationError,
        match="Já existe uma solicitação de RPL para o mês e período selecionado!",
    ):
        valida_duplicidade_solicitacoes_cei(solicitacao_substituicao_cardapio_cei, data)


def _make_inclusao_normal_autorizada(escola, data, periodo_tipos):
    """Cria uma inclusão normal autorizada com períodos e tipos informados.

    Args:
        escola (Escola): Escola da inclusão.
        data (datetime.date): Data da inclusão.
        periodo_tipos (dict): Mapeamento ``{periodo_nome: [tipo_nomes]}``.
    """
    grupo = baker.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola,
        status="CODAE_AUTORIZADO",
    )
    baker.make("InclusaoAlimentacaoNormal", grupo_inclusao=grupo, data=data)
    for periodo_nome, tipo_nomes in periodo_tipos.items():
        quantidade = baker.make(
            "QuantidadePorPeriodo",
            grupo_inclusao_normal=grupo,
            numero_alunos=100,
            periodo_escolar=baker.make("PeriodoEscolar", nome=periodo_nome),
        )
        quantidade.tipos_alimentacao.set(
            [baker.make("TipoAlimentacao", nome=nome) for nome in tipo_nomes]
        )
    return grupo


def test_esta_em_dia_letivo_sigpae_escola_dentro(escola):
    data = datetime.date(2024, 4, 10)
    dia_letivo = baker.make(DiaLetivoSIGPAE, data=data)
    dia_letivo.escolas.add(escola)
    assert escola.esta_em_dia_letivo_sigpae(data) is True


def test_escola_tem_dia_letivo_no_calendario_true(escola):
    data = datetime.date(2024, 4, 10)
    baker.make("DiaCalendario", escola=escola, data=data, dia_letivo=True)
    assert escola_tem_dia_letivo_no_calendario(escola, data) is True


def test_escola_tem_dia_letivo_no_calendario_false(escola):
    data = datetime.date(2024, 4, 10)
    baker.make("DiaCalendario", escola=escola, data=data, dia_letivo=False)
    assert escola_tem_dia_letivo_no_calendario(escola, data) is False


def test_escola_tem_dia_letivo_no_calendario_sem_registro(escola):
    data = datetime.date(2024, 4, 10)
    assert escola_tem_dia_letivo_no_calendario(escola, data) is False


def test_esta_em_dia_letivo_sigpae_lote_e_tipo_unidade(escola):
    data = datetime.date(2024, 4, 10)
    dia_letivo = baker.make(DiaLetivoSIGPAE, data=data)
    dia_letivo.lotes.add(escola.lote)
    dia_letivo.tipos_unidade_escolar.add(escola.tipo_unidade)
    assert escola.esta_em_dia_letivo_sigpae(data) is True


def test_esta_em_dia_letivo_sigpae_sem_registro(escola):
    data = datetime.date(2024, 4, 10)
    assert escola.esta_em_dia_letivo_sigpae(data) is False


def test_esta_em_dia_letivo_sigpae_outra_escola(escola):
    data = datetime.date(2024, 4, 10)
    outra_escola = baker.make("Escola")
    dia_letivo = baker.make(DiaLetivoSIGPAE, data=data)
    dia_letivo.escolas.add(outra_escola)
    assert escola.esta_em_dia_letivo_sigpae(data) is False


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_com_dia_letivo(escola):
    data = datetime.date(2024, 4, 10)
    dia_letivo = baker.make(DiaLetivoSIGPAE, data=data)
    dia_letivo.escolas.add(escola)
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )
        is True
    )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_com_dia_calendario(escola):
    data = datetime.date(2024, 4, 10)
    baker.make("DiaCalendario", escola=escola, data=data, dia_letivo=True)
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )
        is True
    )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_dia_calendario_nao_letivo(
    escola,
):
    data = datetime.date(2024, 4, 10)
    baker.make("DiaCalendario", escola=escola, data=data, dia_letivo=False)
    with pytest.raises(
        ValidationError,
        match="Dia 10/04 não é um dia letivo ou não existe uma inclusão",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_sabado_ignora_dia_calendario(
    escola,
):
    data = datetime.date(2024, 4, 13)  # sábado
    baker.make("DiaCalendario", escola=escola, data=data, dia_letivo=True)
    with pytest.raises(
        ValidationError,
        match="Dia 13/04 não é um dia letivo ou não existe uma inclusão",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_sabado_com_dia_letivo_sigpae(
    escola,
):
    data = datetime.date(2024, 4, 13)  # sábado
    dia_letivo = baker.make(DiaLetivoSIGPAE, data=data)
    dia_letivo.escolas.add(escola)
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )
        is True
    )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_sabado_com_inclusao(escola):
    data = datetime.date(2024, 4, 13)  # sábado
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {"MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value]},
    )
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )
        is True
    )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_com_inclusao(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {"MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value]},
    )
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )
        is True
    )


def test_valida_rpl_inclusao_periodo_contido(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {"MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value]},
    )
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            GrupoInclusaoAlimentacaoNormal,
            [{"periodo": "MANHA", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]}],
        )
        is True
    )


def test_valida_rpl_inclusao_periodo_nao_contido(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {"MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value]},
    )
    with pytest.raises(
        ValidationError,
        match="somente nos períodos MANHA",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            GrupoInclusaoAlimentacaoNormal,
            [{"periodo": "TARDE", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]}],
        )


def test_valida_rpl_inclusao_um_periodo_nao_contido_entre_varios(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {
            "MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value],
            "TARDE": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value],
        },
    )
    with pytest.raises(
        ValidationError,
        match="somente nos períodos MANHA e TARDE",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            GrupoInclusaoAlimentacaoNormal,
            [
                {"periodo": "MANHA", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]},
                {"periodo": "INTEGRAL", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]},
            ],
        )


def test_valida_rpl_inclusao_todos_periodos_contidos(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {
            "MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value],
            "TARDE": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value],
        },
    )
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            GrupoInclusaoAlimentacaoNormal,
            [
                {"periodo": "MANHA", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]},
                {"periodo": "TARDE", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]},
            ],
        )
        is True
    )


def test_valida_rpl_inclusao_sem_refeicao_e_lanche(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola, data, {"MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value]}
    )
    with pytest.raises(
        ValidationError,
        match="não possui Refeição e Lanche autorizado para o periodo MANHA",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            GrupoInclusaoAlimentacaoNormal,
            [{"periodo": "MANHA", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]}],
        )


def test_valida_rpl_inclusao_com_lanche_4h(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {
            "MANHA": [
                TIPOS_ALIMENTACAO.REFEICAO.value,
                TIPOS_ALIMENTACAO.LANCHE_4H.value,
            ]
        },
    )
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            GrupoInclusaoAlimentacaoNormal,
            [{"periodo": "MANHA", "lanches": [TIPOS_ALIMENTACAO.LANCHE_4H.value]}],
        )
        is True
    )


def test_valida_rpl_inclusao_lanche_4h_nao_autorizado(escola):
    data = datetime.date(2024, 4, 10)
    _make_inclusao_normal_autorizada(
        escola,
        data,
        {"MANHA": [TIPOS_ALIMENTACAO.REFEICAO.value, TIPOS_ALIMENTACAO.LANCHE.value]},
    )
    with pytest.raises(
        ValidationError,
        match="não possui Refeição e Lanche 4h autorizado para o periodo MANHA",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            GrupoInclusaoAlimentacaoNormal,
            [{"periodo": "MANHA", "lanches": [TIPOS_ALIMENTACAO.LANCHE_4H.value]}],
        )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_sem_nada(escola):
    data = datetime.date(2024, 4, 10)
    with pytest.raises(
        ValidationError,
        match="Dia 10/04 não é um dia letivo ou não existe uma inclusão",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, GrupoInclusaoAlimentacaoNormal
        )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_inclusao_cei(escola):
    data = datetime.date(2024, 4, 10)
    inclusao = baker.make(
        "InclusaoAlimentacaoDaCEI",
        escola=escola,
        status="CODAE_AUTORIZADO",
    )
    baker.make("DiasMotivosInclusaoDeAlimentacaoCEI", inclusao_cei=inclusao, data=data)
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, InclusaoAlimentacaoDaCEI
        )
        is True
    )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_cei_sem_inclusao(escola):
    data = datetime.date(2024, 4, 10)
    with pytest.raises(
        ValidationError,
        match="Dia 10/04 não é um dia letivo ou não existe uma inclusão",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, InclusaoAlimentacaoDaCEI
        )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_inclusao_cemei(escola):
    data = datetime.date(2024, 4, 10)
    inclusao = baker.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        data=data,
    )
    refeicao = baker.make("TipoAlimentacao", nome=TIPOS_ALIMENTACAO.REFEICAO.value)
    lanche = baker.make("TipoAlimentacao", nome=TIPOS_ALIMENTACAO.LANCHE.value)
    periodo = baker.make("PeriodoEscolar", nome="MANHA")
    quantidade = baker.make(
        "QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        quantidade_alunos=10,
        periodo_escolar=periodo,
    )
    quantidade.tipos_alimentacao.set([refeicao, lanche])
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola,
            data,
            InclusaoDeAlimentacaoCEMEI,
            [{"periodo": "MANHA", "lanches": [TIPOS_ALIMENTACAO.LANCHE.value]}],
            "EMEI",
        )
        is True
    )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_cemei_parte_cei(escola):
    data = datetime.date(2024, 4, 10)
    inclusao = baker.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        data=data,
    )
    faixa = baker.make("FaixaEtaria", inicio=0, fim=12, ativo=True)
    periodo = baker.make("PeriodoEscolar", nome="MANHA")
    baker.make(
        "QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        faixa_etaria=faixa,
        quantidade_alunos=10,
        periodo_escolar=periodo,
    )
    assert (
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, InclusaoDeAlimentacaoCEMEI, [], "CEI"
        )
        is True
    )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_cemei_parte_errada(escola):
    data = datetime.date(2024, 4, 10)
    inclusao = baker.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        data=data,
    )
    faixa = baker.make("FaixaEtaria", inicio=0, fim=12, ativo=True)
    periodo = baker.make("PeriodoEscolar", nome="MANHA")
    baker.make(
        "QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        faixa_etaria=faixa,
        quantidade_alunos=10,
        periodo_escolar=periodo,
    )
    with pytest.raises(
        ValidationError,
        match="somente para CEI",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, InclusaoDeAlimentacaoCEMEI, [], "EMEI"
        )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_cemei_todos_sem_emei(escola):
    data = datetime.date(2024, 4, 10)
    inclusao = baker.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        data=data,
    )
    faixa = baker.make("FaixaEtaria", inicio=0, fim=12, ativo=True)
    periodo = baker.make("PeriodoEscolar", nome="MANHA")
    baker.make(
        "QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        faixa_etaria=faixa,
        quantidade_alunos=10,
        periodo_escolar=periodo,
    )
    with pytest.raises(
        ValidationError,
        match="somente para CEI",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, InclusaoDeAlimentacaoCEMEI, [], "TODOS"
        )


def test_valida_dia_letivo_ou_inclusao_alimentacao_rpl_cemei_escopo_nulo(escola):
    data = datetime.date(2024, 4, 10)
    inclusao = baker.make(
        "InclusaoDeAlimentacaoCEMEI",
        escola=escola,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "DiasMotivosInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        data=data,
    )
    faixa = baker.make("FaixaEtaria", inicio=0, fim=12, ativo=True)
    periodo = baker.make("PeriodoEscolar", nome="MANHA")
    baker.make(
        "QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEI",
        inclusao_alimentacao_cemei=inclusao,
        faixa_etaria=faixa,
        quantidade_alunos=10,
        periodo_escolar=periodo,
    )
    with pytest.raises(
        ValidationError,
        match="somente para CEI",
    ):
        valida_dia_letivo_ou_inclusao_alimentacao_rpl(
            escola, data, InclusaoDeAlimentacaoCEMEI, [], None
        )
