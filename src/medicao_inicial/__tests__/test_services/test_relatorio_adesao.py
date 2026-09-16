from datetime import date, datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict
from model_bakery import baker

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO, TIPOS_ALIMENTACAO
from src.medicao_inicial.services.relatorio_adesao import (
    _parse_data,
    _valida_ano_mes,
    _validar_mes_ano_data,
    obtem_escolas_ordenadas,
    obtem_resultados,
    obtem_resultados_para_escola,
    obtem_resultados_por_escola,
    valida_parametros_periodo_lancamento,
)

pytestmark = pytest.mark.django_db


def _cria_escola_e_solicitacao_aprovada(
    escola_base, mes, ano, nome, codigo_eol, tipo_unidade=None
):
    escola = baker.make(
        "Escola",
        nome=nome,
        lote=escola_base.lote,
        diretoria_regional=escola_base.diretoria_regional,
        tipo_gestao=escola_base.tipo_gestao,
        tipo_unidade=tipo_unidade or escola_base.tipo_unidade,
        codigo_eol=codigo_eol,
    )
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=mes,
        ano=ano,
        escola=escola,
        rastro_lote=escola.lote,
        status="MEDICAO_APROVADA_PELA_CODAE",
    )
    return escola, solicitacao


def _cria_medicao_com_valores(
    solicitacao,
    periodo_escolar,
    categoria_medicao,
    tipo_alimentacao,
    make_medicao,
    make_valores_medicao,
    valores,
):
    medicao = make_medicao(solicitacao, periodo_escolar)
    dias = [str(dia).rjust(2, "0") for dia in range(1, len(valores) + 1)]
    for dia, valor in zip(dias, valores):
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            tipo_alimentacao=tipo_alimentacao,
            dia=dia,
        )
        make_valores_medicao(
            medicao=medicao,
            categoria_medicao=categoria_medicao,
            valor=str(valor).rjust(2, "0"),
            nome_campo="frequencia",
            dia=dia,
        )
    return medicao


def test_obtem_resultados_relatorio_adesao_sem_periodo_de_lancamento(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
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

    query_params = QueryDict(f"mes_ano={mes}_{ano}")
    resultados = obtem_resultados(query_params)

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

    query_params = QueryDict(
        f"mes_ano={mes}_{ano}&periodo_lancamento_de={periodo_lancamento_de}&periodo_lancamento_ate={periodo_lancamento_ate}"
    )
    resultados = obtem_resultados(query_params)

    assert resultados == {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }


def test_obtem_resultados_relatorio_adesao_exclui_medicoes_de_recreio_nas_ferias(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    escola,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
    recreio_nas_ferias,
):
    mes = "12"
    ano = "2025"
    solicitacao_recreio = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=mes,
        ano=ano,
        escola=escola,
        rastro_lote=escola.lote,
        status="MEDICAO_APROVADA_PELA_CODAE",
        recreio_nas_ferias=recreio_nas_ferias,
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    _cria_medicao_com_valores(
        solicitacao_recreio,
        periodo_escolar,
        categoria_medicao,
        tipo_alimentacao_refeicao,
        make_medicao,
        make_valores_medicao,
        range(1, 6),
    )

    query_params = QueryDict(f"mes_ano={mes}_{ano}")
    resultados = obtem_resultados(query_params)

    assert resultados == {}


def test_obtem_resultados_relatorio_adesao_solicitacao_nao_aprovada_pela_codae(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
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

    query_params = QueryDict(f"mes_ano={mes}_{ano}")
    resultados = obtem_resultados(query_params)

    assert resultados == {}


def test_obtem_resultados_por_escola(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    escola,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    mes = "03"
    ano = "2024"
    valores = range(1, 6)
    total_servido = sum(valores)
    total_frequencia = sum(valores)
    total_adesao = round(total_servido / total_frequencia, 4)

    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = _cria_medicao_com_valores(
        solicitacao,
        periodo_escolar,
        categoria_medicao,
        tipo_alimentacao_refeicao,
        make_medicao,
        make_valores_medicao,
        valores,
    )

    escola2, solicitacao2 = _cria_escola_e_solicitacao_aprovada(
        escola, mes, ano, "EMEF DOIS", "654321"
    )
    _cria_medicao_com_valores(
        solicitacao2,
        periodo_escolar,
        categoria_medicao,
        tipo_alimentacao_refeicao,
        make_medicao,
        make_valores_medicao,
        valores,
    )

    query_params = QueryDict(
        f"mes_ano={mes}_{ano}"
        f"&escola__uuid[]={escola.uuid}"
        f"&escola__uuid[]={escola2.uuid}"
    )
    resultados = obtem_resultados_por_escola(query_params)

    resultados_por_eol = {
        resultado["escola"]["codigo_eol"]: resultado for resultado in resultados
    }
    assert set(resultados_por_eol.keys()) == {escola.codigo_eol, escola2.codigo_eol}

    esperado = {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }
    assert resultados_por_eol[escola.codigo_eol]["escola"] == {
        "nome": escola.nome,
        "codigo_eol": escola.codigo_eol,
    }
    assert resultados_por_eol[escola.codigo_eol]["resultados"] == esperado
    assert resultados_por_eol[escola2.codigo_eol]["escola"] == {
        "nome": escola2.nome,
        "codigo_eol": escola2.codigo_eol,
    }
    assert resultados_por_eol[escola2.codigo_eol]["resultados"] == esperado


def test_obtem_resultados_por_escola_sem_medicoes_retorna_resultados_vazios(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    escola,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    mes = "03"
    ano = "2024"
    valores = range(1, 6)

    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    _cria_medicao_com_valores(
        solicitacao,
        periodo_escolar,
        categoria_medicao,
        tipo_alimentacao_refeicao,
        make_medicao,
        make_valores_medicao,
        valores,
    )

    escola_sem_medicao, _ = _cria_escola_e_solicitacao_aprovada(
        escola, mes, ano, "EMEF SEM MEDICAO", "654321"
    )

    query_params = QueryDict(
        f"mes_ano={mes}_{ano}"
        f"&escola__uuid[]={escola.uuid}"
        f"&escola__uuid[]={escola_sem_medicao.uuid}"
    )
    resultados = obtem_resultados_por_escola(query_params)

    resultados_por_eol = {
        resultado["escola"]["codigo_eol"]: resultado for resultado in resultados
    }
    assert set(resultados_por_eol.keys()) == {
        escola.codigo_eol,
        escola_sem_medicao.codigo_eol,
    }
    assert resultados_por_eol[escola.codigo_eol]["resultados"] != {}
    assert resultados_por_eol[escola_sem_medicao.codigo_eol]["resultados"] == {}


def test_obtem_resultados_filtra_por_tipos_unidades(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    escola,
    tipo_unidade_escolar_emei,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    mes = "03"
    ano = "2024"
    valores = range(1, 6)
    total_servido = sum(valores)
    total_frequencia = sum(valores)
    total_adesao = round(total_servido / total_frequencia, 4)

    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = _cria_medicao_com_valores(
        solicitacao,
        periodo_escolar,
        categoria_medicao,
        tipo_alimentacao_refeicao,
        make_medicao,
        make_valores_medicao,
        valores,
    )

    escola_emei, solicitacao_emei = _cria_escola_e_solicitacao_aprovada(
        escola,
        mes,
        ano,
        "EMEI TESTE",
        "654321",
        tipo_unidade=tipo_unidade_escolar_emei,
    )
    _cria_medicao_com_valores(
        solicitacao_emei,
        periodo_escolar,
        categoria_medicao,
        tipo_alimentacao_refeicao,
        make_medicao,
        make_valores_medicao,
        [2, 3, 4, 5, 6],
    )

    query_params = QueryDict(
        f"mes_ano={mes}_{ano}&tipos_unidades[]={escola.tipo_unidade.uuid}"
    )
    resultados = obtem_resultados(query_params)

    assert resultados == {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }


def test_obtem_escolas_ordenadas_por_nome(
    escola,
):
    # arrange
    escola_aaa, _ = _cria_escola_e_solicitacao_aprovada(
        escola, "03", "2024", "EMEF AAA", "111111"
    )
    escola_bbb, _ = _cria_escola_e_solicitacao_aprovada(
        escola, "03", "2024", "EMEF BBB", "222222"
    )

    # act
    escolas = obtem_escolas_ordenadas(
        [str(escola_bbb.uuid), str(escola.uuid), str(escola_aaa.uuid)]
    )

    # assert
    assert [e.nome for e in escolas] == ["EMEF AAA", "EMEF BBB", "EMEF TESTE"]


def test_obtem_resultados_para_escola(
    categoria_medicao,
    tipo_alimentacao_refeicao,
    escola,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    # arrange
    mes = "03"
    ano = "2024"
    valores = range(1, 6)
    total_servido = sum(valores)
    total_frequencia = sum(valores)
    total_adesao = round(total_servido / total_frequencia, 4)

    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )
    periodo_escolar = make_periodo_escolar("MANHA")
    medicao = _cria_medicao_com_valores(
        solicitacao,
        periodo_escolar,
        categoria_medicao,
        tipo_alimentacao_refeicao,
        make_medicao,
        make_valores_medicao,
        valores,
    )

    # act
    query_params = QueryDict(f"mes_ano={mes}_{ano}&escola__uuid[]={escola.uuid}")
    resultado = obtem_resultados_para_escola(escola, query_params)

    # assert
    assert resultado["escola"] == {
        "nome": escola.nome,
        "codigo_eol": escola.codigo_eol,
    }
    assert resultado["resultados"] == {
        medicao.nome_periodo_grupo: {
            tipo_alimentacao_refeicao.nome.upper(): {
                "total_servido": total_servido,
                "total_frequencia": total_frequencia,
                "total_adesao": total_adesao,
            }
        }
    }


def test_obtem_resultados_ordem_deterministica_de_periodos_e_alimentacoes(
    categoria_medicao,
    make_solicitacao_medicao_inicial,
    make_medicao,
    make_valores_medicao,
    make_periodo_escolar,
):
    mes = "03"
    ano = "2024"
    solicitacao = make_solicitacao_medicao_inicial(
        mes, ano, "MEDICAO_APROVADA_PELA_CODAE"
    )

    tipo_lanche = baker.make("TipoAlimentacao", nome=TIPOS_ALIMENTACAO.LANCHE.value)
    tipo_refeicao = baker.make("TipoAlimentacao", nome=TIPOS_ALIMENTACAO.REFEICAO.value)
    tipo_sobremesa = baker.make(
        "TipoAlimentacao", nome=TIPOS_ALIMENTACAO.SOBREMESA.value
    )

    # insere o período TARDE antes do MANHA para validar a ordenação dos períodos
    periodo_tarde = make_periodo_escolar("TARDE")
    medicao_tarde = make_medicao(solicitacao, periodo_tarde)
    # insere as alimentações fora da ordem esperada (Sobremesa, Refeição, Lanche)
    for tipo in [tipo_sobremesa, tipo_refeicao, tipo_lanche]:
        make_valores_medicao(
            medicao=medicao_tarde,
            categoria_medicao=categoria_medicao,
            valor="10",
            tipo_alimentacao=tipo,
            dia="01",
        )
    make_valores_medicao(
        medicao=medicao_tarde,
        categoria_medicao=categoria_medicao,
        valor="10",
        nome_campo="frequencia",
        dia="01",
    )

    periodo_manha = make_periodo_escolar("MANHA")
    medicao_manha = make_medicao(solicitacao, periodo_manha)
    for tipo in [tipo_sobremesa, tipo_refeicao, tipo_lanche]:
        make_valores_medicao(
            medicao=medicao_manha,
            categoria_medicao=categoria_medicao,
            valor="20",
            tipo_alimentacao=tipo,
            dia="01",
        )
    make_valores_medicao(
        medicao=medicao_manha,
        categoria_medicao=categoria_medicao,
        valor="20",
        nome_campo="frequencia",
        dia="01",
    )

    resultados = obtem_resultados(QueryDict(f"mes_ano={mes}_{ano}"))

    assert list(resultados.keys()) == ["MANHA", "TARDE"]
    assert list(resultados["MANHA"].keys()) == ["LANCHE", "REFEIÇÃO", "SOBREMESA"]
    assert list(resultados["TARDE"].keys()) == ["LANCHE", "REFEIÇÃO", "SOBREMESA"]


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
    periodo_lancamento_de = datetime.strptime(data, FORMATO_DATA_BRASILEIRO).date()
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
    data = datetime.strptime(periodo_lancamento_de, FORMATO_DATA_BRASILEIRO).date()
    with pytest.raises(
        ValidationError,
        match="[\"O mês/ano de 'periodo_lancamento_de' (05/2024) não coincide com 'mes_ano' (03_2024).\"]",
    ):
        _validar_mes_ano_data(data, int(mes), int(ano), "periodo_lancamento_de")
