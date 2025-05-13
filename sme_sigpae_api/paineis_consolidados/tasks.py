import datetime
import io
import logging
import re

import numpy as np
from celery import shared_task
from django.template.loader import render_to_string

from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.escola.models import Escola, Lote, TipoUnidadeEscolar
from sme_sigpae_api.paineis_consolidados.api.serializers import (
    SolicitacoesExportXLSXSerializer,
)
from sme_sigpae_api.paineis_consolidados.models import (
    MoldeConsolidado,
    SolicitacoesCODAE,
)

from ..perfil.models import Usuario
from ..relatorios.utils import html_to_pdf_file
from .api import constants

logger = logging.getLogger(__name__)


def build_subtitulo(
    data,
    status_,
    queryset,
    lotes,
    tipos_solicitacao,
    tipos_unidade,
    unidades_educacionais,
):
    subtitulo = f"Total de Solicitações {status_}: {len(queryset)}"

    nomes_lotes = ", ".join([lote.nome for lote in Lote.objects.filter(uuid__in=lotes)])
    subtitulo += f" | Lote(s): {nomes_lotes}" if nomes_lotes else ""

    de_para_tipos_solicitacao = {
        "INC_ALIMENTA": "Inclusão de Alimentação",
        "ALT_CARDAPIO": "Alteração do tipo de Alimentação",
        "KIT_LANCHE_UNIFICADO": "Kit Lanche Unificado",
        "KIT_LANCHE_AVULSA": "Kit Lanche Passeio",
        "INV_CARDAPIO": "Inversão de dia de Cardápio",
        "SUSP_ALIMENTACAO": "Suspensão de Alimentação",
    }
    nomes_tipos_solicitacao = ", ".join(
        [de_para_tipos_solicitacao[tipo_sol] for tipo_sol in tipos_solicitacao]
    )
    subtitulo += (
        f" | Tipo(s) de solicitação(ões): {nomes_tipos_solicitacao}"
        if nomes_tipos_solicitacao
        else ""
    )

    nomes_tipos_unidade = ", ".join(
        [
            tipo_unidade.iniciais
            for tipo_unidade in TipoUnidadeEscolar.objects.filter(
                uuid__in=tipos_unidade
            )
        ]
    )
    subtitulo += (
        f" | Tipo(s) unidade(s): {nomes_tipos_unidade}" if nomes_tipos_unidade else ""
    )

    nomes_ues = ", ".join(
        [
            escola.nome
            for escola in Escola.objects.filter(uuid__in=unidades_educacionais)
        ]
    )
    subtitulo += f" | Unidade(s) educacional(is): {nomes_ues}" if nomes_ues else ""

    data_inicial = data.get("de")
    subtitulo += f" | Data inicial: {data_inicial}" if data_inicial else ""

    data_final = data.get("ate")
    subtitulo += f" | Data final: {data_final}" if data_final else ""

    subtitulo += f' | Data de Extração do Relatório: {datetime.date.today().strftime("%d/%m/%Y")}'

    return subtitulo


def formata_data(model_obj):
    data_inicial = model_obj.data_inicial.strftime("%d/%m/%Y")
    data_final = model_obj.data_final.strftime("%d/%m/%Y")
    return f"{data_inicial} - {data_final}"


def cria_tipos_alimentacao(qt_periodo):
    tipos_alimentacao = [tipo.nome for tipo in qt_periodo.tipos_alimentacao.all()]
    return ", ".join(tipos_alimentacao)


def cria_nova_linha(df, index, model_obj, qt_periodo, observacoes):
    nova_linha = df.iloc[index].copy()
    nova_linha["data_evento"] = formata_data(model_obj)
    nova_linha["dia_semana"] = qt_periodo.dias_semana_display()
    nova_linha["periodo_inclusao"] = qt_periodo.periodo_escolar.nome
    nova_linha["observacoes"] = (
        qt_periodo.cancelado_justificativa if qt_periodo.cancelado else observacoes
    )
    nova_linha["tipo_alimentacao"] = cria_tipos_alimentacao(qt_periodo)
    nova_linha["numero_alunos"] = qt_periodo.numero_alunos
    return nova_linha


def novas_linhas_inc_continua_e_kit_lanche(df, queryset, instituicao):
    novas_linhas, lista_uuids = [], []
    for index, solicitacao in enumerate(queryset):
        model_obj = solicitacao.get_raw_model.objects.get(uuid=solicitacao.uuid)
        if solicitacao.tipo_doc == "INC_ALIMENTA_CONTINUA":
            observacoes = re.sub(
                r"<p>|</p>", "", re.sub(r"</p>,\s*<p>", "::", model_obj.observacoes)
            ).split("::")
            for idx, qt_periodo in enumerate(model_obj.quantidades_periodo.all()):
                obs_periodo = (
                    observacoes[idx] if observacoes and len(observacoes) > idx else ""
                )
                nova_linha = cria_nova_linha(
                    df, index, model_obj, qt_periodo, obs_periodo
                )
                novas_linhas.append(nova_linha)
                lista_uuids.append(solicitacao)
        elif "KIT_LANCHE" in solicitacao.tipo_doc:
            nova_linha = df.iloc[index].copy()
            nova_linha["quantidade_alimentacoes"] = str(
                model_obj.quantidade_alimentacoes
            )
            if solicitacao.tipo_doc == "KIT_LANCHE_UNIFICADA" and isinstance(
                instituicao, Escola
            ):
                nova_linha["quantidade_alimentacoes"] = str(
                    model_obj.total_kit_lanche_escola(instituicao.uuid)
                )
            novas_linhas.append(nova_linha)
            lista_uuids.append(solicitacao)
        else:
            linha = df.iloc[index].copy()
            novas_linhas.append(linha)
            lista_uuids.append(solicitacao)
    return novas_linhas, lista_uuids


def get_formats(workbook):
    merge_format = workbook.add_format(
        {"align": "center", "bg_color": "#a9d18e", "border_color": "#198459"}
    )
    merge_format.set_align("vcenter")
    merge_format.set_bold()

    cell_format = workbook.add_format()
    cell_format.set_text_wrap()
    cell_format.set_align("vcenter")
    cell_format.set_bold()

    single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})
    return merge_format, cell_format, single_cell_format


def nomes_colunas(worksheet, status_, LINHAS, COLUNAS, single_cell_format):
    map_data = {
        "Autorizadas": "Data de Autorização",
        "Canceladas": "Data de Cancelamento",
        "Negadas": "Data de Negação",
        "Recebidas": "Data de Autorização",
    }
    headers = [
        "N",
        "Lote",
        "Terceirizada" if status_ == "Recebidas" else "Unidade Educacional",
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
        map_data[status_],
    ]
    for index, header in enumerate(headers):
        worksheet.write(
            LINHAS[constants.ROW_IDX_HEADER_CAMPOS],
            COLUNAS[index],
            header,
            single_cell_format,
        )


def aplica_fundo_amarelo_tipo1(
    df, worksheet, workbook, solicitacao, model_obj, LINHAS, COLUNAS, index
):
    if solicitacao.tipo_doc in [
        "INC_ALIMENTA_CEMEI",
        "INC_ALIMENTA_CEI",
        "INC_ALIMENTA",
        "ALT_CARDAPIO",
        "ALT_CARDAPIO_CEMEI",
        "SUSP_ALIMENTACAO",
    ]:
        if model_obj.existe_dia_cancelado or model_obj.status == "ESCOLA_CANCELOU":
            worksheet.write(
                LINHAS[constants.ROW_IDX_HEADER_CAMPOS] + 1 + index,
                COLUNAS[constants.COL_IDX_DATA_EVENTO],
                df.values[LINHAS[constants.ROW_IDX_HEADER_CAMPOS] + index][
                    COLUNAS[constants.COL_IDX_DATA_EVENTO]
                ],
                workbook.add_format({"align": "left", "bg_color": "yellow"}),
            )


def aplica_fundo_amarelo_tipo2(
    df, worksheet, workbook, solicitacao, model_obj, LINHAS, COLUNAS, index, idx
):
    if solicitacao.tipo_doc == "INC_ALIMENTA_CONTINUA":
        qts_periodos = model_obj.quantidades_periodo.all()
        if idx < len(qts_periodos):
            qt_periodo = qts_periodos[idx]
            if qt_periodo.cancelado:
                worksheet.write(
                    LINHAS[constants.ROW_IDX_HEADER_CAMPOS] + 1 + index,
                    COLUNAS[constants.COL_IDX_OBSERVACOES],
                    df.values[LINHAS[constants.ROW_IDX_HEADER_CAMPOS] + index][
                        COLUNAS[constants.COL_IDX_OBSERVACOES]
                    ],
                    workbook.add_format({"align": "left", "bg_color": "yellow"}),
                )
            idx += 1
    return idx


def aplica_fundo_amarelo_canceladas(
    df, worksheet, workbook, lista_uuids, LINHAS, COLUNAS
):
    df.reset_index(drop=True, inplace=True)
    previous_solicitacao = None
    idx = 0
    for index, solicitacao in enumerate(lista_uuids):
        model_obj = solicitacao.get_raw_model.objects.get(uuid=solicitacao.uuid)

        if previous_solicitacao != solicitacao:
            idx = 0
            previous_solicitacao = solicitacao

        aplica_fundo_amarelo_tipo1(
            df, worksheet, workbook, solicitacao, model_obj, LINHAS, COLUNAS, index
        )
        idx = aplica_fundo_amarelo_tipo2(
            df, worksheet, workbook, solicitacao, model_obj, LINHAS, COLUNAS, index, idx
        )


def build_xlsx(
    output,
    serializer,
    queryset,
    data,
    lotes,
    tipos_solicitacao,
    tipos_unidade,
    unidades_educacionais,
    instituicao,
):
    ALTURA_COLUNA_30 = 30
    ALTURA_COLUNA_50 = 50

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

    import pandas as pd

    with pd.ExcelWriter(output, engine="xlsxwriter") as xlwriter:
        df = pd.DataFrame(serializer.data)

        novas_colunas = ["dia_semana", "periodo_inclusao", "tipo_alimentacao"]
        for i, nova_coluna in enumerate(novas_colunas):
            df.insert(constants.COL_IDX_DATA_EVENTO + i, nova_coluna, "-")

        df.insert(constants.COL_IDX_NUMERO_DE_ALUNOS, "quantidade_alimentacoes", "-")
        novas_linhas, lista_uuids = novas_linhas_inc_continua_e_kit_lanche(
            df, queryset, instituicao
        )
        df = pd.DataFrame(novas_linhas)
        df.reset_index(drop=True, inplace=True)

        df.insert(0, "N", range(1, len(df) + 1))
        df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
        for _ in range(3):
            df = pd.concat([df_auxiliar, df], ignore_index=True)

        df["N"] = df["N"].apply(lambda x: str(int(x or "0")) if pd.notnull(x) else "")
        df["numero_alunos"] = df["numero_alunos"].apply(
            lambda x: str(int(x or "0")) if pd.notnull(x) else ""
        )

        status_map = {"Em_andamento": "Recebidas"}
        status_ = data.get("status").capitalize()
        status_ = status_map.get(status_, status_[:-2] + "as")
        titulo = f"Relatório de Solicitações de Alimentação {status_}"

        df.to_excel(xlwriter, f"Relatório - {status_}", index=False)
        workbook = xlwriter.book
        worksheet = xlwriter.sheets[f"Relatório - {status_}"]
        worksheet.set_row(LINHAS[0], ALTURA_COLUNA_50)
        worksheet.set_row(LINHAS[1], ALTURA_COLUNA_30)

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

        merge_format, cell_format, single_cell_format = get_formats(workbook)
        len_cols = len(df.columns) - 1
        worksheet.merge_range(0, 0, 0, len_cols, titulo, merge_format)

        subtitulo = build_subtitulo(
            data,
            status_,
            queryset,
            lotes,
            tipos_solicitacao,
            tipos_unidade,
            unidades_educacionais,
        )
        worksheet.merge_range(LINHAS[1], 0, LINHAS[2], len_cols, subtitulo, cell_format)
        worksheet.insert_image(
            "A1", "sme_sigpae_api/static/images/logo-sigpae-light.png"
        )

        nomes_colunas(worksheet, status_, LINHAS, COLUNAS, single_cell_format)

        aplica_fundo_amarelo_canceladas(
            df, worksheet, workbook, lista_uuids, LINHAS, COLUNAS
        )
    output.seek(0)


def build_pdf(lista_solicitacoes_dict, status):
    html_string = render_to_string(
        "relatorio_solicitacoes_alimentacao.html",
        {
            "solicitacoes": lista_solicitacoes_dict,
            "total_solicitacoes": len(lista_solicitacoes_dict),
            "data_extracao_relatorio": datetime.date.today().strftime("%d/%m/%Y"),
            "status": status,
            "status_formatado": "".join(
                letra for letra in status.title() if not letra.isspace()
            ),
        },
    )
    return html_to_pdf_file(html_string, "relatorio_solicitacoes_alimentacao.pdf", True)


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_xls_relatorio_solicitacoes_alimentacao_async(
    user,
    nome_arquivo,
    data,
    uuids,
    lotes,
    tipos_solicitacao,
    tipos_unidade,
    unidades_educacionais,
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    try:
        instituicao = Usuario.objects.get(username=user).vinculo_atual.instituicao
        queryset = SolicitacoesCODAE.objects.filter(uuid__in=uuids).order_by(
            "lote_nome", "escola_nome", "terceirizada_nome"
        )
        # remove duplicados
        aux = []
        sem_uuid_repetido = []
        for resultado in queryset:
            if resultado.uuid not in aux:
                aux.append(resultado.uuid)
                sem_uuid_repetido.append(resultado)

        status_ = data.get("status")
        serializer = SolicitacoesExportXLSXSerializer(
            sem_uuid_repetido,
            context={"instituicao": instituicao, "status": status_.upper()},
            many=True,
        )
        output = io.BytesIO()
        build_xlsx(
            output,
            serializer,
            sem_uuid_repetido,
            data,
            lotes,
            tipos_solicitacao,
            tipos_unidade,
            unidades_educacionais,
            instituicao,
        )
        atualiza_central_download(obj_central_download, nome_arquivo, output.read())
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gera_pdf_relatorio_solicitacoes_alimentacao_async(
    user, nome_arquivo, data, uuids, status
):
    logger.info(f"x-x-x-x Iniciando a geração do arquivo {nome_arquivo} x-x-x-x")
    obj_central_download = gera_objeto_na_central_download(
        user=user, identificador=nome_arquivo
    )
    tipo_doc = 0
    uuid = 1

    label_data = {
        "AUTORIZADOS": " de Autorização",
        "CANCELADOS": " de Cancelamento",
        "NEGADOS": " de Negação",
        "RECEBIDAS": " de Autorização",
    }
    property_data = {
        "AUTORIZADOS": "data_autorizacao",
        "CANCELADOS": "data_cancelamento",
        "NEGADOS": "data_negacao",
        "RECEBIDAS": "data_autorizacao",
    }

    try:
        instituicao = Usuario.objects.get(username=user).vinculo_atual.instituicao
        solicitacoes = SolicitacoesCODAE.objects.filter(uuid__in=uuids).order_by(
            "lote_nome", "escola_nome", "terceirizada_nome"
        )
        solicitacoes = set(
            list(solicitacoes.values_list("tipo_doc", "uuid").distinct())
        )
        lista_solicitacoes_dict = []
        for solicitacao in solicitacoes:
            class_name = MoldeConsolidado.get_class_name(solicitacao[tipo_doc])
            _solicitacao = class_name.objects.get(uuid=solicitacao[uuid])
            lista_solicitacoes_dict.append(
                _solicitacao.solicitacao_dict_para_relatorio(
                    label_data[status],
                    getattr(_solicitacao, property_data[status]),
                    instituicao,
                )
            )
        lista_solicitacoes_dict = sorted(
            lista_solicitacoes_dict,
            key=lambda solicitacao_: (
                solicitacao_["lote"],
                solicitacao_["unidade_educacional"],
            ),
        )
        arquivo = build_pdf(lista_solicitacoes_dict, status)
        atualiza_central_download(obj_central_download, nome_arquivo, arquivo)
    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    logger.info(f"x-x-x-x Finaliza a geração do arquivo {nome_arquivo} x-x-x-x")
