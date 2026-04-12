import pytest
from sme_sigpae_api.medicao_inicial.services.relatorio_financeiro_cei import build_relatorio_financeiro_grupo_cei
from sme_sigpae_api.relatorios.relatorios import relatorio_ateste_financeiro_grupo_cei
from sme_sigpae_api.relatorios.utils import extrair_texto_de_pdf


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_cei(
    relatorio_financeiro_cei,
    parametrizacao_financeira_cei,
    faixas_etarias_ativas,
):
    totais_consumo = {
        "ALIMENTAÇÃO - INTEGRAL": {
            str(faixas_etarias_ativas[0]): 10,
        },
        "ALIMENTAÇÃO - PARCIAL": {
            str(faixas_etarias_ativas[0]): 5,
        },
        "DIETA ESPECIAL - TIPO A - INTEGRAL": {
            str(faixas_etarias_ativas[0]): 2,
        },
        "DIETA ESPECIAL - TIPO B - PARCIAL": {
            str(faixas_etarias_ativas[0]): 1,
        },
    }

    resultado = build_relatorio_financeiro_grupo_cei(
        relatorio_financeiro_cei,
        parametrizacao_financeira_cei,
        faixas_etarias_ativas,
        totais_consumo,
    )

    assert resultado["alimentacao"]["total_atendimentos"] == 15
    assert resultado["dieta_a"]["total_consumo"] == 2
    assert resultado["dieta_b"]["total_consumo"] == 1
    assert resultado["consolidado"]["quantidade"] == 18

    assert resultado["cabecalho"]["data_referencia"] == "10/2025"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_cei_conteudo_pdf(
    relatorio_financeiro_cei,
    parametrizacao_financeira_cei,
):
    pdf_bytes = relatorio_ateste_financeiro_grupo_cei(
        relatorio_financeiro_cei,
        parametrizacao_financeira_cei,
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ATESTE FINANCEIRO - MEDIÇÃO INICIAL" in texto
    assert "SECRETARIA MUNICIPAL DE EDUCAÇÃO" in texto

    assert "REFERÊNCIA:" in texto
    assert "10/2025" in texto

    assert relatorio_financeiro_cei.lote.nome.upper() in texto
    assert (
        relatorio_financeiro_cei.lote.diretoria_regional.nome
        in texto
    )

    assert "Grupo 1" in texto

    assert "ALIMENTAÇÕES FAIXAS ETÁRIAS - SEM DIETAS" in texto
    assert "DIETA ESPECIAL - TIPO A" in texto
    assert "DIETA ESPECIAL - TIPO B" in texto

    assert "CONSOLIDADO TOTAL (A + B + C)" in texto
    assert "QUANTIDADE SERVIDA (A+B+C):" in texto
    assert "VALOR DO FATURAMENTO TOTAL (A+B+C):" in texto
