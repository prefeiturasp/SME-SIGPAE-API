import io
import uuid
from datetime import datetime

import pandas as pd
import pytest
from openpyxl import load_workbook

from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.inclusao_alimentacao.models import GrupoInclusaoAlimentacaoNormal
from sme_sigpae_api.paineis_consolidados.api import constants
from sme_sigpae_api.paineis_consolidados.api.serializers import (
    SolicitacoesExportXLSXSerializer,
)
from sme_sigpae_api.paineis_consolidados.models import SolicitacoesCODAE
from sme_sigpae_api.paineis_consolidados.tasks import (
    build_pdf,
    build_xlsx,
    cria_nova_linha,
    gera_pdf_relatorio_solicitacoes_alimentacao_async,
    gera_xls_relatorio_solicitacoes_alimentacao_async,
    get_formats,
    nomes_colunas,
    novas_linhas_inc_continua_e_kit_lanche,
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


def test_build_xlsx(
    users_diretor_escola,
    grupo_inclusao_alimentacao_normal_factory,
    log_solicitacoes_usuario_factory,
    quantidade_por_periodo_factory,
    inclusao_alimentacao_normal_factory,
):
    usuario = users_diretor_escola[5]
    instituicao = usuario.vinculo_atual.instituicao
    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=instituicao,
            rastro_lote=instituicao.lote,
            rastro_dre=instituicao.diretoria_regional,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.ESCOLA_CANCELOU,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14", grupo_inclusao=grupo_inclusao_alimentacao_normal
    )
    quantidade_por_periodo_factory.create(
        grupo_inclusao_normal=grupo_inclusao_alimentacao_normal
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
        usuario=usuario,
    )
    output = io.BytesIO()
    data = {
        "status": "CANCELADOS",
        "tipos_solicitacao": ["SUSP_ALIMENTACAO", "INC_ALIMENTA"],
        "de": "01/01/2025",
        "ate": "28/02/2025",
    }
    # SolicitacoesCODAE.objects.values_list('uuid', flat=True)
    sem_uuids_repetido = [s for s in SolicitacoesCODAE.objects.all()]
    serializer = SolicitacoesExportXLSXSerializer(
        sem_uuids_repetido,
        context={"instituicao": instituicao, "status": data.get("status").upper()},
        many=True,
    )

    lotes = []
    tipos_solicitacao = ["SUSP_ALIMENTACAO", "INC_ALIMENTA"]
    tipos_unidade = []
    unidades_educacionais = []
    build_xlsx(
        output,
        serializer,
        sem_uuids_repetido,
        data,
        lotes,
        tipos_solicitacao,
        tipos_unidade,
        unidades_educacionais,
        instituicao,
    )
    workbook = load_workbook(output)
    sheet = workbook[f"Relatório - Canceladas"]
    rows = list(sheet.iter_rows(values_only=True))

    assert rows[0] == (
        "Relatório de Solicitações de Alimentação Canceladas",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert rows[1] == (
        "Total de Solicitações Canceladas: 11 | Tipo(s) de solicitação(ões): Suspensão de Alimentação, Inclusão de Alimentação | Data inicial: 01/01/2025 | Data final: 28/02/2025 | Data de Extração do Relatório: 21/01/2025",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert rows[3] == (
        "N",
        "Lote",
        "Unidade Educacional",
        "Tipo de Solicitação",
        "ID da Solicitação",
        "Data do Evento",
        "Dia da semana",
        "Período",
        "Tipo de Alimentação",
        "Tipo de Alteração",
        "Nª de Alunos",
        "N° total de Kits",
        "Observações",
        "Data de Cancelamento",
    )
    assert rows[4][3] == "Inclusão de Alimentação"
    assert rows[4][5] == "14/01/2025"
    assert rows[4][12] == "cancelado"


def test_cria_nova_linha(
    users_diretor_escola,
    grupo_inclusao_alimentacao_normal_factory,
    log_solicitacoes_usuario_factory,
    quantidade_por_periodo_factory,
    inclusao_alimentacao_normal_factory,
):
    usuario = users_diretor_escola[5]
    instituicao = usuario.vinculo_atual.instituicao

    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=instituicao,
            rastro_lote=instituicao.lote,
            rastro_dre=instituicao.diretoria_regional,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.ESCOLA_CANCELOU,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14", grupo_inclusao=grupo_inclusao_alimentacao_normal
    )
    quantidade_por_periodo_factory.create(
        grupo_inclusao_normal=grupo_inclusao_alimentacao_normal
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
        usuario=usuario,
    )
    queryset = [s for s in SolicitacoesCODAE.objects.all()]
    serializer = SolicitacoesExportXLSXSerializer(
        queryset,
        context={"instituicao": instituicao, "status": "CANCELADOS"},
        many=True,
    )
    df = pd.DataFrame(serializer.data)
    novas_colunas = ["dia_semana", "periodo_inclusao", "tipo_alimentacao"]
    for i, nova_coluna in enumerate(novas_colunas):
        df.insert(constants.COL_IDX_DATA_EVENTO + i, nova_coluna, "-")
    df.insert(constants.COL_IDX_NUMERO_DE_ALUNOS, "quantidade_alimentacoes", "-")

    solicitacao = queryset[0]
    model_obj = solicitacao.get_raw_model.objects.get(uuid=solicitacao.uuid)
    qt_periodo = model_obj.quantidades_periodo.all()[0]
    # TODO: O ERRO ESTÁ AQUI
    nova_linha = cria_nova_linha(df, 0, model_obj, qt_periodo, model_obj.observacoes)

    # for index, solicitacao in enumerate(queryset):
    #     model_obj = solicitacao.get_raw_model.objects.get(uuid=solicitacao.uuid)
    #     nova_linha = cria_nova_linha(
    #         df, 0, model_obj, qt_periodo, model_obj.observacoe
    #     )
    assert nova_linha["data_evento"] == "20/01/2025"
    assert nova_linha["dia_semana"] == "Segunda-feira"
    assert nova_linha["periodo_inclusao"] == "2025 - Primeiro Semestre"
    assert nova_linha["observacoes"] == "Nenhuma observação"
    assert nova_linha["tipo_alimentacao"] == ["Café da manhã", "Almoço"]
    assert nova_linha["numero_alunos"] == 30


def test_novas_linhas_inc_continua_e_kit_lanche(users_diretor_escola):
    usuario = users_diretor_escola[5]
    instituicao = usuario.vinculo_atual.instituicao
    queryset = [s for s in SolicitacoesCODAE.objects.all()]
    serializer = SolicitacoesExportXLSXSerializer(
        queryset,
        context={"instituicao": instituicao, "status": "CANCELADOS"},
        many=True,
    )

    df = pd.DataFrame(serializer.data)
    novas_colunas = ["dia_semana", "periodo_inclusao", "tipo_alimentacao"]
    for i, nova_coluna in enumerate(novas_colunas):
        df.insert(constants.COL_IDX_DATA_EVENTO + i, nova_coluna, "-")
    df.insert(constants.COL_IDX_NUMERO_DE_ALUNOS, "quantidade_alimentacoes", "-")
    novas_linhas, lista_uuids = novas_linhas_inc_continua_e_kit_lanche(
        df, queryset, instituicao
    )

    assert isinstance(novas_linhas, list)
    for linha in novas_linhas:
        assert isinstance(linha, pd.Series)

    assert isinstance(lista_uuids, list)
    for lu in lista_uuids:
        assert isinstance(lu, SolicitacoesCODAE)


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
