import numpy as np

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    ProtocoloPadraoDietaEspecial,
)
from sme_sigpae_api.escola.models import Lote


def build_titulo(lotes, status, classificacoes, protocolos, data_inicial, data_final):
    titulo = (
        f'Dietas {"Autorizadas" if status.upper() == "AUTORIZADAS" else "Canceladas"}:'
    )
    if lotes:
        nomes_lotes = ",".join(
            [lote.nome for lote in Lote.objects.filter(uuid__in=lotes)]
        )
        titulo += f" | {nomes_lotes}"
    if classificacoes:
        nomes_classificacoes = ",".join(
            [
                classificacao.nome
                for classificacao in ClassificacaoDieta.objects.filter(
                    id__in=classificacoes
                )
            ]
        )
        titulo += f" | Classificação(ões) da dieta: {nomes_classificacoes}"
    if protocolos:
        nomes_protocolos = ", ".join(
            [
                protocolo.nome_protocolo
                for protocolo in ProtocoloPadraoDietaEspecial.objects.filter(
                    uuid__in=protocolos
                )
            ]
        )
        titulo += f" | Protocolo(s) padrão(ões): {nomes_protocolos}"
    if data_inicial:
        titulo += f" | Data inicial: {data_inicial}"
    if data_final:
        titulo += f" | Data final: {data_final}"
    return titulo


def build_xlsx_relatorio_terceirizadas(
    output,
    serializer,
    queryset,
    status,
    lotes,
    classificacoes,
    protocolos,
    data_inicial,
    data_final,
    exibir_diagnostico=False,
):
    import pandas as pd

    with pd.ExcelWriter(output, engine="xlsxwriter") as xlwriter:
        df = pd.DataFrame(serializer.data)

        # Adiciona linhas em branco no comeco do arquivo
        df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
        df = pd.concat([df_auxiliar, df], ignore_index=True)
        df = pd.concat([df_auxiliar, df], ignore_index=True)
        df = pd.concat([df_auxiliar, df], ignore_index=True)

        df.to_excel(xlwriter, "Solicitações de dieta especial")
        workbook = xlwriter.book
        worksheet = xlwriter.sheets["Solicitações de dieta especial"]
        worksheet.set_row(0, 30)
        worksheet.set_row(1, 30)
        worksheet.set_column("B:F", 30)
        merge_format = workbook.add_format({"align": "center", "bg_color": "#a9d18e"})
        merge_format.set_align("vcenter")
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()
        cell_format.set_align("vcenter")
        v_center_format = workbook.add_format()
        v_center_format.set_align("vcenter")
        single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})
        len_cols = len(df.columns)
        worksheet.merge_range(
            0, 0, 0, len_cols, "Relatório de dietas especiais", merge_format
        )
        titulo = build_titulo(
            lotes, status, classificacoes, protocolos, data_inicial, data_final
        )
        worksheet.merge_range(1, 0, 2, len_cols - 1, titulo, cell_format)
        worksheet.merge_range(
            1,
            len_cols,
            2,
            len_cols,
            f"Total de dietas: {queryset.count()}",
            v_center_format,
        )
        worksheet.write(3, 1, "COD.EOL do Aluno", single_cell_format)
        worksheet.write(3, 2, "Nome do Aluno", single_cell_format)
        worksheet.write(3, 3, "Nome da Escola", single_cell_format)
        worksheet.write(3, 4, "Classificação da dieta", single_cell_format)
        worksheet.write(
            3,
            5,
            "Relação por Diagnóstico" if exibir_diagnostico else "Protocolo Padrão",
            single_cell_format,
        )
        if status.upper() == "CANCELADAS":
            worksheet.set_column("G:G", 30)
            worksheet.write(3, 6, "Data de cancelamento", single_cell_format)
        df.reset_index(drop=True, inplace=True)
    output.seek(0)
