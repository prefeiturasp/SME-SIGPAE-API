from datetime import date, datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict

from sme_sigpae_api.medicao_inicial.services.relatorio_adesao import (
    _parse_data,
    _valida_ano_mes,
    _validar_mes_ano_data,
    obtem_resultados,
    valida_parametros_periodo_lancamento,
)

pytestmark = pytest.mark.django_db


def test_obtem_resultados_relatorio_adesao_sem_periodo_de_lancamento(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacao, periodo_escolar)

    valores = range(1, 6)
    dias = [str(x).rjust(2, "0") for x in range(1, 6)]
    total_servido = sum(valores)
    total_frequencia = sum(valores)
    total_adesao = round(total_servido / total_frequencia, 4)

    for dia, valor in zip(dias, valores):
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao_refeicao,
            dia=dia,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            nome_campo="frequencia",
            dia=dia,
        )

    # act
    query_params = QueryDict(f"mes_ano={mes}_{ano}")
    resultados = obtem_resultados(query_params)

    # assert
    assert resultados == {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }


def test_obtem_resultados_relatorio_adesao_com_periodo_de_lancamento(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"
    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacao, periodo_escolar)

    valores = range(1, 6)
    dias = [str(x).rjust(2, "0") for x in range(1, 6)]
    total_servido = sum(valores[:3])
    total_frequencia = sum(valores[:3])
    total_adesao = round(total_servido / total_frequencia, 4)

    for dia, valor in zip(dias, valores):
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao_refeicao,
            dia=dia,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            nome_campo="frequencia",
            dia=dia,
        )

    # act
    query_params = QueryDict(
        f"mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )
    resultados = obtem_resultados(query_params)

    # assert
    assert resultados == {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }


def test_obtem_resultados_relatorio_adesao_solicitacao_nao_aprovada_pela_codae(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    solicitacao = make_solicitacao_medicao_inicial(mes, ano)
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = make_medicao(solicitacao, periodo_escolar)

    valores = range(1, 6)

    for x in valores:
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(x).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao_refeicao,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(x).rjust(2, "0"),
            nome_campo="frequencia",
        )

    # act
    query_params = QueryDict(f"mes_ano={mes}_{ano}")
    resultados = obtem_resultados(query_params)

    # assert
    assert resultados == {}


def test_valida_parametros_periodo_lancamento():
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"
    query_params = QueryDict(
        f"mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )
    assert valida_parametros_periodo_lancamento(query_params) is None


def test_valida_parametros_periodo_lancamento_sem_periodo_lancamento_ate():
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    query_params = QueryDict(
        f"mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}"
    )
    with pytest.raises(
        ValidationError,
        match="Ambos 'periodo_lancamento_de' e 'periodo_lancamento_ate' devem ser informados juntos",
    ):
        valida_parametros_periodo_lancamento(query_params)


def test_valida_parametros_periodo_lancamento_data_invertida():
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/{mes}/{ano}"
    periodo_lancamento_ate = f"03/{mes}/{ano}"
    query_params = QueryDict(
        f"mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_ate}&periodo_lancamento_ate={periodo_lancamento_de}"
    )
    with pytest.raises(
        ValidationError,
        match="'periodo_lancamento_de' deve ser anterior a 'periodo_lancamento_ate'",
    ):
        valida_parametros_periodo_lancamento(query_params)


def test_valida_ano_mes():
    mes_ano = "03_2024"
    mes, ano = _valida_ano_mes(mes_ano)
    assert isinstance(ano, int)
    assert isinstance(mes, int)
    assert ano == 2024
    assert mes == 3


def test_valida_ano_mes_e_none():
    with pytest.raises(
        ValidationError, match="É necessário informar o mês/ano de referência"
    ):
        _valida_ano_mes(None)


def test_valida_ano_mes_formato_incorreto():
    mes_ano = "03/2024"
    with pytest.raises(ValidationError, match="mes_ano deve estar no formato MM_AAAA"):
        _valida_ano_mes(mes_ano)


def test_parse_data():
    periodo_lancamento_de = f"01/05/2020"
    data = _parse_data(periodo_lancamento_de, "periodo_lancamento_de")
    assert isinstance(data, date)
    assert data.day == 1
    assert data.month == 5
    assert data.year == 2020


def test_parse_data_formato_incorreto():
    periodo_lancamento_de = f"01-05-2020"
    with pytest.raises(
        ValidationError,
        match="Formato de data inválido para 'periodo_lancamento_de'. Use o formato dd/mm/yyyy",
    ):
        _parse_data(periodo_lancamento_de, "periodo_lancamento_de")


def test_validar_mes_ano_data():
    mes = "03"
    ano = "2024"
    data = f"01/{mes}/{ano}"
    periodo_lancamento_de = datetime.strptime(data, "%d/%m/%Y").date()
    assert (
        _validar_mes_ano_data(
            periodo_lancamento_de, int(mes), int(ano), "periodo_lancamento_de"
        )
        is None
    )


def test_validar_mes_ano_data_incorreto():
    mes = "03"
    ano = "2024"
    periodo_lancamento_de = f"01/05/{ano}"
    data = datetime.strptime(periodo_lancamento_de, "%d/%m/%Y").date()
    with pytest.raises(
        ValidationError,
        match="[\"O mês/ano de 'periodo_lancamento_de' (05/2024) não coincide com 'mes_ano' (03_2024).\"]",
    ):
        _validar_mes_ano_data(data, int(mes), int(ano), "periodo_lancamento_de")
