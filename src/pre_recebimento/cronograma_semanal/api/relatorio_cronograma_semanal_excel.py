"""Geração do Excel do Relatório de Cronogramas Semanais.

Cada linha da planilha é a junção de um cronograma semanal com uma de suas
programações de entrega: um cronograma com três programações ocupa três
linhas, repetindo os dados do cronograma.
"""

import io

import xlsxwriter

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from src.pre_recebimento.cronograma_semanal.api.helpers import (
    primeiro_dia_do_mes,
    q_programacao_no_periodo,
    ultimo_dia_do_mes,
)
from src.pre_recebimento.cronograma_semanal.models import CronogramaSemanal

COLUNAS = [
    "Nº do Cronograma Mensal",
    "Nº do Cronograma Semanal",
    "Empresa",
    "Produto",
    "Quantidade Total do Empenho",
    "Unidade",
    "Custo Unitário",
    "Período Programado Inicial",
    "Período Programado Final",
    "Quantidade de Entrega",
    "Unidade",
    "Nº do Processo SEI",
    "Nº do Empenho",
    "Nº do Contrato",
    "Modalidade/ Tipo",
    "Status",
]

INDICE_COLUNA_CUSTO_UNITARIO = 6
INDICES_COLUNAS_NUMERICAS = (4, 9)

MENSAGEM_SEM_REGISTROS = "Nenhum registro encontrado"

TAMANHO_MAXIMO_COLUNA = 40

LINHA_CABECALHO = 0
PRIMEIRA_LINHA_DE_DADOS = 1


def _sanitiza_texto(valor):
    """Previne Excel formula injection prefixando valores que começam com =, +, - ou @."""
    if valor and isinstance(valor, str) and valor[0] in ("=", "+", "-", "@"):
        return "'" + valor
    return valor or ""


def _formata_data(data):
    """Retorna data formatada como dd/mm/yyyy ou string vazia."""
    if data:
        return data.strftime(FORMATO_DATA_BRASILEIRO)
    return ""


def _unidade_medida(cronograma_mensal):
    """Abreviação da unidade de medida do cronograma mensal."""
    unidade_medida = getattr(cronograma_mensal, "unidade_medida", None)
    return getattr(unidade_medida, "abreviacao", "") if unidade_medida else ""


def _nome_produto(cronograma_mensal):
    ficha_tecnica = getattr(cronograma_mensal, "ficha_tecnica", None)
    produto = getattr(ficha_tecnica, "produto", None) if ficha_tecnica else None
    return getattr(produto, "nome", "") if produto else ""


def _dados_do_contrato(cronograma_mensal):
    """(processo SEI, número do contrato, modalidade) do cronograma mensal."""
    contrato = getattr(cronograma_mensal, "contrato", None)
    if not contrato:
        return "", "", ""

    modalidade = getattr(contrato, "modalidade", None)
    return (
        contrato.processo or "",
        contrato.numero or "",
        getattr(modalidade, "nome", "") if modalidade else "",
    )


def _montar_valores_dados(cronograma_semanal, programacao):
    """Valores de uma linha da planilha, na mesma ordem de ``COLUNAS``."""
    mensal = cronograma_semanal.cronograma_mensal
    unidade = _unidade_medida(mensal)
    processo_sei, numero_contrato, modalidade = _dados_do_contrato(mensal)

    return [
        _sanitiza_texto(getattr(mensal, "numero", "")),
        _sanitiza_texto(cronograma_semanal.numero),
        _sanitiza_texto(getattr(getattr(mensal, "empresa", None), "nome_fantasia", "")),
        _sanitiza_texto(_nome_produto(mensal)),
        getattr(mensal, "qtd_total_empenho", None),
        _sanitiza_texto(unidade),
        getattr(mensal, "custo_unitario_produto", None),
        _formata_data(programacao.data_inicio),
        _formata_data(programacao.data_fim),
        programacao.quantidade,
        _sanitiza_texto(unidade),
        _sanitiza_texto(processo_sei),
        _sanitiza_texto(getattr(mensal, "numero_empenho", "")),
        _sanitiza_texto(numero_contrato),
        _sanitiza_texto(modalidade),
        _sanitiza_texto(cronograma_semanal.get_status_display()),
    ]


def _escreve_cabecalho(workbook, worksheet):
    """Escreve a linha de cabeçalho das colunas, na primeira linha."""
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

    for col_idx, coluna in enumerate(COLUNAS):
        worksheet.write(LINHA_CABECALHO, col_idx, coluna, formato_header)
    worksheet.set_row(LINHA_CABECALHO, 30)


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


def _programacoes_do_cronograma(cronograma_semanal, filtros):
    """Programações do cronograma, recortadas pelo mês de entrega.

    Aplica o mesmo recorte do filtro da tela: quando o período é informado,
    só entram as programações cujo ``data_inicio`` ou ``data_fim`` cai
    dentro dos meses selecionados.
    """
    programacoes = cronograma_semanal.programacoes.all()

    filtros = filtros or {}
    data_inicial = primeiro_dia_do_mes(filtros.get("mes_inicial"))
    data_final = ultimo_dia_do_mes(filtros.get("mes_final"))

    if data_inicial or data_final:
        programacoes = programacoes.filter(
            q_programacao_no_periodo(data_inicial, data_final)
        )

    return programacoes


def _queryset_cronogramas(ids_cronogramas):
    return (
        CronogramaSemanal.objects.filter(id__in=ids_cronogramas)
        .select_related(
            "cronograma_mensal",
            "cronograma_mensal__empresa",
            "cronograma_mensal__unidade_medida",
            "cronograma_mensal__ficha_tecnica__produto",
            "cronograma_mensal__contrato__modalidade",
        )
        .order_by("-alterado_em")
        .distinct()
    )


def gera_relatorio_cronogramas_semanais_xlsx(ids_cronogramas, filtros=None):
    """Gera o arquivo Excel do Relatório de Cronogramas Semanais.

    Args:
        ids_cronogramas: Lista de ids de CronogramaSemanal, já filtrados.
        filtros: Filtros da tela que ainda precisam ser aplicados sobre as
            programações (``mes_inicial`` e ``mes_final``).

    Returns:
        bytes: Conteúdo do arquivo .xlsx.
    """
    cronogramas = _queryset_cronogramas(ids_cronogramas)

    file = io.BytesIO()
    workbook = xlsxwriter.Workbook(file, {"in_memory": True})
    worksheet = workbook.add_worksheet("Cronogramas Semanais")

    # Desabilita a grade padrão para limpeza visual
    worksheet.hide_gridlines(2)

    linhas = [
        _montar_valores_dados(cronograma, programacao)
        for cronograma in cronogramas
        for programacao in _programacoes_do_cronograma(cronograma, filtros)
    ]

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

    formato_dados_moeda = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "font_size": 9,
            "num_format": "R$ #,##0.00",
        }
    )

    linha_atual = PRIMEIRA_LINHA_DE_DADOS
    for valores in linhas:
        for col_idx, valor in enumerate(valores):
            eh_numerica = col_idx in INDICES_COLUNAS_NUMERICAS
            eh_moeda = col_idx == INDICE_COLUNA_CUSTO_UNITARIO

            if (eh_numerica or eh_moeda) and valor is not None:
                worksheet.write_number(
                    linha_atual,
                    col_idx,
                    valor,
                    formato_dados_moeda if eh_moeda else formato_dados_numero,
                )
            elif eh_numerica or eh_moeda:
                worksheet.write(linha_atual, col_idx, "", formato_dados)
            else:
                worksheet.write(linha_atual, col_idx, valor, formato_dados)
            _ajusta_max_length(max_lengths, col_idx, valor)
        linha_atual += 1

    if linha_atual == PRIMEIRA_LINHA_DE_DADOS:
        worksheet.write(linha_atual, 0, MENSAGEM_SEM_REGISTROS, formato_dados)

    _ajusta_largura_colunas(workbook, worksheet, max_lengths)

    workbook.close()
    return file.getvalue()
