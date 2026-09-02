import io
from datetime import datetime
from typing import List

import pandas as pd

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from src.dados_comuns.utils import converte_numero_em_mes
from src.escola.models import DiretoriaRegional, Escola, Lote


def _insere_tabela_periodo_na_planilha(aba, refeicoes, colunas, proxima_linha, writer):
    linhas = [[refeicao, *totais.values()] for refeicao, totais in refeicoes.items()]

    df = pd.DataFrame(data=linhas, columns=colunas)

    total_servido = df[colunas[1]].sum()
    total_frequencia = df[colunas[2]].sum()

    totais = pd.DataFrame(
        data=[
            [
                "TOTAL",
                total_servido,
                total_frequencia,
                round(total_servido / total_frequencia, 4),
            ]
        ],
        columns=colunas,
    )

    df = pd.concat([df, totais], ignore_index=True)

    df.to_excel(writer, sheet_name=aba, startrow=proxima_linha, index=False)

    return df


def _obtem_nomes_lotes(query_params: dict) -> list[str]:
    lotes_uuid = query_params.get("lotes")
    if not lotes_uuid:
        return []
    return list(Lote.objects.filter(uuid__in=lotes_uuid).values_list("nome", flat=True))


def _obtem_dre(query_params: dict):
    dre_uuid = query_params.get("diretoria_regional")
    if not dre_uuid:
        return None
    return DiretoriaRegional.objects.filter(uuid=dre_uuid).first()


def _formata_segmento_dre_lote(dre, lote_nomes: list[str]) -> str:
    if lote_nomes and dre:
        return f" | {', '.join(lote_nomes)} - DRE {dre.nome}"
    if lote_nomes:
        return f" | {', '.join(lote_nomes)}"
    if dre:
        return f" | DRE {dre.nome}"
    return ""


def _formata_segmento_escola(query_params: dict, nome_escola: str = None) -> str:
    if nome_escola:
        return f" | {nome_escola}"
    escola_codigo_eol = query_params.get("escola")
    if not escola_codigo_eol:
        return ""
    escola_codigo_eol, *_ = escola_codigo_eol.split("-")
    escola = Escola.objects.filter(codigo_eol=escola_codigo_eol.strip()).first()
    if not escola:
        return ""
    return f" | {escola.nome}"


def _formata_segmento_periodo_lancamento(query_params: dict) -> str:
    periodo_lancamento_de = query_params.get("periodo_lancamento_de")
    periodo_lancamento_ate = query_params.get("periodo_lancamento_ate")
    if not periodo_lancamento_de or not periodo_lancamento_ate:
        return ""
    return (
        f" | PERÍODO DE LANÇAMENTO: DE {periodo_lancamento_de} "
        f"ATÉ {periodo_lancamento_ate}"
    )


def _formata_filtros(query_params: dict, nome_escola: str = None):
    mes, ano = query_params.get("mes_ano").split("_")
    filtros = f"{converte_numero_em_mes(int(mes))} {ano}"

    filtros += _formata_segmento_dre_lote(
        _obtem_dre(query_params), _obtem_nomes_lotes(query_params)
    )
    filtros += _formata_segmento_escola(query_params, nome_escola)
    filtros += _formata_segmento_periodo_lancamento(query_params)

    return filtros


def _eh_relatorio_por_escola(resultados):
    return (
        isinstance(resultados, list) and bool(resultados) and "escola" in resultados[0]
    )


def _preenche_titulo(workbook, worksheet, colunas):
    formatacao = workbook.add_format({"bold": True, "bg_color": "#C1F2B0"})
    formatacao.set_align("center")
    formatacao.set_align("vcenter")

    worksheet.merge_range(
        0,
        0,
        0,
        len(colunas) - 1,
        "Relatório de Adesão das Alimentações Servidas",
        formatacao,
    )
    worksheet.set_row(0, 50)
    worksheet.insert_image(
        0,
        0,
        "src/relatorios/static/images/logo-sigpae.png",
        {
            "x_offset": 50,
            "y_offset": 5,
            "x_scale": 0.08,
            "y_scale": 0.08,
        },
    )


def _preenche_linha_dos_filtros_selecionados(
    workbook,
    worksheet,
    query_params: dict,
    colunas: List[str],
    nome_escola: str = None,
):
    filtros = _formata_filtros(query_params, nome_escola)

    worksheet.merge_range(1, 0, 1, len(colunas) - 1, filtros.upper())
    worksheet.set_row(1, 30, workbook.add_format({"align": "vcenter"}))


def _preenche_data_do_relatorio(workbook, worksheet, colunas):
    worksheet.merge_range(
        2,
        0,
        2,
        len(colunas) - 1,
        "Data: " + datetime.now().date().strftime(FORMATO_DATA_BRASILEIRO),
    )
    worksheet.set_row(2, 25, workbook.add_format({"align": "vcenter"}))


def _preenche_linha_do_periodo(
    workbook, worksheet, proxima_linha: int, periodo: str, colunas: List[str]
):
    formatacao = workbook.add_format(
        {"bold": True, "font_color": "#006400", "align": "vcenter"}
    )

    worksheet.merge_range(
        proxima_linha - 1,
        0,
        proxima_linha - 1,
        len(colunas) - 1,
        periodo.upper(),
        formatacao,
    )
    worksheet.set_row(proxima_linha - 1, 25, workbook.add_format({"align": "vcenter"}))


def _ajusta_layout_header(workbook, worksheet, proxima_linha, df):
    linha = proxima_linha - len(df.index) - 1
    formatacao = workbook.add_format({"bold": True, "bg_color": "#A5DD9B"})
    formatacao.set_align("center")
    formatacao.set_align("vcenter")
    formatacao.set_border()

    worksheet.write_row(linha, 0, df.columns.values, formatacao)
    worksheet.set_row(linha, 25)


def _formata_numeros_linha_total(workbook, worksheet, proxima_linha, colunas, df):
    linha = proxima_linha - 1
    for index, value in enumerate(df.iloc[-1].values):
        formatacao = {
            "bold": True,
            "bg_color": "#EFECEC",
        }

        if index == len(colunas) - 1:
            formatacao["num_format"] = "0.00%"
        else:
            formatacao["num_format"] = "#,##0"

        formatacao = workbook.add_format(formatacao)
        formatacao.set_align("center")
        formatacao.set_align("vcenter")
        formatacao.set_border()

        worksheet.write_row(linha, index, [value], formatacao)

    worksheet.set_row(linha, 25)


def _ajusta_layout_colunas(workbook, worksheet, colunas):
    formatacao = workbook.add_format()
    formatacao.set_align("center")
    formatacao.set_align("vcenter")

    worksheet.set_column(0, len(colunas) - 1, 30, formatacao)


def _formata_numeros_colunas_total_servido_e_frequencia(workbook, worksheet):
    formatacao = workbook.add_format({"num_format": "#,##0"})
    formatacao.set_align("center")
    formatacao.set_align("vcenter")

    worksheet.set_column(1, 2, None, formatacao)


def _formata_numeros_coluna_total_adesao(workbook, worksheet, colunas):
    formatacao = workbook.add_format({"num_format": "0.00%"})
    formatacao.set_align("center")
    formatacao.set_align("vcenter")

    worksheet.set_column(len(colunas) - 1, len(colunas) - 1, None, formatacao)


def _preenche_aba(
    workbook, writer, aba: str, resultados, query_params, colunas, nome_escola=None
):
    proxima_linha = 4  # 4 linhas em branco para o cabecalho
    quantidade_de_linhas_em_branco_apos_tabela = 2

    worksheet = workbook.add_worksheet(aba)

    _preenche_titulo(workbook, worksheet, colunas)
    _preenche_linha_dos_filtros_selecionados(
        workbook, worksheet, query_params, colunas, nome_escola
    )
    _preenche_data_do_relatorio(workbook, worksheet, colunas)

    for periodo, refeicoes in resultados.items():
        df = _insere_tabela_periodo_na_planilha(
            aba, refeicoes, colunas, proxima_linha, writer
        )

        _preenche_linha_do_periodo(
            workbook,
            worksheet,
            proxima_linha,
            periodo,
            colunas,
        )

        proxima_linha += len(df.index) + 1

        _ajusta_layout_header(workbook, worksheet, proxima_linha, df)
        _formata_numeros_linha_total(workbook, worksheet, proxima_linha, colunas, df)

        proxima_linha += quantidade_de_linhas_em_branco_apos_tabela

    _ajusta_layout_colunas(workbook, worksheet, colunas)
    _formata_numeros_colunas_total_servido_e_frequencia(workbook, worksheet)
    _formata_numeros_coluna_total_adesao(workbook, worksheet, colunas)


def gera_relatorio_adesao_xlsx(resultados, query_params):
    colunas = [
        "Tipo de Alimentação",
        "Total de Alimentações Servidas",
        "Número Total de Frequência",
        "% de Adesão",
    ]

    file = io.BytesIO()

    with pd.ExcelWriter(file, engine="xlsxwriter") as writer:
        workbook = writer.book

        if _eh_relatorio_por_escola(resultados):
            for resultado in resultados:
                aba = resultado["escola"]["nome"]
                _preenche_aba(
                    workbook,
                    writer,
                    aba,
                    resultado["resultados"],
                    query_params,
                    colunas,
                    nome_escola=resultado["escola"]["nome"],
                )
        else:
            _preenche_aba(
                workbook,
                writer,
                "Relatório de Adesão",
                resultados,
                query_params,
                colunas,
            )

    return file.getvalue()
