import datetime
from typing import BinaryIO

import numpy as np
from django.http import QueryDict

from sme_sigpae_api.escola.models import DiretoriaRegional, PeriodoEscolar
from sme_sigpae_api.escola.utils import faixa_to_string


def get_faixa_etaria_cei(log: dict, faixa_etaria: str) -> str:
    if log["tipo_unidade"] not in [
        "CEI DIRET",
        "CEU CEI",
        "CEI",
        "CCI",
        "CCI/CIPS",
        "CEI CEU",
    ]:
        return faixa_etaria
    faixa_etaria = faixa_to_string(log["inicio"], log["fim"])
    return faixa_etaria


def get_faixa_etaria_cemei(log: dict, faixa_etaria: str) -> str:
    if log["tipo_unidade"] not in ["CEMEI", "CEU CEMEI"]:
        return faixa_etaria
    if log["inicio"]:
        faixa_etaria = faixa_to_string(log["inicio"], log["fim"])
    else:
        faixa_etaria = "Infantil"
    return faixa_etaria


def get_faixa_etaria_emebs(log: dict, faixa_etaria: str) -> str:
    if log["tipo_unidade"] != "EMEBS":
        return faixa_etaria
    if log["infantil_ou_fundamental"] == "INFANTIL":
        faixa_etaria = "Infantil (4 a 6 anos)"
    elif log["infantil_ou_fundamental"] == "FUNDAMENTAL":
        faixa_etaria = "Fundamental (acima de 6 anos)"
    return faixa_etaria


def get_faixa_etaria(log: dict) -> str:
    faixa_etaria = ""
    faixa_etaria = get_faixa_etaria_cei(log, faixa_etaria)
    faixa_etaria = get_faixa_etaria_cemei(log, faixa_etaria)
    faixa_etaria = get_faixa_etaria_emebs(log, faixa_etaria)
    return faixa_etaria


def build_titulo(
    logs_dietas_formatados: list[dict], querydict_params: QueryDict
) -> str:
    dre_nome = DiretoriaRegional.objects.get(
        iniciais=logs_dietas_formatados[0]["lote_dre"].split(" DRE ")[1]
    ).nome
    titulo = f"Total de Dietas Autorizadas em {logs_dietas_formatados[0]['data_de_referencia']} "
    titulo += f"para as unidades da DRE {dre_nome}"

    periodos_escolares = querydict_params.getlist("periodos_escolares_selecionadas[]")
    if periodos_escolares:
        nomes_periodos = ", ".join(
            PeriodoEscolar.objects.filter(uuid__in=periodos_escolares).values_list(
                "nome", flat=True
            )
        )
        titulo += f" | Períodos: {nomes_periodos}"

    total_dietas = sum([log["dietas_autorizadas"] for log in logs_dietas_formatados])
    titulo += f": {total_dietas}"
    titulo += f" | Data de extração do relatório: {datetime.date.today().strftime('%d/%m/%Y')}"
    return titulo


def formata_celula_faixa_etaria(
    df, workbook, worksheet, hash_cor, valor_celula
) -> None:
    col_index = df.columns.get_loc("faixa_etaria")
    excel_col_letter = chr(ord("A") + col_index)
    format_infantil = workbook.add_format({"bg_color": hash_cor})
    worksheet.conditional_format(
        f"{excel_col_letter}5:{excel_col_letter}{len(df) + 4}",
        {
            "type": "cell",
            "criteria": "==",
            "value": valor_celula,
            "format": format_infantil,
        },
    )


def build_xlsx_relatorio_historico_dietas(
    output: BinaryIO, logs_dietas: list[dict], querydict_params: QueryDict
) -> None:
    import pandas as pd

    xlwriter = pd.ExcelWriter(output, engine="xlsxwriter")

    logs_dietas_formatados = [
        {
            "lote_dre": f"{log['lote']} - DRE {log['dre']}",
            "unidade_educacional": log["nome_escola"],
            "classificacao_da_dieta": log["nome_classificacao"],
            "periodo": log["nome_periodo_escolar"],
            "faixa_etaria": get_faixa_etaria(log),
            "dietas_autorizadas": log["quantidade_total"],
            "data_de_referencia": log["data"].strftime("%d/%m/%Y"),
        }
        for log in logs_dietas
    ]

    df = pd.DataFrame(logs_dietas_formatados)
    df.insert(0, "Nº", range(1, len(df) + 1))

    # Adiciona linhas em branco no comeco do arquivo
    df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
    df = pd.concat([df_auxiliar, df], ignore_index=True)
    df = pd.concat([df_auxiliar, df], ignore_index=True)
    df = pd.concat([df_auxiliar, df], ignore_index=True)
    df.to_excel(xlwriter, "Histórico de Dietas Autorizadas", index=False)
    workbook = xlwriter.book
    worksheet = xlwriter.sheets["Histórico de Dietas Autorizadas"]
    worksheet.set_row(0, 30)
    worksheet.set_row(1, 30)
    worksheet.set_column("B:H", 30)
    worksheet.set_column("C:C", 50)
    merge_format = workbook.add_format(
        {"align": "center", "bg_color": "#a9d18e", "bold": True}
    )
    merge_format.set_align("vcenter")
    cell_format = workbook.add_format({"align": "center", "bold": True})
    cell_format.set_text_wrap()
    cell_format.set_align("vcenter")
    v_center_format = workbook.add_format()
    v_center_format.set_align("vcenter")
    single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})
    len_cols = len(df.columns)
    worksheet.merge_range(
        0,
        0,
        0,
        len_cols - 1,
        "Relatório Histórico de Dietas Especiais Autorizadas",
        merge_format,
    )
    worksheet.insert_image(
        0,
        0,
        "sme_sigpae_api/relatorios/static/images/logo-sigpae.png",
        {
            "x_offset": 0,
            "y_offset": 0,
            "x_scale": 0.05,
            "y_scale": 0.05,
        },
    )
    titulo = build_titulo(logs_dietas_formatados, querydict_params)
    worksheet.merge_range(1, 0, 2, len_cols - 1, titulo, cell_format)
    worksheet.write(3, 0, "Nº", single_cell_format)
    worksheet.write(3, 1, "Lote/DRE", single_cell_format)
    worksheet.write(3, 2, "Unidade Educacional", single_cell_format)
    worksheet.write(3, 3, "Classificação da Dieta", single_cell_format)
    worksheet.write(3, 4, "Período", single_cell_format)
    worksheet.write(3, 5, "Faixa Etária", single_cell_format)
    worksheet.write(3, 6, "Dietas Autorizadas", single_cell_format)
    worksheet.write(3, 7, "Data de Referência", single_cell_format)

    formata_celula_faixa_etaria(df, workbook, worksheet, "#F4B084", '"Infantil"')
    formata_celula_faixa_etaria(
        df, workbook, worksheet, "#BDD7EE", '"Infantil (4 a 6 anos)"'
    )
    formata_celula_faixa_etaria(
        df, workbook, worksheet, "#C6E0B4", '"Fundamental (acima de 6 anos)"'
    )
    xlwriter.save()
    output.seek(0)
