import datetime
import io

import numpy as np
import pandas as pd


def gerar_relatorio_reclamacao_produto_excel(
    reclamacoes: list[dict], quantidade_reclamacoes: int, filtros: dict
) -> io.BytesIO:
    """
    Gera um relatório em formato Excel com informações sobre reclamações de produtos.

    Args:
        reclamacoes (list[dict]): Lista de dicionários contendo informações detalhadas das reclamações
        quantidade_reclamacoes (int):  Número total de reclamações filtradas.
        filtros (dict): Filtros aplicados na consulta

    Returns:
        io.BytesIO: Arquivo Excel em memória contendo o relatório.
    """
    output = io.BytesIO()
    dados_reclamacao = [
        _extrair_dados_reclamacao(reclamacao, index)
        for index, reclamacao in enumerate(reclamacoes, start=1)
    ]

    colunas = [
        "Nº",
        "Edital",
        "DRE/LOTE",
        "Empresa",
        "Nome do Produto",
        "Marca",
        "Fabricante",
        "Status do Produto",
        "Nº da Reclamação",
        "RF e Nome do Reclamante",
        "Cód EOL e Nome da Escola",
        "Status da Reclamação",
        "Data da Reclamação",
    ]
    subtitulo = _gerar_subtitulo(filtros, quantidade_reclamacoes)

    build_xlsx_reclamacao(
        output,
        dados=dados_reclamacao,
        titulo="Relatório de Acompanhamento de Reclamação de Produtos",
        subtitulo=subtitulo,
        # titulo_sheet='Produtos',
        colunas=colunas,
    )
    return output


def _extrair_dados_reclamacao(reclamacao: dict[str, str], index: int) -> dict[str, str]:
    """
    Extrai e organiza os dados de uma reclamação em formato tabular.

    Args:
        reclamacao (dict[str, str]): Dados brutos da reclamação.
        index (int): Número sequencial da reclamação.

    Returns:
        dict[str, str]: Dicionário estruturado com os campos padronizados do relatório.
    """
    escola = reclamacao.get("escola", {})
    codigo_eol = escola.get("codigo_eol")
    nome_escola = escola.get("nome")
    diretoria_regional = escola.get("diretoria_regional", {})
    lote = escola.get("lote", {})
    terceirizada = lote.get("terceirizada", {})
    homologacao_produto = reclamacao.get("homologacao_produto", {})
    produto = homologacao_produto.get("produto", {})
    rf = reclamacao.get("reclamante_registro_funcional")
    nome = reclamacao.get("reclamante_nome")

    return {
        "Nº": index,
        "Edital": reclamacao.get("numero_edital"),
        "DRE/LOTE": f'{diretoria_regional.get("iniciais")} - {lote.get("nome")}',
        "Empresa": terceirizada.get("nome_fantasia"),
        "Nome do Produto": produto.get("nome"),
        "Marca": produto.get("marca", {}).get("nome"),
        "Fabricante": produto.get("fabricante", {}).get("nome"),
        "Status do Produto": homologacao_produto.get("status_titulo").upper(),
        "Nº da Reclamação": f"#{reclamacao.get('id_externo')}",
        "RF e Nome do Reclamante": f"{rf} - {nome}",
        "Cód EOL e Nome da Escola": f"{codigo_eol} - {nome_escola}",
        "Status da Reclamação": reclamacao.get("status_titulo"),
        "Data da Reclamação": reclamacao.get("criado_em")[:10],
    }


def _gerar_subtitulo(filtros: dict, quantidade_reclamacoes: int) -> str:
    """
    Gera o subtítulo do relatório com base nos filtros aplicados e na quantidade de reclamações.

    Args:
        filtros (dict): Filtros utilizados na consulta
        quantidade_reclamacoes (int): Número total de reclamações encontradas.

    Returns:
       str: Texto do subtítulo formatado.
    """
    periodo = None
    data_inicial = filtros.get("data_inicial_reclamacao")
    data_final = filtros.get("data_final_reclamacao")
    if data_inicial and data_final:
        periodo = f"De {data_inicial} a {data_final}"
    elif data_inicial and not data_final:
        periodo = f"A partir de {data_inicial}"
    elif not data_inicial and data_final:
        periodo = f"Até {data_final}"

    subtitulo = f"Total de Reclamações de produtos para os editais selecionados: {quantidade_reclamacoes} | "
    if periodo:
        subtitulo += f"Período das Reclamações: {periodo} | "
    subtitulo += f"Data de Extração do Relatório: {datetime.datetime.now().date().strftime("%d/%m/%Y")}"

    return subtitulo


def build_xlsx_reclamacao(
    output: io.BytesIO,
    dados: list[dict],
    titulo: str,
    subtitulo: str,
    colunas: list[str],
) -> io.BytesIO:
    """
    Constrói e formata a planilha Excel com base nos dados fornecidos.

    Args:
        output (io.BytesIO): Buffer em memória para escrita do Excel.
        dados (list[dict]): Dados estruturados para o relatório.
        titulo (str): Título do relatório.
        subtitulo (str): Subtítulo do relatório.
        colunas (list[str]): Nomes das colunas da tabela.

    Returns:
        io.BytesIO: Arquivo Excel formatado no buffer.
    """

    LINHA_0 = 0
    LINHA_1 = 1
    LINHA_2 = 2
    LINHA_3 = 3

    ALTURA_COLUNA_30 = 30
    ALTURA_COLUNA_50 = 50
    TAMANHO_MAXIMO_COLUNA = 25

    nome_aba = "Relatório Reclamação Produto"
    with pd.ExcelWriter(output, engine="xlsxwriter") as xlwriter:
        df = pd.DataFrame(dados)

        # Inserindo linhas vazias para espaço de título/subtítulo
        df_auxiliar = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
        df = pd.concat([df_auxiliar, df], ignore_index=True)
        df = pd.concat([df_auxiliar, df], ignore_index=True)
        df = pd.concat([df_auxiliar, df], ignore_index=True)
        df.to_excel(xlwriter, nome_aba, index=False)
        workbook = xlwriter.book
        worksheet = xlwriter.sheets[nome_aba]
        numero_colunas = len(df.columns) - 1
        worksheet.set_row(LINHA_0, ALTURA_COLUNA_50)
        worksheet.set_row(LINHA_1, ALTURA_COLUNA_30)
        worksheet.set_column("A:M", ALTURA_COLUNA_30)

        # Título
        merge_format = workbook.add_format(
            {"align": "center", "bg_color": "#a9d18e", "border_color": "#198459"}
        )
        merge_format.set_align("vcenter")
        merge_format.set_bold()
        worksheet.merge_range(0, 0, 0, numero_colunas, titulo, merge_format)
        worksheet.insert_image(
            "A1", "sme_sigpae_api/static/images/logo-sigpae-light.png"
        )

        # Subtítulo
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()
        cell_format.set_align("vcenter")
        cell_format.set_bold()
        v_center_format = workbook.add_format()
        v_center_format.set_align("vcenter")
        worksheet.merge_range(
            LINHA_1, 0, LINHA_2, numero_colunas, subtitulo, cell_format
        )

        # Cabeçalho
        single_cell_format = workbook.add_format(
            {
                "bg_color": "#a9d18e",
                "align": "center",  # Centralização horizontal
                "valign": "vcenter",  # Centralização vertical
                "bold": True,  # Negrito diretamente na criação
            }
        )
        worksheet.set_row(LINHA_3, 20)
        for index, titulo_coluna in enumerate(colunas):
            worksheet.write(LINHA_3, index, titulo_coluna, single_cell_format)

        # Ajuste dinâmico das colunas
        left_align_format = workbook.add_format({"align": "left", "valign": "vcenter"})
        center_align_format = workbook.add_format(
            {"align": "center", "valign": "vcenter"}
        )
        for i, col in enumerate(df.columns):
            col_data = df[col].astype(str).fillna("")
            max_len = max([len(str(col))] + [len(x) for x in col_data])
            tamanho_final = min(max_len + 1, TAMANHO_MAXIMO_COLUNA)
            if i == 0:
                worksheet.set_column(i, i, tamanho_final, center_align_format)
            else:
                worksheet.set_column(i, i, tamanho_final, left_align_format)

        df.reset_index(drop=True, inplace=True)
    return output.seek(0)
