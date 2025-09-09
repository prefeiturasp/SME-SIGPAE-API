import numpy as np
import pandas as pd
from datetime import datetime
from django.template.loader import render_to_string
from sme_sigpae_api.escola.models import Lote
from sme_sigpae_api.relatorios.utils import html_to_pdf_file


def gera_dicionario_relatorio_recreio(solicitacoes):
    dados = []
    for solicitacao in solicitacoes:
        alergias = solicitacao.alergias_intolerancias.all()
        alergias_lista = [a.descricao for a in alergias] if alergias else ["--"]
        dados_solicitacoes = {
            "codigo_eol_aluno": solicitacao.aluno.codigo_eol,
            "nome_aluno": solicitacao.aluno.nome,
            "nome_escola": solicitacao.escola.nome,
            "escola_destino": (
                solicitacao.escola_destino.nome if solicitacao.escola_destino else "--"
            ),
            "data_inicio": (
                solicitacao.data_inicio.strftime("%d/%m/%Y")
                if solicitacao.data_inicio
                else "--"
            ),
            "data_fim": (
                solicitacao.data_termino.strftime("%d/%m/%Y")
                if solicitacao.data_termino
                else "--"
            ),
            "classificacao": (
                solicitacao.classificacao.nome if solicitacao.classificacao else "--"
            ),
            "alergias_intolerancias": ", ".join(alergias_lista),
        }
        dados.append(dados_solicitacoes)
    return dados


def gera_pdf_relatorio_recreio_nas_ferias(dados, user, lote):
    dre_lote = Lote.objects.get(uuid=lote)
    html_string = render_to_string(
        "relatorio_recreio_nas_ferias.html",
        {
            "dados": dados,
            "user": user,
            "total_dados": len(dados),
            "data_extracao": datetime.now().strftime("%d/%m/%Y"),
            "data_hora_geracao": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
            "dre_lote": f"{dre_lote.diretoria_regional.iniciais} - {dre_lote.nome}",
        },
    )
    return html_to_pdf_file(
        html_string, "relatorio_recreio_nas_ferias.pdf", is_async=True
    )


def gera_xlsx_relatorio_recreio_nas_ferias(output, dados, lote) -> None:
    sheet_name = "Relatório de Recreio nas Férias"
    with pd.ExcelWriter(output, engine="xlsxwriter") as xlwriter:
        dados_formato = [{
            "Cód. EOL e Nome do Aluno": f"{d['codigo_eol_aluno']} - {d['nome_aluno']}",
            "Unidade de Origem": d["nome_escola"],
            "Unidade de Destino": d["escola_destino"],
            "Classificação da Dieta": d["classificacao"],
            "Relação por Diagnóstico": d["alergias_intolerancias"],
            "Vigência da Dieta": f"DE {d['data_inicio']} ATÉ {d['data_fim']}",
        } for d in dados]

        df = pd.DataFrame(dados_formato)
        df.insert(0, "Nº", range(1, len(df) + 1))

        df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
        df = pd.concat([df_auxiliar] * 3 + [df], ignore_index=True)

        df.to_excel(xlwriter, sheet_name=sheet_name, index=False)

        workbook = xlwriter.book
        worksheet = xlwriter.sheets[sheet_name]

        merge_format = workbook.add_format(
            {"align": "center", "valign": "vcenter", "bg_color": "#a9d18e", "bold": True}
        )
        cell_format = workbook.add_format(
            {"align": "center", "valign": "vcenter", "bold": True, "text_wrap": True}
        )
        single_cell_format = workbook.add_format({"bg_color": "#a9d18e"})

        worksheet.set_row(0, 30)
        worksheet.set_row(1, 30)
        worksheet.set_column("B:H", 40)

        len_cols = len(df.columns)
        worksheet.merge_range(
            0, 0, 0, len_cols - 1,
            "Relatório de Dietas Autorizadas para Recreio nas Férias",
            merge_format,
        )

        worksheet.insert_image(
            0, 0,
            "sme_sigpae_api/relatorios/static/images/logo-sigpae.png",
            {"x_scale": 0.05, "y_scale": 0.05},
        )

        dre_lote = Lote.objects.get(uuid=lote)
        titulo = (
            f"Total de Dietas Autorizadas: {len(dados)} | "
            f"Para as Unidades da DRE/LOTE: {dre_lote.diretoria_regional.iniciais} - {dre_lote.nome} | "
            f"Data de extração do relatório: {datetime.now().strftime('%d/%m/%Y')}"
        )
        worksheet.merge_range(1, 0, 2, len_cols - 1, titulo, cell_format)

        colunas = [
            "Nº",
            "Cód. EOL e Nome do Aluno",
            "Unidade de Origem",
            "Unidade de Destino",
            "Classificação da Dieta",
            "Relação por Diagnóstico",
            "Vigência da Dieta",
        ]
        for idx, col in enumerate(colunas):
            worksheet.write(3, idx, col, single_cell_format)

    output.seek(0)
