from io import BytesIO
import pandas as pd
import pytest
import openpyxl

from src.escola.models import PeriodoEscolar
from src.medicao_inicial.models import CategoriaMedicao
from src.medicao_inicial.services.relatorio_consolidado_emei_emef import (
    _define_filtro,
    _get_lista_alimentacoes_dietas,
    _get_total_pagamento,
    _processa_periodo_campo,
    _sort_and_merge,
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
    _get_lista_alimentacoes
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(solicitacao_sem_lancamento):
    colunas = get_alimentacoes_por_periodo([solicitacao_sem_lancamento])
    assert isinstance(colunas, list)
    assert len(colunas) == 2
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "Solicitações de Alimentação") == 0

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") ==0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") ==0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 1


def test_get_valores_tabela_unidade_emei(
    solicitacao_sem_lancamento
):
    colunas    = [('MANHA', 'total_refeicoes_pagamento'), ('MANHA', 'total_sobremesas_pagamento')]
    tipos_unidade = ["EMEI"]
    linhas = get_valores_tabela(
        [solicitacao_sem_lancamento], colunas, tipos_unidade, {}
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 5
    assert linhas[0] == ['EMEF', '123456', 'EMEF TESTE', 'SL', 'SL']
    
def test_insere_tabela_periodos_na_planilha_unidade_emei(
    solicitacao_sem_lancamento
):
    colunas    = [('MANHA', 'total_refeicoes_pagamento'), ('MANHA', 'total_sobremesas_pagamento')]
    linhas = [['EMEF', '123456', 'EMEF TESTE', 'SL', 'SL']]
    arquivo = BytesIO()
    aba = f"Relatório Consolidado {solicitacao_sem_lancamento.mes}-{ solicitacao_sem_lancamento.ano}"
    writer = pd.ExcelWriter(arquivo, engine="xlsxwriter")

    df = insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer)
    assert isinstance(df, pd.DataFrame)
    colunas_df = df.columns.tolist()
    assert len(colunas_df) == 5
    assert sum(1 for tupla in colunas_df if tupla[0] == "MANHA") == 2
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO A") == 0
    assert sum(1 for tupla in colunas_df if tupla[0] == "DIETA ESPECIAL - TIPO B") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Tipo") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Cód. EOL") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Unidade Escolar") == 1
    assert sum(1 for tupla in colunas_df if tupla[1] == "Kit Lanche") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche Emerg.") ==0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche") == 0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Lanche 4h") ==0
    assert sum(1 for tupla in colunas_df if tupla[1] == "Refeição") ==0
    assert (
        sum(
            1 for tupla in colunas_df if tupla[1] == "Total de Refeições para Pagamento"
        )
        == 1
    )
    assert sum(1 for tupla in colunas_df if tupla[1] == "Sobremesa") == 0
    assert (
        sum(
            1
            for tupla in colunas_df
            if tupla[1] == "Total de Sobremesas para Pagamento"
        )
        == 1
    )

    assert df.iloc[0].tolist() == ['EMEF', '123456', 'EMEF TESTE', 'SL', 'SL']
    assert df.iloc[1].tolist() == [0.0, 123456.0, 0.0, 0.0, 0.0]

def test_ajusta_layout_tabela(informacoes_excel_writer_sem_lancamentos):
    aba, writer, workbook, worksheet, df, arquivo = informacoes_excel_writer_sem_lancamentos
    ajusta_layout_tabela(workbook, worksheet, df)
    writer.close()
    workbook_openpyxl = openpyxl.load_workbook(arquivo)
    sheet = workbook_openpyxl[aba]
    merged_ranges = sheet.merged_cells.ranges
    assert len(merged_ranges) == 2
    esperados = {"A3:C3", "D3:E3"}
    assert {str(r) for r in merged_ranges} == esperados

    assert sheet["A3"].value is None
    assert sheet["C3"].value == None
    assert sheet["C3"].fill.fgColor.rgb == "00000000"
    assert sheet["D3"].value == "MANHA"
    assert sheet["D3"].fill.fgColor.rgb == "FF198459"
    assert sheet["E3"].value == None
    assert sheet["E3"].fill.fgColor.rgb == "00000000"
    workbook_openpyxl.close()
    
def test_get_lista_alimentacoes(solicitacao_sem_lancamento):
    medicoes = solicitacao_sem_lancamento.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]

    lista_alimentacoes_manha = _get_lista_alimentacoes(medicao_manha, "MANHA")
    assert isinstance(lista_alimentacoes_manha, list)
    assert lista_alimentacoes_manha == [
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

def test_get_lista_alimentacoes_dietas(solicitacao_sem_lancamento):
    medicoes = solicitacao_sem_lancamento.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    dieta_a = "DIETA ESPECIAL - TIPO A"
    dieta_a_enteral_restricao = (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    )
    dieta_b = "DIETA ESPECIAL - TIPO B"

    lista_dietas_a = _get_lista_alimentacoes_dietas(medicao_manha, dieta_a)
    assert isinstance(lista_dietas_a, list)
    assert len(lista_dietas_a) == 0

    lista_dietas_a_er = _get_lista_alimentacoes_dietas(
        medicao_manha, dieta_a_enteral_restricao
    )
    assert isinstance(lista_dietas_a_er, list)
    assert len(lista_dietas_a_er) == 0

    lista_dietas_b = _get_lista_alimentacoes_dietas(medicao_manha, dieta_b)
    assert isinstance(lista_dietas_b, list)
    assert len(lista_dietas_b) == 0
    
def test_sort_and_merge():
    periodos_alimentacoes = {
        "MANHA": [
            "total_refeicoes_pagamento",
            "total_sobremesas_pagamento",
        ],
    }
    dietas_alimentacoes = {}
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    assert isinstance(dict_periodos_dietas, dict)

    assert "DIETA ESPECIAL - TIPO A" not in dict_periodos_dietas
    assert "DIETA ESPECIAL - TIPO B" not in dict_periodos_dietas

    assert "MANHA" in dict_periodos_dietas
    assert len(dict_periodos_dietas["MANHA"]) == 2
    assert dict_periodos_dietas["MANHA"] == [
        "total_refeicoes_pagamento",
        "total_sobremesas_pagamento",
    ]

    assert "Solicitações de Alimentação" not in dict_periodos_dietas
    
def test_processa_periodo_campo_unidade_emef(solicitacao_sem_lancamento):
    valores_iniciais = [
        solicitacao_sem_lancamento.escola.tipo_unidade.iniciais,
        solicitacao_sem_lancamento.escola.codigo_eol,
        solicitacao_sem_lancamento.escola.nome,
    ]
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    manha_refeicao = _processa_periodo_campo(
        solicitacao_sem_lancamento,
        "MANHA",
        "refeicao",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
        True,
    )
    assert isinstance(manha_refeicao, list)
    assert len(manha_refeicao) == 4
    assert manha_refeicao == ['EMEF', '123456', 'EMEF TESTE', 'SL']

    solicitacao_kit_lanche = _processa_periodo_campo(
        solicitacao_sem_lancamento,
        "Solicitações de Alimentação",
        "kit_lanche",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
        True,
    )
    assert isinstance(solicitacao_kit_lanche, list)
    assert len(solicitacao_kit_lanche) == 5
    assert solicitacao_kit_lanche == ['EMEF', '123456', 'EMEF TESTE', 'SL', 'SL']

    dieta_a_lanche = _processa_periodo_campo(
        solicitacao_sem_lancamento,
        "DIETA ESPECIAL - TIPO A",
        "lanche_4h",
        valores_iniciais,
        dietas_especiais,
        periodos_escolares,
        True,
    )
    assert isinstance(dieta_a_lanche, list)
    assert len(dieta_a_lanche) == 6
    assert dieta_a_lanche == ['EMEF', '123456', 'EMEF TESTE', 'SL', 'SL', 'SL']

def test_define_filtro(solicitacao_sem_lancamento):
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)

    manha = _define_filtro("MANHA", dietas_especiais, periodos_escolares)
    assert isinstance(manha, dict)
    assert "grupo__nome" not in manha
    assert "periodo_escolar__nome" in manha
    assert manha["periodo_escolar__nome"] == "MANHA"

    dieta_especial = _define_filtro(
        "DIETA ESPECIAL - TIPO A", dietas_especiais, periodos_escolares
    )
    assert isinstance(dieta_especial, dict)
    assert "grupo__nome" not in dieta_especial
    assert "periodo_escolar__nome" in dieta_especial
    assert "grupo__nome__in" not in dieta_especial
    assert dieta_especial["periodo_escolar__nome"] == "DIETA ESPECIAL - TIPO A"

    solicitacao = _define_filtro(
        "Solicitações de Alimentação", dietas_especiais, periodos_escolares
    )
    assert isinstance(solicitacao, dict)
    assert "periodo_escolar__nome" not in solicitacao
    assert "grupo__nome" in solicitacao
    assert solicitacao["grupo__nome"] == "Solicitações de Alimentação"
    


def test_get_total_pagamento_unidade_emef(solicitacao_sem_lancamento):
    medicoes = solicitacao_sem_lancamento.medicoes.all().order_by(
        "periodo_escolar__nome"
    )
    medicao_manha = medicoes[0]
    tipos_unidades = "EMEF"
    total_refeicao = _get_total_pagamento(
        medicao_manha, "total_refeicoes_pagamento", tipos_unidades
    )
    assert total_refeicao == 0
    total_sobremesa = _get_total_pagamento(
        medicao_manha, "total_sobremesas_pagamento", tipos_unidades
    )
    assert total_sobremesa == 0