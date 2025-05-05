import pytest
from django.http import QueryDict

from sme_sigpae_api.medicao_inicial.services.relatorio_adesao import obtem_resultados


@pytest.mark.django_db
def test_obtem_resultados_relatorio_adesao(
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
    total_servido = sum(valores)
    total_frequencia = sum(valores)
    total_adesao = round(total_servido / total_frequencia, 4)

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
    resultados = obtem_resultados(mes, ano, QueryDict())

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


@pytest.mark.django_db
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
    resultados = obtem_resultados(mes, ano, QueryDict())

    # assert
    assert resultados == {}
