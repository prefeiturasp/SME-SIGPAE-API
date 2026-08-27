import io
from datetime import datetime

import xlsxwriter

from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto

COLUNAS = [
    "Nome do Produto",
    "Empresa",
    "Categoria",
    "Programa",
    "Nº de Pregão / Chamada Pública",
    "Fabricante / Produtor, Envasador ou Distribuidor",
    "Data de Validade",
    "Produto é orgânico",
    "Qual o mecanismo de controle?",
    "O produto contém ou pode conter ingredientes/aditivos alergênicos?",
    "O Produto contém glúten?",
    "O produto contém lactose",
    "O produto é líquido?",
    "Peso líquido do Produto na embalagem primária",
    "Unidade de Medida (primária)",
    "Peso líquido do Produto na embalagem secundária",
    "Unidade de Medida (secundária)",
    "Status",
]

# Índices (0-based) das colunas numéricas de peso: 13 e 15
# (colunas 14 e 16 na planilha, 1-based).
INDICES_COLUNAS_NUMERICAS = (13, 15)

TITULO_RELATORIO = "Relatório de Fichas Técnicas"
MENSAGEM_SEM_REGISTROS = "Nenhum registro encontrado"

TAMANHO_MAXIMO_COLUNA = 40


def _sim_nao(valor):
    """True → "Sim"; False/None → "Não"."""
    return "Sim" if valor is True else "Não"


def _nome_fabricante_envasador(ficha):
    """Concatena fabricante e envasador/distribuidor com " / ", ignorando nulos."""
    nomes = []
    if ficha.fabricante and ficha.fabricante.fabricante:
        nomes.append(ficha.fabricante.fabricante.nome)
    if ficha.envasador_distribuidor and ficha.envasador_distribuidor.fabricante:
        nomes.append(ficha.envasador_distribuidor.fabricante.nome)
    return " / ".join(nomes)


def _sanitiza_texto(valor):
    """Previne Excel formula injection prefixando valores que começam com =, +, - ou @."""
    if valor and isinstance(valor, str) and valor[0] in ("=", "+", "-", "@"):
        return "'" + valor
    return valor or ""


def _montar_valores_dados(ficha):
    """Prepara os valores de uma linha de dados (mesma ordem de COLUNAS)."""
    return [
        _sanitiza_texto(ficha.produto.nome) if ficha.produto else "",
        _sanitiza_texto(ficha.empresa.nome_fantasia) if ficha.empresa else "",
        _sanitiza_texto(ficha.get_categoria_display()),
        _sanitiza_texto(ficha.get_programa_display()),
        _sanitiza_texto(ficha.pregao_chamada_publica),
        _sanitiza_texto(_nome_fabricante_envasador(ficha)),
        _sanitiza_texto(ficha.prazo_validade),
        _sim_nao(ficha.organico),
        _sanitiza_texto(ficha.get_mecanismo_controle_display() or ""),
        _sim_nao(ficha.alergenicos),
        _sim_nao(ficha.gluten),
        _sim_nao(ficha.lactose),
        _sim_nao(ficha.produto_eh_liquido),
        ficha.peso_liquido_embalagem_primaria,
        (
            _sanitiza_texto(ficha.unidade_medida_primaria.abreviacao)
            if ficha.unidade_medida_primaria
            else ""
        ),
        ficha.peso_liquido_embalagem_secundaria,
        (
            _sanitiza_texto(ficha.unidade_medida_secundaria.abreviacao)
            if ficha.unidade_medida_secundaria
            else ""
        ),
        _sanitiza_texto(ficha.get_status_display()),
    ]


def _escreve_cabecalho(workbook, worksheet):
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
    worksheet.merge_range(0, 0, 0, len(COLUNAS) - 1, TITULO_RELATORIO, formato_titulo)
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
    except Exception:  # nosec
        pass  # Segue sem a imagem se o arquivo não for encontrado

    # Subtítulo (linha 1) - data de extração
    worksheet.merge_range(
        1,
        0,
        1,
        len(COLUNAS) - 1,
        f"Data de extração: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        formato_subtitulo,
    )
    worksheet.set_row(1, 30)

    # Linha de cabeçalho das colunas (linha 2)
    for col_idx, coluna in enumerate(COLUNAS):
        worksheet.write(2, col_idx, coluna, formato_header)
    worksheet.set_row(2, 30)


def _ajusta_max_length(max_lengths, col_idx, valor):
    """Compara e atualiza o tamanho máximo de uma coluna."""
    if valor is None:
        return
    tamanho = len(str(valor))
    if tamanho > max_lengths[col_idx]:
        max_lengths[col_idx] = tamanho


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


def gera_relatorio_fichas_tecnicas_xlsx(fichas_ids):
    """Gera o arquivo Excel do Relatório de Fichas Técnicas.

    Args:
        fichas_ids: Lista de ids de FichaTecnicaDoProduto.

    Returns:
        bytes: Conteúdo do arquivo .xlsx.
    """
    fichas = (
        FichaTecnicaDoProduto.objects.filter(id__in=fichas_ids)
        .select_related(
            "produto",
            "empresa",
            "fabricante__fabricante",
            "envasador_distribuidor__fabricante",
            "unidade_medida_primaria",
            "unidade_medida_secundaria",
        )
        .order_by("-criado_em")
    )

    file = io.BytesIO()
    workbook = xlsxwriter.Workbook(file, {"in_memory": True})
    worksheet = workbook.add_worksheet("Fichas Técnicas")

    # Desabilita a grade padrão para limpeza visual
    worksheet.hide_gridlines(2)

    _escreve_cabecalho(workbook, worksheet)

    max_lengths = [len(coluna) for coluna in COLUNAS]

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
    for ficha in fichas:
        valores = _montar_valores_dados(ficha)
        for col_idx, valor in enumerate(valores):
            if col_idx in INDICES_COLUNAS_NUMERICAS:
                if valor is not None:
                    worksheet.write_number(
                        linha_atual, col_idx, valor, formato_dados_numero
                    )
                else:
                    worksheet.write(linha_atual, col_idx, "", formato_dados)
            else:
                worksheet.write(linha_atual, col_idx, valor, formato_dados)
            _ajusta_max_length(max_lengths, col_idx, valor)
        linha_atual += 1

    if linha_atual == 3:
        worksheet.write(linha_atual, 0, MENSAGEM_SEM_REGISTROS, formato_dados)

    _ajusta_largura_colunas(workbook, worksheet, max_lengths)

    workbook.close()
    return file.getvalue()
