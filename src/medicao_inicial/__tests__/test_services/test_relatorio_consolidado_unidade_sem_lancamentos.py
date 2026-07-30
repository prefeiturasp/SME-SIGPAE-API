from io import BytesIO
import pandas as pd
import pytest
import openpyxl

from src.medicao_inicial.services.relatorio_consolidado_emei_emef import (
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
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