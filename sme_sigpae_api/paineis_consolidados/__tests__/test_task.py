import io
import uuid
from datetime import datetime
from unittest.mock import Mock

import pandas as pd
import pytest
import xlsxwriter
from django.db.models.query import QuerySet

from sme_sigpae_api.paineis_consolidados.api import constants
from sme_sigpae_api.paineis_consolidados.api.serializers import (
    SolicitacoesExportXLSXSerializer,
)
from sme_sigpae_api.paineis_consolidados.tasks import (
    build_pdf,
    build_xlsx,
    cria_nova_linha,
    gera_pdf_relatorio_solicitacoes_alimentacao_async,
    gera_xls_relatorio_solicitacoes_alimentacao_async,
    get_formats,
    nomes_colunas,
)
from sme_sigpae_api.relatorios.utils import extrair_texto_de_pdf

pytestmark = pytest.mark.django_db


def test_xls_relatorio_status(users_diretor_escola):
    usuario = users_diretor_escola[5]
    uuids = ["7fa6e609-db33-48e1-94ea-6d5a0c07935c"]
    lotes = []
    tipos_solicitacao = []
    tipos_unidade = []
    unidades_educacionais = []
    request_data = {
        "status": "CANCELADOS",
        "tipos_solicitacao": ["SUSP_ALIMENTACAO", "INC_ALIMENTA"],
        "de": "01/01/2025",
        "ate": "28/02/2025",
    }
    resultado = gera_xls_relatorio_solicitacoes_alimentacao_async.delay(
        user=usuario.username,
        nome_arquivo="relatorio_solicitacoes_alimentacao.xlsx",
        data=request_data,
        uuids=uuids,
        lotes=lotes,
        tipos_solicitacao=tipos_solicitacao,
        tipos_unidade=tipos_unidade,
        unidades_educacionais=unidades_educacionais,
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True


def test_pdf_relatorio_status(users_diretor_escola):
    usuario = users_diretor_escola[5]
    uuids = ["7fa6e609-db33-48e1-94ea-6d5a0c07935c"]
    request_data = {
        "status": "CANCELADOS",
        "tipos_solicitacao": ["SUSP_ALIMENTACAO", "INC_ALIMENTA"],
        "de": "01/01/2025",
        "ate": "28/02/2025",
    }
    resultado = gera_pdf_relatorio_solicitacoes_alimentacao_async.delay(
        user=usuario.username,
        nome_arquivo="relatorio_solicitacoes_alimentacao.pdf",
        data=request_data,
        uuids=uuids,
        status=request_data.get("status", None),
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True


# def test_build_xlsx(users_diretor_escola, solicitacoes_export_excel_serializers):

#     usuario = users_diretor_escola[5]
#     instituicao = usuario.vinculo_atual.instituicao
#     uuids = ["7fa6e609-db33-48e1-94ea-6d5a0c07935c"]
#     lotes = []
#     tipos_solicitacao = []
#     tipos_unidade = []
#     unidades_educacionais = []
#     request_data = {
#         "status": "CANCELADOS",
#         "tipos_solicitacao": ["SUSP_ALIMENTACAO", "INC_ALIMENTA"],
#         "de": "01/01/2025",
#         "ate": "28/02/2025",
#     }
#     serializer = SolicitacoesExportXLSXSerializer(
#         [solicitacoes_export_excel_serializers],
#         context={"instituicao": instituicao, "status": request_data.get("status").upper()},
#         many=True,
#     )
#     output = io.BytesIO()
#     build_xlsx(
#         output,
#         serializer,
#         uuids,
#         request_data,
#         lotes,
#         tipos_solicitacao,
#         tipos_unidade,
#         unidades_educacionais,
#         instituicao,
#     )
#     pass


def test_cria_nova_linha():
    pass
    # model_obj = Mock()
    # qt_periodo = Mock()
    # qt_periodo.dias_semana_display.return_value = "Segunda-feira"
    # qt_periodo.periodo_escolar.nome = "2025 - Primeiro Semestre"
    # qt_periodo.cancelado = False
    # qt_periodo.cancelado_justificativa = "Cancelado por motivo X"
    # qt_periodo.numero_alunos = 30
    # qt_periodo.tipos_alimentacao = QuerySet()

    # observacoes = "Nenhuma observação"

    # # def mock_formata_data(model):
    # #     return "20/01/2025"

    # # def mock_cria_tipos_alimentacao(periodo):
    # #     return ["Café da manhã", "Almoço"]

    # # # Patching das funções auxiliares
    # # global formata_data, cria_tipos_alimentacao
    # # formata_data = mock_formata_data
    # # cria_tipos_alimentacao = mock_cria_tipos_alimentacao

    # mock_dataframe = pd.DataFrame(
    #     [
    #         {"col1": "value1", "col2": "value2"},
    #         {"col1": "value3", "col2": "value4"},
    #     ]
    # )

    # index = 0

    # # Chamada da função
    # nova_linha = cria_nova_linha(mock_dataframe, index, model_obj, qt_periodo, observacoes)

    # # Verificações
    # assert nova_linha["data_evento"] == "20/01/2025"
    # assert nova_linha["dia_semana"] == "Segunda-feira"
    # assert nova_linha["periodo_inclusao"] == "2025 - Primeiro Semestre"
    # assert nova_linha["observacoes"] == "Nenhuma observação"
    # assert nova_linha["tipo_alimentacao"] == ["Café da manhã", "Almoço"]
    # assert nova_linha["numero_alunos"] == 30


def test_cria_nova_linha_para_alimentacao_continua():
    pass


def test_cria_nova_linha_para_kit_lanche():
    pass


def test_novas_linhas_inc_continua_e_kit_lanche():
    pass


def test_get_formats():
    output_file = "/tmp/test.xlsx"
    xlwriter = pd.ExcelWriter(output_file, engine="xlsxwriter")
    workbook = xlwriter.book
    bg_color = "#a9d18e"
    border_color = "#198459"

    merge_format, cell_format, single_cell_format = get_formats(workbook)

    assert merge_format.right_color == border_color
    assert merge_format.bottom_color == border_color
    assert merge_format.left_color == border_color
    assert merge_format.top_color == border_color
    assert merge_format.bg_color == bg_color
    assert merge_format.bold == True

    assert cell_format.bold == True
    assert cell_format.text_wrap == True

    assert single_cell_format.bg_color == bg_color

    workbook.close()


def test_build_subtitulo():
    pass


def test_nomes_colunas():
    LINHAS = [
        constants.ROW_IDX_TITULO_ARQUIVO,
        constants.ROW_IDX_FILTROS_PT1,
        constants.ROW_IDX_FILTROS_PT2,
        constants.ROW_IDX_HEADER_CAMPOS,
    ]
    COLUNAS = [
        constants.COL_IDX_N,
        constants.COL_IDX_LOTE,
        constants.COL_IDX_UNIDADE_EDUCACIONAL,
        constants.COL_IDX_TIPO_DE_SOLICITACAO,
        constants.COL_IDX_ID_SOLICITACAO,
        constants.COL_IDX_DATA_EVENTO,
        constants.COL_IDX_DIA_DA_SEMANA,
        constants.COL_IDX_PERIODO,
        constants.COL_IDX_TIPO_DE_ALIMENTACAO,
        constants.COL_IDX_TIPO_DE_ALTERACAO,
        constants.COL_IDX_NUMERO_DE_ALUNOS,
        constants.COL_IDX_NUMERO_TOTAL_KITS,
        constants.COL_IDX_OBSERVACOES,
        constants.COL_IDX_DATA_LOG,
    ]
    output_file = "/tmp/test.xlsx"
    nome_aba = "Relatório"
    xlwriter = pd.ExcelWriter(output_file, engine="xlsxwriter")
    workbook = xlwriter.book
    worksheet = workbook.add_worksheet(nome_aba)
    xlwriter.sheets["Relatório"] = worksheet
    worksheet.set_row(LINHAS[0], 50)
    worksheet.set_row(LINHAS[1], 30)
    columns_width = {
        "A:A": 5,
        "B:B": 8,
        "C:C": 40,
        "D:D": 30,
        "E:E": 15,
        "F:G": 30,
        "H:H": 10,
        "I:J": 30,
        "K:K": 13,
        "L:L": 15,
        "M:M": 30,
        "N:N": 20,
    }
    for col, width in columns_width.items():
        worksheet.set_column(col, width)
    single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})
    nomes_colunas(worksheet, "Canceladas", LINHAS, COLUNAS, single_cell_format)

    assert len(worksheet.col_sizes) == len(COLUNAS)
    assert len(worksheet.row_sizes) == 2
    assert worksheet.name == nome_aba

    xlwriter.close()


def test_aplica_fundo_amarelo_canceladas():
    pass


def test_aplica_fundo_amarelo_tipo1():
    pass


def test_aplica_fundo_amarelo_tipo2():
    pass


def test_build_pdf():
    pdf_cancelados = build_pdf([], "CANCELADOS")
    assert isinstance(pdf_cancelados, bytes)

    texto = extrair_texto_de_pdf(pdf_cancelados).lower()
    assert "Total de Solicitações Cancelados:  0".lower() in texto
    assert "SIGPAE - RELATÓRIO DE solicitações de alimentação".lower() in texto
    assert datetime.now().strftime("%d/%m/%Y") in texto
    assert texto.count("cancelados") == 2

    pdf_autorizados = build_pdf([], "AUTORIZADOS")
    assert isinstance(pdf_autorizados, bytes)

    texto = extrair_texto_de_pdf(pdf_autorizados).lower()
    assert "Total de Solicitações autorizados:  0".lower() in texto
    assert "SIGPAE - RELATÓRIO DE solicitações de alimentação".lower() in texto
    assert datetime.now().strftime("%d/%m/%Y") in texto
    assert texto.count("autorizados") == 2
