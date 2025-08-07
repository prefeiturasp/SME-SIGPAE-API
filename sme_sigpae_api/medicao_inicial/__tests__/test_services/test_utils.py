from io import BytesIO

import pandas as pd
import pytest

from sme_sigpae_api.dados_comuns.constants import NOMES_CAMPOS
from sme_sigpae_api.medicao_inicial.services.utils import (
    generate_columns,
    gera_colunas_alimentacao,
    get_categorias_dietas,
    get_nome_periodo,
    get_valores_iniciais,
    update_dietas_alimentacoes,
    update_periodos_alimentacoes,
)

pytestmark = pytest.mark.django_db


def test_get_nome_periodo_emei_emef(
    medicao_grupo_solicitacao_alimentacao, medicao_grupo_alimentacao
):
    periodo = get_nome_periodo(medicao_grupo_solicitacao_alimentacao[0])
    assert isinstance(periodo, str)
    assert periodo == "Solicitações de Alimentação"

    periodo_manha = get_nome_periodo(medicao_grupo_alimentacao[0])
    assert isinstance(periodo_manha, str)
    assert periodo_manha == "MANHA"


def test_get_nome_periodo_cei(relatorio_consolidado_xlsx_cei):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    integral = get_nome_periodo(medicoes[0])
    assert isinstance(integral, str)
    assert integral == "INTEGRAL"

    manha = get_nome_periodo(medicoes[1])
    assert isinstance(manha, str)
    assert manha == "MANHA"

    parcial = get_nome_periodo(medicoes[2])
    assert isinstance(parcial, str)
    assert parcial == "PARCIAL"

    tarde = get_nome_periodo(medicoes[3])
    assert isinstance(tarde, str)
    assert tarde == "TARDE"


def test_get_nome_periodo_cemei(relatorio_consolidado_xlsx_cemei):
    medicoes = relatorio_consolidado_xlsx_cemei.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    assert medicoes.count() == 6

    integral_cei = get_nome_periodo(medicoes[0])
    assert isinstance(integral_cei, str)
    assert integral_cei == "INTEGRAL"

    parcial = get_nome_periodo(medicoes[1])
    assert isinstance(parcial, str)
    assert parcial == "PARCIAL"

    integral = get_nome_periodo(medicoes[2])
    assert isinstance(integral, str)
    assert integral == "Infantil INTEGRAL"

    manha = get_nome_periodo(medicoes[3])
    assert isinstance(manha, str)
    assert manha == "Infantil MANHA"

    tarde = get_nome_periodo(medicoes[4])
    assert isinstance(tarde, str)
    assert tarde == "Infantil TARDE"

    solicitacao = get_nome_periodo(medicoes[5])
    assert isinstance(solicitacao, str)
    assert solicitacao == "Solicitações de Alimentação"


def test_get_nome_periodo_emebs(relatorio_consolidado_xlsx_emebs):
    medicoes = relatorio_consolidado_xlsx_emebs.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )
    assert medicoes.count() == 6

    integral = get_nome_periodo(medicoes[0])
    assert isinstance(integral, str)
    assert integral == "INTEGRAL"

    manha = get_nome_periodo(medicoes[1])
    assert isinstance(manha, str)
    assert manha == "MANHA"

    noite = get_nome_periodo(medicoes[2])
    assert isinstance(noite, str)
    assert noite == "NOITE"

    tarde = get_nome_periodo(medicoes[3])
    assert isinstance(tarde, str)
    assert tarde == "TARDE"

    programas_projetos = get_nome_periodo(medicoes[4])
    assert isinstance(programas_projetos, str)
    assert programas_projetos == "Programas e Projetos"

    solicitacao = get_nome_periodo(medicoes[5])
    assert isinstance(solicitacao, str)
    assert solicitacao == "Solicitações de Alimentação"


def test_update_periodos_alimentacoes(faixas_etarias_ativas):
    lista_faixas = [faixa.id for faixa in faixas_etarias_ativas]
    lista_alimentacoes = [
        "lanche",
        "lanche_4h",
        "refeicao",
        "sobremesa",
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]
    lista_alimentacoes_solicitacao = ["kit_lanche", "lanche_emergencial"]
    periodos_alimentacoes = {}

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "INTEGRAL", lista_faixas
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "INTEGRAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["INTEGRAL"] == lista_faixas

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "PARCIAL", lista_faixas
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "PARCIAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["PARCIAL"] == lista_faixas

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "Infantil INTEGRAL", lista_alimentacoes
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Infantil INTEGRAL" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["Infantil INTEGRAL"] == lista_alimentacoes

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "Infantil MANHA", lista_alimentacoes
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Infantil MANHA" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["Infantil MANHA"] == lista_alimentacoes

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes, "Infantil TARDE", lista_alimentacoes
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Infantil TARDE" in periodos_alimentacoes.keys()
    assert periodos_alimentacoes["Infantil TARDE"] == lista_alimentacoes

    periodos_alimentacoes = update_periodos_alimentacoes(
        periodos_alimentacoes,
        "Solicitações de Alimentação",
        lista_alimentacoes_solicitacao,
    )
    assert isinstance(periodos_alimentacoes, dict)
    assert "Solicitações de Alimentação" in periodos_alimentacoes.keys()
    assert (
        periodos_alimentacoes["Solicitações de Alimentação"]
        == lista_alimentacoes_solicitacao
    )
    assert set(
        [
            "INTEGRAL",
            "PARCIAL",
            "Infantil INTEGRAL",
            "Infantil MANHA",
            "Infantil TARDE",
            "Solicitações de Alimentação",
        ]
    ).issubset(periodos_alimentacoes.keys())


def test_get_categorias_dietas_emef(relatorio_consolidado_xlsx_emef):
    medicoes = relatorio_consolidado_xlsx_emef.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    medicao_solicitacao = medicoes[1]

    categoria_manha = get_categorias_dietas(medicao_manha)
    assert isinstance(categoria_manha, list)
    assert len(categoria_manha) == 3
    assert categoria_manha == [
        "DIETA ESPECIAL - TIPO A",
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
        "DIETA ESPECIAL - TIPO B",
    ]

    categoria_solicitacao = get_categorias_dietas(medicao_solicitacao)
    assert isinstance(categoria_solicitacao, list)
    assert len(categoria_solicitacao) == 0


def test_get_categorias_dietas_cemei(relatorio_consolidado_xlsx_cemei):
    medicoes = relatorio_consolidado_xlsx_cemei.medicoes.all().order_by(
        "periodo_escolar__nome", "grupo__nome"
    )

    categoria_integral_cei = get_categorias_dietas(medicoes[0])
    assert isinstance(categoria_integral_cei, list)
    assert len(categoria_integral_cei) == 2
    assert categoria_integral_cei == [
        "DIETA ESPECIAL - TIPO A",
        "DIETA ESPECIAL - TIPO B",
    ]

    categoria_integral_emei = get_categorias_dietas(medicoes[3])
    assert isinstance(categoria_integral_emei, list)
    assert len(categoria_integral_emei) == 3
    assert categoria_integral_emei == [
        "DIETA ESPECIAL - TIPO A",
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
        "DIETA ESPECIAL - TIPO B",
    ]


def test_get_categorias_dietas_cei(relatorio_consolidado_xlsx_cei):
    medicoes = relatorio_consolidado_xlsx_cei.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    assert medicoes.count() == 4

    categoria_integral = get_categorias_dietas(medicoes[0])
    assert isinstance(categoria_integral, list)
    assert len(categoria_integral) == 2
    assert categoria_integral == ["DIETA ESPECIAL - TIPO A", "DIETA ESPECIAL - TIPO B"]

    categoria_manha = get_categorias_dietas(medicoes[1])
    assert isinstance(categoria_manha, list)
    assert len(categoria_manha) == 1
    assert categoria_manha == ["DIETA ESPECIAL - TIPO A"]

    categoria_parcial = get_categorias_dietas(medicoes[2])
    assert isinstance(categoria_parcial, list)
    assert len(categoria_parcial) == 2
    assert categoria_parcial == ["DIETA ESPECIAL - TIPO A", "DIETA ESPECIAL - TIPO B"]

    categoria_tarde = get_categorias_dietas(medicoes[3])
    assert isinstance(categoria_tarde, list)
    assert len(categoria_tarde) == 1
    assert categoria_tarde == ["DIETA ESPECIAL - TIPO B"]


def test_update_dietas_alimentacoes_por_faixa(faixas_etarias_ativas):
    lista_faixa_dietas = [faixa.id for faixa in faixas_etarias_ativas]
    categoria_a = "DIETA ESPECIAL - TIPO A"
    categoria_b = "DIETA ESPECIAL - TIPO B"

    dietas_alimentacoes = update_dietas_alimentacoes(
        {}, categoria_a, lista_faixa_dietas
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_a in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_a] == lista_faixa_dietas

    dietas_alimentacoes = update_dietas_alimentacoes(
        dietas_alimentacoes, categoria_b, lista_faixa_dietas
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_b in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_b] == lista_faixa_dietas

    assert set([categoria_a, categoria_b]).issubset(dietas_alimentacoes.keys())


def test_update_dietas_alimentacoes():
    categoria_a = "DIETA ESPECIAL - TIPO A"
    categoria_a_enteral_restricao = (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    )
    categoria_b = "DIETA ESPECIAL - TIPO B"

    lista_alimentacoes = ["lanche", "lanche_4h"]

    dietas_alimentacoes = update_dietas_alimentacoes(
        {}, categoria_a, lista_alimentacoes
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_a in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_a] == lista_alimentacoes

    dietas_alimentacoes = update_dietas_alimentacoes(
        dietas_alimentacoes, categoria_b, lista_alimentacoes
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_b in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_b] == lista_alimentacoes

    lista_alimentacoes += ["refeicao"]
    dietas_alimentacoes = update_dietas_alimentacoes(
        dietas_alimentacoes, categoria_a_enteral_restricao, lista_alimentacoes
    )
    assert isinstance(dietas_alimentacoes, dict)
    assert categoria_a_enteral_restricao in dietas_alimentacoes.keys()
    assert dietas_alimentacoes[categoria_a_enteral_restricao] == lista_alimentacoes


def test_generate_columns(faixas_etarias_ativas):
    faixas = [faixa.id for faixa in faixas_etarias_ativas]
    dict_periodos_dietas = {
        "Solicitações de Alimentação": ["kit_lanche", "lanche_emergencial"],
        "INTEGRAL": faixas,
        "Infantil MANHA": [
            "lanche",
            "lanche_4h",
            "refeicao",
            "total_refeicoes_pagamento",
            "sobremesa",
            "total_sobremesas_pagamento",
        ],
        "DIETA ESPECIAL - TIPO A": ["lanche", "lanche_4h", "refeicao"],
        "DIETA ESPECIAL - TIPO B": ["lanche", "lanche_4h"],
    }
    colunas = generate_columns(dict_periodos_dietas)
    assert isinstance(colunas, list)
    assert len(colunas) == 21
    assert sum(1 for tupla in colunas if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas if tupla[0] == "Infantil MANHA") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 3
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "Solicitações de Alimentação") == 2

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 1


def test_get_valores_iniciais_emef(relatorio_consolidado_xlsx_emef):
    valores = get_valores_iniciais(relatorio_consolidado_xlsx_emef)
    assert isinstance(valores, list)
    assert len(valores) == 3
    assert valores == [
        relatorio_consolidado_xlsx_emef.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_emef.escola.codigo_eol,
        relatorio_consolidado_xlsx_emef.escola.nome,
    ]


def test_get_valores_iniciais_cei(relatorio_consolidado_xlsx_cei):
    valores = get_valores_iniciais(relatorio_consolidado_xlsx_cei)
    assert isinstance(valores, list)
    assert len(valores) == 3
    assert valores == [
        relatorio_consolidado_xlsx_cei.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_cei.escola.codigo_eol,
        relatorio_consolidado_xlsx_cei.escola.nome,
    ]


def test_get_valores_iniciais_cemei(relatorio_consolidado_xlsx_cemei):
    valores = get_valores_iniciais(relatorio_consolidado_xlsx_cemei)
    assert isinstance(valores, list)
    assert len(valores) == 3
    assert valores == [
        relatorio_consolidado_xlsx_cemei.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_cemei.escola.codigo_eol,
        relatorio_consolidado_xlsx_cemei.escola.nome,
    ]


def test_get_valores_iniciais_emebs(relatorio_consolidado_xlsx_emebs):
    valores = get_valores_iniciais(relatorio_consolidado_xlsx_emebs)
    assert isinstance(valores, list)
    assert len(valores) == 3
    assert valores == [
        relatorio_consolidado_xlsx_emebs.escola.tipo_unidade.iniciais,
        relatorio_consolidado_xlsx_emebs.escola.codigo_eol,
        relatorio_consolidado_xlsx_emebs.escola.nome,
    ]


def test_gera_colunas_alimentacao_cemei(
    relatorio_consolidado_xlsx_cemei,
    mock_colunas_cemei,
    mock_linhas_cemei,
    faixas_etarias_ativas,
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_cemei.mes}-{ relatorio_consolidado_xlsx_cemei.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    NOMES_CAMPOS.update({faixa.id: faixa.__str__() for faixa in faixas_etarias_ativas})

    df = gera_colunas_alimentacao(
        aba, mock_colunas_cemei, mock_linhas_cemei, writer, NOMES_CAMPOS
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 76

    assert sum(1 for tupla in colunas_df if tupla[0] == "INTEGRAL") == 8
    assert sum(1 for tupla in colunas_df if tupla[0] == "PARCIAL") == 8
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO A - INTEGRAL"
        )
        == 8
    )
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO B - INTEGRAL"
        )
        == 8
    )
    assert (
        sum(
            1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A - PARCIAL"
        )
        == 8
    )
    assert (
        sum(
            1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B - PARCIAL"
        )
        == 8
    )
    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL INTEGRAL") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL MANHA") == 6
    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL TARDE") == 6
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO A - INFANTIL"
        )
        == 3
    )
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[0] == "DIETA ESPECIAL - TIPO B - INFANTIL"
        )
        == 2
    )

    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Kit Lanche") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche Emerg.") == 1

    assert sum(1 for tupla in colunas_df if tupla[1] == "00 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "01 a 03 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 a 05 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "06 a 07 meses") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "08 a 11 meses") == 6
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "01 ano a 01 ano e 11 meses") == 6
    )
    assert (
        sum(1 for tupla in colunas_df if tupla[1] == "02 anos a 03 anos e 11 meses")
        == 6
    )
    assert sum(1 for tupla in colunas_df if tupla[1] == "04 anos a 06 anos") == 6

    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche") == 5
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 4h") == 5
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeição") == 4
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeições p/ Pagamento") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesa") == 3
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesas p/ Pagamento") == 3

    assert df.iloc[0].tolist() == [
        "CEMEI",
        "543210",
        "CEMEI TESTE",
        5.0,
        5.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        30.0,
        30.0,
        15.0,
        15.0,
        15.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        543210.0,
        0.0,
        5.0,
        5.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        15.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        150.0,
        30.0,
        30.0,
        15.0,
        15.0,
        15.0,
    ]


def test_gera_colunas_alimentacao_emebs(
    relatorio_consolidado_xlsx_emebs, mock_colunas_emebs, mock_linhas_emebs
):
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {relatorio_consolidado_xlsx_emebs.mes}-{ relatorio_consolidado_xlsx_emebs.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")
    colunas_fixas = [
        ("", "", "Tipo"),
        ("", "", "Cód. EOL"),
        ("", "", "Unidade Escolar"),
    ]

    headers = []
    for turma, chave, valor in mock_colunas_emebs:
        if chave == "Solicitações de Alimentação":
            headers.append(("", "", NOMES_CAMPOS[valor]))
        else:
            headers.append((turma, chave.upper(), NOMES_CAMPOS[valor]))

    df = gera_colunas_alimentacao(
        aba,
        None,
        mock_linhas_emebs,
        writer,
        None,
        colunas_fixas=colunas_fixas,
        headers=headers,
    )
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 67

    assert sum(1 for tupla in colunas_df if tupla[0] == "INFANTIL") == 28
    assert sum(1 for tupla in colunas_df if tupla[0] == "FUNDAMENTAL") == 34

    assert sum(1 for tupla in colunas_df if tupla[1] == "MANHA") == 12
    assert sum(1 for tupla in colunas_df if tupla[1] == "TARDE") == 12
    assert sum(1 for tupla in colunas_df if tupla[1] == "INTEGRAL") == 12
    assert sum(1 for tupla in colunas_df if tupla[1] == "NOITE") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "PROGRAMAS E PROJETOS") == 10
    assert sum(1 for tupla in colunas_df if tupla[1] == "DIETA ESPECIAL - TIPO A") == 6
    assert sum(1 for tupla in colunas_df if tupla[1] == "DIETA ESPECIAL - TIPO B") == 4

    assert sum(1 for tupla in colunas_df if tupla[2] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Kit Lanche") == 1
    assert sum(1 for tupla in colunas_df if tupla[2] == "Lanche Emerg.") == 1

    assert sum(1 for tupla in colunas_df if tupla[2] == "Lanche") == 13
    assert sum(1 for tupla in colunas_df if tupla[2] == "Lanche 4h") == 13
    assert sum(1 for tupla in colunas_df if tupla[2] == "Refeição") == 11
    assert sum(1 for tupla in colunas_df if tupla[2] == "Sobremesa") == 7
    assert sum(1 for tupla in colunas_df if tupla[2] == "Refeições p/ Pagamento") == 9
    assert sum(1 for tupla in colunas_df if tupla[2] == "Sobremesas p/ Pagamento") == 9

    assert df.iloc[0].tolist() == [
        "EMEBS",
        "000329",
        "EMEBS TESTE",
        5.0,
        5.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        40.0,
        40.0,
        20.0,
        20.0,
        20.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        50.0,
        50.0,
        25.0,
        25.0,
        25.0,
    ]
    assert df.iloc[1].tolist() == [
        0.0,
        329.0,
        0.0,
        5.0,
        5.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        40.0,
        40.0,
        20.0,
        20.0,
        20.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        350.0,
        50.0,
        50.0,
        25.0,
        25.0,
        25.0,
    ]
