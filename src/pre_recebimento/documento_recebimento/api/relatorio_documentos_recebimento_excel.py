import io
from datetime import datetime

from src.pre_recebimento.documento_recebimento.api.serializers.serializers import (
    calcular_saldo_laudo,
)

COLUNAS = [
    "Nº do Cronograma",
    "Produto",
    "Empresa",
    "Nº do Pregão ou Chamada Pública",
    "Nº do Processo SEI",
    "Nº do Laudo",
    "Status",
    "Nome do Laboratório",
    "Data de Fabricação",
    "Data de Validade",
    "Nº do(s) Lote(s) do Laudo",
    "Data de Fabricação Até",
    "Data Máxima de Recebimento",
    "Data de Conclusão do Laudo",
    "Unidade",
    "Quantidade Total do Laudo",
    "Saldo Inicial do Laudo",
    "Saldo Atual",
    "Obs",
    "Solicitação de Correção",
]


def _formata_data(data):
    """Retorna data formatada como dd/mm/yyyy ou string vazia."""
    if data:
        return data.strftime("%d/%m/%Y")
    return ""


def _formata_numero(valor):
    """Retorna valor numérico formatado ou string vazia."""
    if valor is not None:
        return float(valor)
    return ""


def _sanitiza_texto(valor):
    """Previne Excel formula injection prefixando valores que começam com =, +, - ou @."""
    if valor and isinstance(valor, str) and valor and valor[0] in ("=", "+", "-", "@"):
        return "'" + valor
    return valor or ""


def _escreve_cabecalho(workbook, worksheet, totalizadores):
    """Escreve cabeçalho com logo, título, subtítulo e linha de colunas."""
    formato_titulo = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#A9D18E",
            "align": "center",
            "valign": "vcenter",
            "font_size": 14,
        }
    )

    formato_subtitulo = workbook.add_format(
        {
            "bold": False,
            "bg_color": "#D9EAD3",
            "align": "center",
            "valign": "vcenter",
            "font_size": 10,
            "text_wrap": True,
        }
    )

    formato_header = workbook.add_format(
        {
            "bold": True,
            "bg_color": "#A9D18E",
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "text_wrap": True,
            "font_size": 9,
        }
    )

    # Logo + Título (linha 0)
    worksheet.merge_range(
        0, 0, 0, len(COLUNAS) - 1, "Relatório Documentos de Recebimento", formato_titulo
    )
    worksheet.set_row(0, 50)

    try:
        worksheet.insert_image(
            0,
            0,
            "src/relatorios/static/images/logo-sigpae.png",
            {
                "x_offset": 10,
                "y_offset": 5,
                "x_scale": 0.08,
                "y_scale": 0.08,
            },
        )
    except Exception:
        pass  # Segue sem a imagem se o arquivo não for encontrado

    # Subtítulo (linha 1) - totalizadores + data/hora
    total_geral = totalizadores.get("Total de Documentos Recebidos", 0)
    pendentes = totalizadores.get("Total de Pendentes de Aprovação", 0)
    correcao = totalizadores.get("Total de Enviados para Correção", 0)
    aprovados = totalizadores.get("Total de Aprovados", 0)
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

    texto_totalizadores = (
        f"Total de Documentos Recebidos: {total_geral}  |  "
        f"Pendentes de Aprovação: {pendentes}  |  "
        f"Enviados para Correção: {correcao}  |  "
        f"Aprovados: {aprovados}  |  "
        f"Data/Hora da extração: {data_hora}"
    )

    worksheet.merge_range(
        1, 0, 1, len(COLUNAS) - 1, texto_totalizadores, formato_subtitulo
    )
    worksheet.set_row(1, 30)

    # Linha de cabeçalho das colunas (linha 2)
    for col_idx, coluna in enumerate(COLUNAS):
        worksheet.write(2, col_idx, coluna, formato_header)
    worksheet.set_row(2, 30)


def _escreve_dados(workbook, worksheet, queryset, max_lengths):
    """Itera sobre os cronogramas e escreve os dados linha a linha."""
    formato_dados = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "font_size": 9,
            "text_wrap": True,
        }
    )

    formato_dados_numero = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "font_size": 9,
            "num_format": "#,##0.00",
        }
    )

    linha_atual = 3

    for cronograma in queryset:
        docs = list(cronograma.documentos_de_recebimento.all())

        if not docs:
            continue

        for doc in docs:
            datas = list(doc.datas_fabricacao_e_prazos.all())

            if datas:
                for data_item in datas:
                    _escreve_linha(
                        worksheet,
                        linha_atual,
                        cronograma,
                        doc,
                        data_item,
                        formato_dados,
                        formato_dados_numero,
                        max_lengths,
                    )
                    linha_atual += 1
            else:
                _escreve_linha(
                    worksheet,
                    linha_atual,
                    cronograma,
                    doc,
                    None,
                    formato_dados,
                    formato_dados_numero,
                    max_lengths,
                )
                linha_atual += 1

    return linha_atual


def _prepara_valores_linha(cronograma, doc, data_item):
    """Prepara todos os valores de uma linha para escrita na planilha."""
    contrato = cronograma.contrato if hasattr(cronograma, "contrato") else None

    num_pregao_chamada = ""
    if contrato:
        num_pregao_chamada = contrato.pregao_chamada_publica or ""

    numero_processo_sei = contrato.processo if contrato else ""

    numero_laudo = _sanitiza_texto(doc.numero_laudo)
    status_doc = doc.get_status_display() if hasattr(doc, "get_status_display") else ""
    nome_laboratorio = _sanitiza_texto(doc.laboratorio.nome if doc.laboratorio else "")
    numero_lote_laudo = _sanitiza_texto(doc.numero_lote_laudo)

    data_final_lote = _formata_data(doc.data_final_lote)
    data_conclusao = _formata_data(doc.criado_em)

    unidade_medida = doc.unidade_medida.abreviacao if doc.unidade_medida else ""

    quantidade_laudo = _formata_numero(doc.quantidade_laudo)
    saldo_inicial = quantidade_laudo
    saldo_atual = _formata_numero(calcular_saldo_laudo(doc))

    correcao = _sanitiza_texto(doc.correcao_solicitada)

    data_fabricacao = ""
    data_validade = ""
    data_maxima_recebimento = ""

    if data_item:
        data_fabricacao = _formata_data(data_item.data_fabricacao)
        data_validade = _formata_data(data_item.data_validade)
        data_maxima_recebimento = _formata_data(data_item.data_maxima_recebimento)

    valores = [
        cronograma.numero or "",
        cronograma.ficha_tecnica.produto.nome
        if cronograma.ficha_tecnica and cronograma.ficha_tecnica.produto
        else "",
        cronograma.empresa.razao_social if cronograma.empresa else "",
        num_pregao_chamada,
        numero_processo_sei,
        numero_laudo,
        status_doc,
        nome_laboratorio,
        data_fabricacao,
        data_validade,
        numero_lote_laudo,
        data_final_lote,
        data_maxima_recebimento,
        data_conclusao,
        unidade_medida,
    ]

    valores_numericos = [
        (15, quantidade_laudo),
        (16, saldo_inicial),
        (17, saldo_atual),
    ]

    return {
        "valores": valores,
        "valores_numericos": valores_numericos,
        "correcao": correcao,
    }


def _escreve_linha(worksheet, linha, cronograma, doc, data_item, fmt, fmt_numero, max_lengths=None):
    """Escreve uma única linha de dados na planilha."""
    dados = _prepara_valores_linha(cronograma, doc, data_item)
    valores = dados["valores"]
    valores_numericos = dados["valores_numericos"]
    correcao = dados["correcao"]

    # Escreve colunas de texto (índices 0 a 14)
    for col_idx, valor in enumerate(valores):
        worksheet.write(linha, col_idx, valor, fmt)

    # Escreve colunas numéricas (índices 15, 16, 17)
    for col_idx, valor in valores_numericos:
        if valor != "":
            worksheet.write_number(linha, col_idx, valor, fmt_numero)
        else:
            worksheet.write(linha, col_idx, "", fmt)

    # Escreve colunas de texto no final (índices 18, 19)
    worksheet.write(linha, 18, _sanitiza_texto(cronograma.observacoes), fmt)
    worksheet.write(linha, 19, correcao, fmt)

    _atualiza_max_lengths(max_lengths, valores, valores_numericos, cronograma, correcao)


def _ajusta_max_length(max_lengths, col_idx, valor):
    """Compara e atualiza o tamanho máximo de uma coluna."""
    tamanho = len(str(valor))
    if tamanho > max_lengths[col_idx]:
        max_lengths[col_idx] = tamanho


def _atualiza_max_lengths(max_lengths, valores, valores_numericos, cronograma, correcao):
    """Atualiza as larguras máximas das colunas baseado no conteúdo escrito."""
    if max_lengths is None:
        return
    for col_idx, valor in enumerate(valores):
        _ajusta_max_length(max_lengths, col_idx, valor)
    for col_idx in [15, 16, 17]:
        idx = col_idx - 15
        if idx < len(valores_numericos):
            _ajusta_max_length(max_lengths, col_idx, valores_numericos[idx][1])
    _ajusta_max_length(max_lengths, 18, _sanitiza_texto(cronograma.observacoes))
    _ajusta_max_length(max_lengths, 19, correcao)


TAMANHO_MAXIMO_COLUNA = 40


def _ajusta_largura_colunas(workbook, worksheet, max_lengths):
    """Ajusta a largura das colunas dinamicamente baseado no conteúdo."""
    formato = workbook.add_format()
    formato.set_align("center")
    formato.set_align("vcenter")

    for col_idx, tamanho in enumerate(max_lengths):
        largura = min(tamanho + 2, TAMANHO_MAXIMO_COLUNA)
        if largura < 10:
            largura = 10
        worksheet.set_column(col_idx, col_idx, largura, formato)


def gera_relatorio_documentos_recebimento_xlsx(queryset, totalizadores):
    """Gera o arquivo Excel do Relatório Documentos de Recebimento.

    Args:
        queryset: QuerySet de Cronograma com documentos_de_recebimento
                  pré-carregados (select_related + prefetch_related).
        totalizadores: Dict com os totalizadores dos cards.

    Returns:
        bytes: Conteúdo do arquivo .xlsx.
    """
    file = io.BytesIO()

    # Usa xlsxwriter que é a engine padrão do projeto
    import xlsxwriter

    workbook = xlsxwriter.Workbook(file, {"in_memory": True})
    worksheet = workbook.add_worksheet("Docs Recebimento")

    # Desabilita a grade padrão para limpeza visual
    worksheet.hide_gridlines(2)

    _escreve_cabecalho(workbook, worksheet, totalizadores)
    max_lengths = [len(c) for c in COLUNAS]
    _escreve_dados(workbook, worksheet, queryset, max_lengths)
    _ajusta_largura_colunas(workbook, worksheet, max_lengths)

    workbook.close()
    return file.getvalue()
