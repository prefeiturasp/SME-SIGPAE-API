import datetime
from copy import deepcopy
from typing import BinaryIO

import numpy as np
from django.http import QueryDict
from django.template.loader import render_to_string

from sme_sigpae_api.escola.models import DiretoriaRegional, PeriodoEscolar
from sme_sigpae_api.escola.utils import faixa_to_string
from sme_sigpae_api.relatorios.utils import html_to_pdf_file


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


def formata_logs_para_titulo(logs_dietas: list[dict]) -> list[dict]:
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
    return logs_dietas_formatados


def encontrar_todos_os_periodos(obj):
    periodos = []

    if isinstance(obj, dict):
        for chave, valor in obj.items():
            if chave == "periodo":
                periodos.append(valor)
            periodos.extend(encontrar_todos_os_periodos(valor))
    elif isinstance(obj, list):
        for item in obj:
            periodos.extend(encontrar_todos_os_periodos(item))

    periodos_unicos = list(set(periodos))
    return [str(p).title() for p in periodos_unicos]


def build_titulo(
    logs_dietas_formatados: list[dict],
    querydict_params: QueryDict,
    for_pdf: bool = False,
) -> str:
    dre_nome = DiretoriaRegional.objects.get(
        iniciais=logs_dietas_formatados[0]["lote_dre"].split(" DRE ")[1]
    ).nome
    data_referencia = logs_dietas_formatados[0]["data_de_referencia"]

    bold = (
        (lambda text: f"<strong>{text}</strong>")
        if for_pdf
        else (lambda text: str(text))
    )

    titulo = f"Total de Dietas Autorizadas em {bold(data_referencia)} "
    titulo += f"para as unidades da DRE {bold(dre_nome)}"

    periodos_escolares = querydict_params.getlist("periodos_escolares_selecionadas[]")
    if periodos_escolares:
        nomes_periodos = ", ".join(
            PeriodoEscolar.objects.filter(uuid__in=periodos_escolares).values_list(
                "nome", flat=True
            )
        )
    elif for_pdf:
        nomes_periodos = ", ".join(encontrar_todos_os_periodos(logs_dietas_formatados))

    titulo += f" | {bold('Períodos:')} {nomes_periodos}"

    total_dietas = sum(log["dietas_autorizadas"] for log in logs_dietas_formatados)
    data_extraido = datetime.date.today().strftime("%d/%m/%Y")

    titulo += f": {bold(total_dietas)}"
    titulo += f" | Data de extração do relatório: {bold(data_extraido)}"
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

    with pd.ExcelWriter(output, engine="xlsxwriter") as xlwriter:
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
    output.seek(0)


def processar_cemei(periodos):
    turma_infantil = periodos.get("turma_infantil", [])
    por_idade = periodos.get("por_idade", [])

    dados_combinados = {}

    for item in turma_infantil:
        periodo = item["periodo"]
        dados_combinados[periodo] = {
            "periodo": periodo,
            "autorizadas_infantil": item["autorizadas"],
            "por_idade": [],
        }

    for item in por_idade:
        periodo = item["periodo"]
        if periodo not in dados_combinados:
            dados_combinados[periodo] = {
                "periodo": periodo,
                "autorizadas_infantil": 0,
                "por_idade": [],
            }
        dados_combinados[periodo]["por_idade"].extend(item.get("faixa_etaria", []))

    return list(dados_combinados.values())


def processar_emebs(periodos):
    infantil = periodos.get("infantil", [])
    fundamental = periodos.get("fundamental", [])

    dados_combinados = {}

    for item in infantil:
        periodo = item["periodo"]
        dados_combinados.setdefault(
            periodo,
            {
                "periodo": periodo,
                "autorizadas_infantil": 0,
                "autorizadas_fundamental": 0,
            },
        )
        dados_combinados[periodo]["autorizadas_infantil"] += item["autorizadas"]

    for item in fundamental:
        periodo = item["periodo"]
        dados_combinados.setdefault(
            periodo,
            {
                "periodo": periodo,
                "autorizadas_infantil": 0,
                "autorizadas_fundamental": 0,
            },
        )
        dados_combinados[periodo]["autorizadas_fundamental"] += item["autorizadas"]

    return list(dados_combinados.values())


def reestruturar_resultados(objeto):
    unidades_cemei = ["CEMEI", "CEU CEMEI"]
    unidades_emebs = ["EMEBS"]

    resultados_novos = []

    for resultado in objeto["resultados"]:
        novo_resultado = deepcopy(resultado)
        tipo_unidade = resultado.get("tipo_unidade", "")
        periodos = resultado.get("periodos", {})

        if tipo_unidade in unidades_cemei:
            novo_resultado["periodos"] = processar_cemei(periodos)
        elif tipo_unidade in unidades_emebs:
            novo_resultado["periodos"] = processar_emebs(periodos)

        resultados_novos.append(novo_resultado)

    return {"total_dietas": objeto["total_dietas"], "resultados": resultados_novos}


def gera_pdf_relatorio_historico_dieta_especial(dados, user, titulo):
    unidades_cei = ["CEI DIRET", "CEU CEI", "CEI", "CCI", "CCI/CIPS", "CEI CEU"]
    unidades_cemei = ["CEMEI", "CEU CEMEI"]
    unidades_emei_emef = [
        "EMEI",
        "CEU EMEI",
        "CEU EMEI",
        "EMEF",
        "CEU EMEF",
        "EMEFM",
        "CIEJA",
    ]
    unidades_emebs = ["EMEBS"]
    unidades_sem_periodos = ["CMCT", "CEU GESTAO"]

    dados = reestruturar_resultados(dados)

    html_string = render_to_string(
        "relatorio_historico_dieta_especial.html",
        {
            "unidades_cei": unidades_cei,
            "unidades_cemei": unidades_cemei,
            "unidades_emei_emef": unidades_emei_emef,
            "unidades_emebs": unidades_emebs,
            "unidades_sem_periodos": unidades_sem_periodos,
            "dados": dados,
            "user": user,
            "titulo_filtros": titulo,
        },
    )
    return html_to_pdf_file(
        html_string, "relatorio_historico_dieta_especial.pdf", is_async=True
    )
