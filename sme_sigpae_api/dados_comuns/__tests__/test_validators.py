import datetime

import pytest
from freezegun import freeze_time
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.cardapio.models import (
    AlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)

from ..validators import (
    campo_deve_ser_deste_tipo,
    campo_nao_pode_ser_nulo,
    deve_existir_cardapio,
    deve_pedir_com_antecedencia,
    deve_ser_no_mesmo_ano_corrente,
    deve_ser_no_passado,
    deve_ter_extensao_xls_xlsx_pdf,
    dia_util,
    nao_pode_ser_feriado,
    nao_pode_ser_no_passado,
    objeto_nao_deve_ter_duplicidade,
    valida_duplicidade_solicitacoes,
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
    assert verificar_se_existe(obj_model, assunto="TESTEXXX") is False


def test_verificar_se_existe_return_true(validators_models_object):
    obj_model = validators_models_object.__class__
    assert verificar_se_existe(obj_model, assunto="TESTE") is True


def test_verificar_se_existe_raise_exception(validators_models_object):
    with pytest.raises(TypeError, match='obj_model deve ser um "django models class"'):
        verificar_se_existe(validators_models_object)


def test_objeto_nao_deve_ter_duplicidade_return_none(validators_models_object):
    obj_model = validators_models_object.__class__
    assert objeto_nao_deve_ter_duplicidade(obj_model, assunto="TESTEXXX") is None


def test_objeto_nao_deve_ter_duplicidade_raise_error(validators_models_object):
    obj_model = validators_models_object.__class__
    with pytest.raises(ValidationError, match="Objeto já existe"):
        objeto_nao_deve_ter_duplicidade(obj_model, assunto="TESTE")


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
        assert nao_pode_ser_feriado(dia)


def test_nao_pode_ser_feriado_valor_valido(dias_uteis):
    dia, _ = dias_uteis
    assert nao_pode_ser_feriado(dia) is None


def test_nao_existe_cardapio(dias_sem_cardapio, escola):
    with pytest.raises(
        ValidationError,
        match=f'Escola não possui cardápio para esse dia: {dias_sem_cardapio.strftime("%d-%m-%Y")}',
    ):
        assert deve_existir_cardapio(escola, dias_sem_cardapio)


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


def test_valida_duplicidade_solicitacoes(substituicoes_alimentacao_periodo):
    substituicoes_alimentacao_periodo["data_inicial"] = datetime.date(2024, 4, 10)
    substituicoes_alimentacao_periodo["data_final"] = datetime.date(2024, 4, 30)
    assert valida_duplicidade_solicitacoes(substituicoes_alimentacao_periodo) is True


def test_valida_duplicidade_solicitacoes_duplicada(substituicoes_alimentacao_periodo):
    substituicoes_alimentacao_periodo["data_inicial"] = datetime.date(2024, 3, 10)
    substituicoes_alimentacao_periodo["data_final"] = datetime.date(2024, 3, 20)

    solicitacoes = AlteracaoCardapio.objects.filter(
        motivo=substituicoes_alimentacao_periodo["motivo"],
        escola=substituicoes_alimentacao_periodo["escola"],
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
        valida_duplicidade_solicitacoes(substituicoes_alimentacao_periodo)
