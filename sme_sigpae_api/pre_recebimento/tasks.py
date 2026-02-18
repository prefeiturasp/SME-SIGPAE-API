import io
import logging
from datetime import date

import pandas as pd
from celery import shared_task
from django.template.loader import render_to_string
from workalendar.america import BrazilSaoPauloCity

from sme_sigpae_api.dados_comuns.constants import TRADUCOES_FERIADOS
from sme_sigpae_api.dados_comuns.utils import (
    atualiza_central_download,
    atualiza_central_download_com_erro,
    gera_objeto_na_central_download,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.helpers import (
    converter_para_numero,
    filtrar_etapas,
    totalizador_relatorio_cronograma,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.api.serializers.serializers import (
    CronogramaRelatorioSerializer,
)
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    InterrupcaoProgramadaEntrega,
)
from sme_sigpae_api.relatorios.utils import html_to_pdf_file

logger = logging.getLogger(__name__)


def _preparar_dataframe_cronogramas(dados):
    """Prepara o DataFrame com os dados dos cronogramas."""
    if not dados:
        return pd.DataFrame(), []

    df = pd.DataFrame(dados)
    df.insert(13, "unidade_etapa", value=df.iloc[:, 5])

    if "data_programada" in df.columns:
        df["data_programada"] = pd.to_datetime(
            df["data_programada"], format="%d/%m/%Y", errors="coerce"
        ).dt.normalize()

    indices_leve_leite = df.index[df["programa_leve_leite"]].tolist()
    df = df.drop(columns=["programa_leve_leite"])

    return df, indices_leve_leite


def _aplicar_estilos_leve_leite(worksheet, workbook, indices_leve_leite, dados):
    """Aplica a formatação azul para produtos do programa Leve Leite."""
    if not indices_leve_leite:
        return

    blue_format = workbook.add_format({"font_color": "#90CEFD"})
    col_produto = 1  # Coluna B

    for row_idx in indices_leve_leite:
        excel_row = row_idx + 3
        valor_produto = dados[row_idx].get("produto_nome", "")
        worksheet.write(excel_row, col_produto, valor_produto, blue_format)


def aplicar_formatacao_numeros(worksheet, workbook, coluna, largura=None):
    """Aplica formatação numérica brasileira em uma coluna específica."""
    number_format = workbook.add_format({"num_format": "#,##0.00;(#,##0.00)"})
    col_range = f"{coluna}:{coluna}"
    worksheet.set_column(col_range, largura, number_format)


def _finalizar_formatacao_worksheet(
    worksheet, workbook, headers, subtitulo, titulo_relatorio, remove_titulos=False
):
    """Aplica formatações finais à planilha."""
    ultima_coluna = len(headers) - 1
    _definir_largura_colunas(worksheet)
    if not remove_titulos:
        _formatar_titulo(ultima_coluna, titulo_relatorio, workbook, worksheet)
        _formatar_subtitulo(subtitulo, ultima_coluna, workbook, worksheet)
    _formatar_headers(headers, workbook, worksheet)
    aplicar_formatacao_numeros(worksheet, workbook, "E", largura=18)  # Quantidade Total
    aplicar_formatacao_numeros(worksheet, workbook, "M", largura=12)  # Quantidade


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gerar_relatorio_cronogramas_xlsx_async(user, ids_cronogramas, filtros=None):
    logger.info(
        "x-x-x-x Iniciando a geração do arquivo relatorio_cronogramas.xlsx x-x-x-x"
    )

    HEADERS = [
        "Nº do Cronograma",
        "Produto",
        "Empresa",
        "Marca",
        "Quantidade Total",
        "Unidade",
        "Custo Unitário",
        "Armazém",
        "Status",
        "Etapa",
        "Parte",
        "Data de Entrega",
        "Quantidade",
        "Unidade/Etapa",
        "Total de Embalagens",
        "Situação",
        "Nº do Processo - SEI",
        "Nº do Empenho",
        "Nº do Contrato",
    ]

    TITULO_ARQUIVO = "relatorio_cronogramas.xlsx"
    TITULO_RELATORIO = "Relatório de Cronogramas"

    obj_central_download = gera_objeto_na_central_download(
        user=user,
        identificador=TITULO_ARQUIVO,
    )

    output = io.BytesIO()
    xlsxwriter = pd.ExcelWriter(
        output, engine="xlsxwriter", datetime_format="dd/mm/yyyy"
    )

    try:
        dados, subtitulo = _dados_relatorio_cronograma_xlsx(ids_cronogramas, filtros)
        df, indices_leve_leite = _preparar_dataframe_cronogramas(dados)

        df.to_excel(
            xlsxwriter,
            TITULO_RELATORIO,
            index=False,
            header=False,
            startrow=1,
        )

        workbook = xlsxwriter.book
        worksheet = xlsxwriter.sheets[TITULO_RELATORIO]

        _aplicar_estilos_leve_leite(worksheet, workbook, indices_leve_leite, dados)
        _finalizar_formatacao_worksheet(
            worksheet,
            workbook,
            HEADERS,
            subtitulo,
            TITULO_RELATORIO,
            remove_titulos=True,
        )

        xlsxwriter.close()
        output.seek(0)

        atualiza_central_download(
            obj_central_download,
            TITULO_ARQUIVO,
            output.read(),
        )

    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    finally:
        logger.info(
            "x-x-x-x Finaliza a geração do arquivo relatorio_cronogramas.xlsx x-x-x-x"
        )


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
    time_limit=3000,
    soft_time_limit=3000,
)
def gerar_relatorio_cronogramas_pdf_async(user, ids_cronogramas, filtros=None):
    logger.info(
        "x-x-x-x Iniciando a geração do arquivo relatorio_cronogramas.pdf x-x-x-x"
    )

    TEMPLATE_HTML = "relatorio_cronogramas.html"
    TITULO_ARQUIVO = "relatorio_cronogramas.pdf"

    obj_central_download = gera_objeto_na_central_download(
        user=user,
        identificador=TITULO_ARQUIVO,
    )

    try:
        paginas, subtitulo = _dados_relatorio_cronograma_pdf(ids_cronogramas, filtros)
        html_string = render_to_string(
            TEMPLATE_HTML,
            {
                "paginas": paginas,
                "subtitulo": subtitulo,
                "filtros": filtros,
            },
        )
        arquivo_relatorio = html_to_pdf_file(
            html_string,
            TITULO_ARQUIVO,
            True,
        )

        atualiza_central_download(
            obj_central_download,
            TITULO_ARQUIVO,
            arquivo_relatorio,
        )

        return arquivo_relatorio

    except Exception as e:
        atualiza_central_download_com_erro(obj_central_download, str(e))

    finally:
        logger.info(
            "x-x-x-x Finaliza a geração do arquivo relatorio_cronogramas.xlsx x-x-x-x"
        )


def _criar_linha_base_excel(cronograma, etapa):
    """Cria a linha base com dados do cronograma e etapa para o Excel."""

    return {
        "cronograma_numero": cronograma.get("numero"),
        "produto_nome": cronograma.get("produto", ""),
        "empresa_razao_social": cronograma.get("empresa", ""),
        "marca": cronograma.get("marca", ""),
        "qtd_total_programada": cronograma.get("qtd_total_programada"),
        "produto_unidade": etapa.get("unidade_medida"),
        "custo_unitario": cronograma.get("custo_unitario_produto"),
        "armazem": cronograma.get("armazem", ""),
        "cronograma_status": cronograma.get("status"),
        "etapa": etapa.get("etapa"),
        "parte": etapa.get("parte"),
        "data_programada": etapa.get("data_programada"),
        "quantidade": converter_para_numero(etapa.get("quantidade")),
        "total_embalagens": etapa.get("total_embalagens"),
        "programa_leve_leite": cronograma.get("programa_leve_leite", False),
        "situacao": etapa.get("situacao", ""),
        "numero_processo": cronograma.get("numero_processo", ""),
        "numero_empenho": etapa.get("numero_empenho", ""),
        "numero_contrato": cronograma.get("numero_contrato", ""),
    }


def _processar_fichas_recebimento(linha_base, etapa, fichas_recebimento):
    linhas = []
    for ficha in fichas_recebimento:
        linha = linha_base.copy()

        if ficha.get("houve_reposicao"):
            linha["etapa"] = (
                f"{etapa.get('etapa')} - {etapa.get('parte')} - Reposição / Pagamento de Notificação"
            )
            linha["parte"] = ""

        linha["situacao"] = ficha.get("situacao")
        linhas.append(linha)

    return linhas


def _deve_mostrar_linha_a_receber(etapa, fichas_recebimento, filtros):
    situacoes_filtro = filtros.get("situacao", []) if filtros else []
    return (not fichas_recebimento or not etapa.get("foi_recebida")) and (
        not situacoes_filtro or "A Receber" in situacoes_filtro
    )


def _dados_relatorio_cronograma_xlsx(ids_cronogramas, filtros=None):
    cronogramas = (
        Cronograma.objects.filter(id__in=ids_cronogramas)
        .order_by("-alterado_em")
        .distinct()
    )

    dados_cronogramas = CronogramaRelatorioSerializer(cronogramas, many=True).data

    if filtros:
        dados_cronogramas = filtrar_etapas(dados_cronogramas, filtros)

    dados = []
    for cronograma in dados_cronogramas:
        for etapa in cronograma.get("etapas", []):
            linha_base = _criar_linha_base_excel(cronograma, etapa)
            fichas_recebimento = etapa.get("fichas_recebimento", [])

            if fichas_recebimento:
                linhas_fichas = _processar_fichas_recebimento(
                    linha_base, etapa, fichas_recebimento
                )
                dados.extend(linhas_fichas)

            if _deve_mostrar_linha_a_receber(etapa, fichas_recebimento, filtros):
                linha = linha_base.copy()
                linha["situacao"] = "A receber"
                dados.append(linha)

    subtitulo = _subtitulo_relatorio_cronogramas_xlsx(cronogramas)
    return dados, subtitulo


def _dados_relatorio_cronograma_pdf(ids_cronogramas, filtros=None):
    cronogramas = (
        Cronograma.objects.prefetch_related("etapas")
        .filter(id__in=ids_cronogramas)
        .order_by("-alterado_em")
        .distinct()
    )
    dados = CronogramaRelatorioSerializer(cronogramas, many=True).data

    if filtros:
        dados = filtrar_etapas(dados, filtros)

    dados_paginados = _paginar_dados_relatorio_pdf(dados)
    subtitulo = _subtitulo_relatorio_cronogramas_pdf(cronogramas)

    return dados_paginados, subtitulo


def _paginar_dados_relatorio_pdf(dados):
    """
    Pagina os cronogramas em uma lista de listas, respeitando as seguintes regras:

    - Cada página pode conter:
        - Até 3 cronogramas.
        - No máximo 6 etapas, no total.
        - Exceções:
            - Se houver apenas 2 cronogramas, a página pode conter até 9 etapas.
            - Se houver apenas 1 cronograma, a página não levará em consideração o número de etapas.

    Parâmetros:
    dados (list): Lista de dicionários, onde cada dicionário representa um cronograma
                  e possui uma chave 'etapas' que é uma lista de etapas.

    Retorna:
    dados_paginados: Uma lista de listas, onde cada lista interna contém cronogramas paginados
                     de acordo com as regras definidas.
    """

    dados_paginados = []
    pagina_atual = []
    for cronograma in dados:
        qtd_cronogramas = len(pagina_atual)
        qtd_etapas_atual = sum([len(c["etapas"]) for c in pagina_atual])
        qtd_etapas_adicionais = len(cronograma["etapas"])

        if (
            qtd_cronogramas > 2 or qtd_etapas_atual + qtd_etapas_adicionais > 6
        ) and not (
            (qtd_cronogramas == 1 and qtd_etapas_atual + qtd_etapas_adicionais < 10)
            or (qtd_cronogramas == 0)
        ):
            dados_paginados.append([*pagina_atual])
            pagina_atual.clear()

        pagina_atual.append(cronograma)

    if pagina_atual:
        dados_paginados.append(pagina_atual)

    return dados_paginados


def _subtitulo_relatorio_cronogramas_xlsx(qs_cronogramas):
    result = "Total de Cronogramas Criados"
    result += f": {qs_cronogramas.count()}"

    ordered_status_count = totalizador_relatorio_cronograma(qs_cronogramas)
    status_count_string = "".join(
        [f" | {status}: {count}" for status, count in ordered_status_count.items()]
    )
    result += status_count_string

    result += f" | Data de Extração do Relatório: {date.today().strftime('%d/%m/%Y')}"

    return result


def _subtitulo_relatorio_cronogramas_pdf(qs_cronogramas):
    result = "Total de Cronogramas Criados"
    result += f": <strong>{qs_cronogramas.count()}</strong>"

    ordered_status_count = totalizador_relatorio_cronograma(qs_cronogramas)

    status_count_string = "".join(
        [
            (
                f" |<br>{status}: <strong>{count}</strong>"
                if idx == len(ordered_status_count) - 3
                else f" | {status}: <strong>{count}</strong>"
            )
            for idx, (status, count) in enumerate(ordered_status_count.items())
        ]
    )

    result += status_count_string

    result += f" | Data de Extração do Relatório: <strong>{date.today().strftime('%d/%m/%Y')}</strong>"

    return result


def _definir_largura_colunas(worksheet):
    LARGURA_COLUNAS = {
        "A:A": 18,
        "B:B": 40,
        "C:C": 30,
        "D:D": 18,
        "E:E": 18,
        "F:F": 10,
        "G:G": 20,
        "H:H": 30,
        "I:I": 30,
        "J:J": 10,
        "K:K": 10,
        "L:L": 18,
        "M:M": 12,
        "N:N": 10,
        "O:O": 12,
        "P:P": 10,
        "Q:Q": 18,
        "R:R": 12,
        "S:S": 18,
    }

    for col, width in LARGURA_COLUNAS.items():
        worksheet.set_column(col, width)


def _formatar_titulo(ULTIMA_COLUNA, TITULO_RELATORIO, workbook, worksheet):
    ALTURA_LINHA_TITULO = 65
    LINHA_TITULO = 0
    LOGO_SIGPAE = "sme_sigpae_api/static/images/logo-sigpae-light.png"

    titulo_format = workbook.add_format(
        {
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#a9d18e",
            "border_color": "#198459",
        }
    )
    worksheet.set_row(LINHA_TITULO, ALTURA_LINHA_TITULO)
    worksheet.merge_range(
        LINHA_TITULO,
        0,
        LINHA_TITULO,
        ULTIMA_COLUNA,
        TITULO_RELATORIO,
        titulo_format,
    )
    worksheet.insert_image(
        LINHA_TITULO,
        0,
        LOGO_SIGPAE,
        {"x_offset": 10, "y_offset": 10},
    )


def _formatar_subtitulo(subtitulo, ULTIMA_COLUNA, workbook, worksheet):
    ALTURA_LINHA_SUBTITULO = 50
    LINHA_SUBTITULO = 1

    subtitulo_format = workbook.add_format(
        {
            "bold": True,
            "text_wrap": True,
            "valign": "vcenter",
        }
    )
    worksheet.set_row(LINHA_SUBTITULO, ALTURA_LINHA_SUBTITULO)
    worksheet.merge_range(
        LINHA_SUBTITULO,
        0,
        LINHA_SUBTITULO,
        ULTIMA_COLUNA,
        subtitulo,
        subtitulo_format,
    )


def _formatar_headers(HEADERS, workbook, worksheet):
    ALTURA_LINHA_HEADERS = 30
    LINHA_HEADERS = 0

    headers_format = workbook.add_format(
        {
            "bold": True,
            "text_wrap": True,
            "align": "left",
            "valign": "vcenter",
            "bg_color": "#a9d18e",
        }
    )
    worksheet.set_row(LINHA_HEADERS, ALTURA_LINHA_HEADERS)
    for index, header in enumerate(HEADERS):
        worksheet.write(
            LINHA_HEADERS,
            index,
            header,
            headers_format,
        )


@shared_task(
    retry_backoff=2,
    retry_kwargs={"max_retries": 8},
)
def importa_feriados_para_interrupcoes_programadas():
    """
    Task periódica para importar feriados do ano atual e próximo ano
    como Interrupções Programadas de Entrega.
    """
    logger.info(
        "x-x-x-x Iniciando importação de feriados para Interrupções Programadas x-x-x-x"
    )

    calendario = BrazilSaoPauloCity()
    ano_atual = date.today().year
    anos = [ano_atual, ano_atual + 1]

    tipos_calendario = [
        InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_ARMAZENAVEL,
        InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_PONTO_A_PONTO,
    ]

    datas_existentes_por_tipo = {}
    for tipo in tipos_calendario:
        datas_existentes = set(
            InterrupcaoProgramadaEntrega.objects.filter(
                data__year__in=anos,
                tipo_calendario=tipo,
            ).values_list("data", flat=True)
        )
        datas_existentes_por_tipo[tipo] = datas_existentes

    feriados_criados = 0
    feriados_ignorados = 0

    for ano in anos:
        feriados = calendario.holidays(ano)

        for data_feriado, nome_feriado in feriados:
            nome_traduzido = TRADUCOES_FERIADOS.get(nome_feriado, nome_feriado)

            for tipo_calendario in tipos_calendario:
                if data_feriado in datas_existentes_por_tipo[tipo_calendario]:
                    feriados_ignorados += 1
                    continue

                InterrupcaoProgramadaEntrega.objects.create(
                    data=data_feriado,
                    motivo=InterrupcaoProgramadaEntrega.MOTIVO_FERIADO,
                    descricao_motivo=nome_traduzido,
                    tipo_calendario=tipo_calendario,
                )
                feriados_criados += 1

    logger.info(
        f"x-x-x-x Finaliza importação de feriados. "
        f"Criados: {feriados_criados}, Ignorados: {feriados_ignorados} x-x-x-x"
    )
