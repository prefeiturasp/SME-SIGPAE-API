from decimal import Decimal

import pytest

from src.medicao_inicial.services.relatorio_ateste_financeiro import (
    build_relatorio_financeiro_grupo_cei,
    build_relatorio_financeiro_grupo_cemei,
    build_relatorio_financeiro_grupo_emei,
)
from src.medicao_inicial.utils import normalizar_nome_campo
from src.relatorios.relatorios import (
    relatorio_ateste_financeiro_grupo_cei,
    relatorio_ateste_financeiro_grupo_cemei,
    relatorio_ateste_financeiro_grupo_emei,
)
from src.relatorios.utils import extrair_texto_de_pdf


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
        totais_consumo,
    )

    assert resultado["alimentacao"]["total_atendimentos"] == 15
    assert resultado["dieta_a"]["total_consumo"] == 2
    assert resultado["dieta_b"]["total_consumo"] == 1
    assert resultado["consolidado"]["quantidade"] == 18

    assert resultado["cabecalho"]["data_referencia"] == "OUTUBRO/2025"


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
    assert "OUTUBRO/2025" in texto

    assert relatorio_financeiro_cei.lote.nome.upper() in texto
    assert relatorio_financeiro_cei.lote.diretoria_regional.nome in texto

    assert "Grupo 1" in texto

    assert "ALIMENTAÇÕES FAIXAS ETÁRIAS - SEM DIETAS" in texto
    assert "DIETA ESPECIAL - TIPO A" in texto
    assert "DIETA ESPECIAL - TIPO B" in texto

    assert "CONSOLIDADO TOTAL (A + B + C)" in texto
    assert "QUANTIDADE SERVIDA (A+B+C):" in texto
    assert "VALOR DO FATURAMENTO TOTAL (A+B+C):" in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_emei(
    relatorio_financeiro_emei,
    parametrizacao_financeira_emei,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_emei,
    vinculo_alimentacao_emei,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche,
        tipo_alimentacao_lanche_4h,
        tipo_alimentacao_refeicao,
    ]

    GRUPO_NOME = grupo_unidade_escolar_emei.nome

    valores_por_tipo = {
        "ALIMENTAÇÃO": [10, 20, 30],
        "DIETA ESPECIAL - TIPO A": [2, 4, 6],
        "DIETA ESPECIAL - TIPO B": [1, 2, 3],
    }

    totais_consumo = {
        chave: {
            (
                f"total_{normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()}"
                if chave == "ALIMENTAÇÃO"
                else normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()
            ): valor
            for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
        }
        for chave, valores in valores_por_tipo.items()
    }

    resultado = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
        totais_consumo,
    )

    assert resultado["alimentacao"]["total_atendimentos"] == 60
    assert resultado["alimentacao"]["valor_total"] == Decimal("1680.00")

    assert resultado["dieta_a"]["total_consumo"] == 12
    assert resultado["dieta_b"]["total_consumo"] == 3

    assert resultado["consolidado"]["quantidade"] == 75
    assert resultado["consolidado"]["valor"] == Decimal("1717.88")
    assert (
        resultado["consolidado"]["valor_extenso"]
        == "mil, setecentos e dezessete reais e oitenta e oito centavos"
    )

    assert resultado["cabecalho"]["data_referencia"] == "NOVEMBRO/2025"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_emei_conteudo_pdf(
    relatorio_financeiro_emei,
    parametrizacao_financeira_emei,
):
    pdf_bytes = relatorio_ateste_financeiro_grupo_emei(
        relatorio_financeiro_emei,
        parametrizacao_financeira_emei,
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ATESTE FINANCEIRO - MEDIÇÃO INICIAL" in texto

    assert "REFERÊNCIA:" in texto
    assert "NOVEMBRO/2025" in texto

    assert relatorio_financeiro_emei.lote.nome.upper() in texto
    assert relatorio_financeiro_emei.lote.diretoria_regional.nome in texto

    assert "Grupo 3" in texto
    assert "(CEU EMEI, EMEI)" in texto

    assert "TIPOS DE ALIMENTAÇÕES - SEM DIETAS" in texto
    assert "DIETA ESPECIAL - TIPO A, A ENTERAL E RESTRIÇÃO DE AMINOÁCIDOS" in texto
    assert "DIETA ESPECIAL - TIPO B" in texto

    assert "CONSOLIDADO TOTAL (A + B + C)" in texto
    assert "QUANTIDADE SERVIDA (A+B+C):" in texto
    assert "VALOR DO FATURAMENTO TOTAL (A+B+C):" in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_cieja(
    relatorio_financeiro_cieja,
    parametrizacao_financeira_cieja,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_cieja,
    vinculo_alimentacao_cieja,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche_4h,
        tipo_alimentacao_refeicao,
    ]

    GRUPO_NOME = grupo_unidade_escolar_cieja.nome

    valores_por_tipo = {
        "ALIMENTAÇÃO": [30, 60, 90],
        "DIETA ESPECIAL - TIPO A": [20, 40, 60],
        "DIETA ESPECIAL - TIPO B": [11, 22, 33],
    }

    totais_consumo = {
        chave: {
            (
                f"total_{normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()}"
                if chave == "ALIMENTAÇÃO"
                else normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()
            ): valor
            for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
        }
        for chave, valores in valores_por_tipo.items()
    }

    resultado = build_relatorio_financeiro_grupo_emei(
        relatorio_financeiro_cieja,
        parametrizacao_financeira_cieja,
        totais_consumo,
    )

    assert resultado["alimentacao"]["linhas"][0]["tipo"] == "REFEIÇÃO CIEJA E CMCT"

    assert len(resultado["dieta_a"]["linhas"]) == 2
    assert len(resultado["dieta_b"]["linhas"]) == 1

    assert resultado["consolidado"]["quantidade"] == 161

    assert resultado["cabecalho"]["data_referencia"] == "MARÇO/2026"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_cieja_conteudo_pdf(
    relatorio_financeiro_cieja,
    parametrizacao_financeira_cieja,
    vinculo_alimentacao_cieja,
):
    pdf_bytes = relatorio_ateste_financeiro_grupo_emei(
        relatorio_financeiro_cieja,
        parametrizacao_financeira_cieja,
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "MARÇO/2026" in texto

    assert relatorio_financeiro_cieja.lote.nome.upper() in texto
    assert relatorio_financeiro_cieja.lote.diretoria_regional.nome in texto

    assert "Grupo 6" in texto
    assert "(CIEJA, CMCT)" in texto

    assert texto.count("REFEIÇÃO CIEJA E CMCT") == 2
    assert texto.count("LANCHE 4H") == 3
    assert "KIT LANCHE" in texto

    assert "Página 1/1" in texto
    assert "Documento gerado em " in texto


@pytest.mark.django_db
def test_build_relatorio_financeiro_grupo_cemei(
    relatorio_financeiro_cemei,
    parametrizacao_financeira_cemei,
    faixas_etarias_ativas,
    tipo_alimentacao_lanche,
    tipo_alimentacao_lanche_4h,
    tipo_alimentacao_refeicao,
    grupo_unidade_escolar_cemei,
    vinculo_alimentacao_cemei,
):
    TIPOS_ALIMENTACOES = [
        tipo_alimentacao_lanche,
        tipo_alimentacao_lanche_4h,
        tipo_alimentacao_refeicao,
    ]

    GRUPO_NOME = grupo_unidade_escolar_cemei.nome

    totais_consumo_faixa = {
        chave: {str(faixa): 10 for faixa in faixas_etarias_ativas}
        for chave in [
            "ALIMENTAÇÃO - INTEGRAL",
            "ALIMENTAÇÃO - PARCIAL",
            "DIETA ESPECIAL - TIPO A - INTEGRAL",
            "DIETA ESPECIAL - TIPO B - PARCIAL",
        ]
    }

    valores_por_tipo = {
        "ALIMENTAÇÃO": [55, 66, 77],
        "DIETA ESPECIAL - TIPO A": [11, 22, 33],
        "DIETA ESPECIAL - TIPO B": [44, 55, 88],
    }

    totais_consumo_tipo = {
        chave: {
            (
                f"total_{normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()}"
                if chave == "ALIMENTAÇÃO"
                else normalizar_nome_campo(tipo.nome, GRUPO_NOME).lower()
            ): valor
            for tipo, valor in zip(TIPOS_ALIMENTACOES, valores)
        }
        for chave, valores in valores_por_tipo.items()
    }

    totais_consumo = {
        "FAIXA": totais_consumo_faixa,
        "TIPO": totais_consumo_tipo,
    }

    resultado = build_relatorio_financeiro_grupo_cemei(
        relatorio_financeiro_cemei,
        parametrizacao_financeira_cemei,
        totais_consumo,
    )

    numero_faixas = len(faixas_etarias_ativas) * 2

    assert len(resultado["cei"]["dieta_a"]["linhas"]) == numero_faixas
    assert len(resultado["cei"]["dieta_b"]["linhas"]) == numero_faixas

    assert len(resultado["emei"]["dieta_a"]["linhas"]) == 3
    assert len(resultado["emei"]["dieta_b"]["linhas"]) == 2

    assert resultado["emei"]["consolidado"]["quantidade"] == 363
    assert resultado["emei"]["consolidado"]["valor"] == Decimal("3467.82")

    assert resultado["cei"]["consolidado"]["quantidade"] == 320
    assert resultado["cei"]["consolidado"]["valor"] == Decimal("481.60")

    assert resultado["cabecalho"]["data_referencia"] == "ABRIL/2026"


@pytest.mark.django_db
def test_relatorio_ateste_financeiro_grupo_cemei_conteudo_pdf(
    relatorio_financeiro_cemei,
    parametrizacao_financeira_cemei,
    faixas_etarias_ativas,
    vinculo_alimentacao_cemei,
):
    pdf_bytes = relatorio_ateste_financeiro_grupo_cemei(
        relatorio_financeiro_cemei,
        parametrizacao_financeira_cemei,
    )

    texto = extrair_texto_de_pdf(pdf_bytes)

    assert "ABRIL/2026" in texto

    assert relatorio_financeiro_cemei.lote.nome.upper() in texto
    assert relatorio_financeiro_cemei.lote.diretoria_regional.nome in texto

    assert "Grupo 2" in texto
    assert "(CEMEI, CEU CEMEI)" in texto

    for faixa in faixas_etarias_ativas:
        assert texto.count(faixa.__str__()) == 6

    assert "REFEIÇÃO" in texto
    assert "LANCHE" in texto
    assert "LANCHE 4H" in texto
