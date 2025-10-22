import io
from uuid import UUID

import pandas as pd
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_UNIDADES_GRUPO_CEI,
    ORDEM_UNIDADES_GRUPO_CEMEI,
    ORDEM_UNIDADES_GRUPO_CIEJA_CMCT,
    ORDEM_UNIDADES_GRUPO_EMEBS,
    ORDEM_UNIDADES_GRUPO_EMEF,
    ORDEM_UNIDADES_GRUPO_EMEI,
)
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import DiretoriaRegional, Lote
from sme_sigpae_api.medicao_inicial.services import (
    relatorio_consolidado_cei,
    relatorio_consolidado_cemei,
    relatorio_consolidado_cieja_cmct,
    relatorio_consolidado_emebs,
    relatorio_consolidado_emei_emef,
)

from ..models import SolicitacaoMedicaoInicial


def gera_relatorio_consolidado_xlsx(
    solicitacoes_uuid: list[UUID], tipos_de_unidade: list[str], query_params: dict
) -> bytes:
    """
    Gera relatório consolidado em formato XLSX baseado nas solicitações fornecidas.

    Função principal que coordena a geração completa do relatório consolidado, desde a obtenção dos dados do banco
    até a criação do arquivo Excel formatado.

    Args:
        solicitacoes_uuid (list[UUID]): Lista de UUIDs das solicitações de medição inicial a serem incluídas no relatório.
        tipos_de_unidade (list[str]): Lista de tipos de unidade (siglas) para determinar o módulo de formatação apropriado.
        query_params (dict): Dicionário com parâmetros da query string contendo filtros aplicados (mes, ano, dre, lotes) para formatação do relatório.

    Raises:
        e: Repassa quaisquer exceções ocorridas no processo de geração para permitir tratamento externo.

    Returns:
        bytes: Conteúdo binário do arquivo Excel gerado, pronto para ser salvo em disco ou enviado como resposta HTTP.
    """
    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(uuid__in=solicitacoes_uuid)
    try:
        modulo_da_unidade, parametros = _obter_modulo_da_unidade(tipos_de_unidade)
        colunas = modulo_da_unidade.get_alimentacoes_por_periodo(solicitacoes)
        linhas = modulo_da_unidade.get_valores_tabela(
            solicitacoes, colunas, *parametros
        )

        arquivo_excel = _gera_excel(
            tipos_de_unidade, query_params, colunas, linhas, modulo_da_unidade
        )
    except Exception as e:
        raise e
    return arquivo_excel


def _obter_modulo_da_unidade(tipos_de_unidade: list[str]) -> tuple:
    """
    Identifica o módulo de relatório consolidado apropriado para os tipos de unidade.

    Determina qual módulo de geração de relatório consolidado deve ser utilizado baseado nos tipos de unidade fornecidos,
    seguindo uma estratégia de prioridade definida por grupos pré-estabelecidos

    Args:
        tipos_de_unidade (list[str]): Lista de tipos de unidade (siglas) para as quais identificar o módulo apropriado.

    Raises:
        ValueError: Se nenhum módulo for encontrado para os tipos de unidade fornecidos, indicando que os tipos não estão mapeados
        em nenhum grupo conhecido.

    Returns:
        tuple: Tupla contendo:
            - modulo: Módulo de relatório consolidado a ser utilizado
            - parametros (list): Lista de parâmetros a serem passados para o módulo
    """
    estrategias = [
        {
            "unidades": ORDEM_UNIDADES_GRUPO_EMEF | ORDEM_UNIDADES_GRUPO_EMEI,
            "modulo": relatorio_consolidado_emei_emef,
            "parametros": [tipos_de_unidade],
        },
        {
            "unidades": ORDEM_UNIDADES_GRUPO_CEI,
            "modulo": relatorio_consolidado_cei,
            "parametros": [tipos_de_unidade],
        },
        {
            "unidades": ORDEM_UNIDADES_GRUPO_CEMEI,
            "modulo": relatorio_consolidado_cemei,
            "parametros": [],
        },
        {
            "unidades": ORDEM_UNIDADES_GRUPO_EMEBS,
            "modulo": relatorio_consolidado_emebs,
            "parametros": [],
        },
        {
            "unidades": ORDEM_UNIDADES_GRUPO_CIEJA_CMCT,
            "modulo": relatorio_consolidado_cieja_cmct,
            "parametros": [],
        },
    ]
    for estrategia in estrategias:
        if set(tipos_de_unidade).issubset(estrategia["unidades"]):
            return estrategia["modulo"], estrategia["parametros"]
    raise ValueError(f"Unidades inválidas: {tipos_de_unidade}")


def _gera_excel(
    tipos_de_unidade: list[str],
    query_params: dict,
    colunas: list[tuple],
    linhas: list[list[str | float]],
    modulo_da_unidade: object,
) -> bytes:
    """
    Gera arquivo Excel em memória com relatório consolidado formatado.

    Orquestra a criação completa de um relatório Excel, incluindo estruturação
    dos dados, aplicação de formatação visual, inserção de títulos e filtros,
    e ajustes de layout específicos para o tipo de unidade.

    Args:
        tipos_de_unidade (list[str]): Lista de tipos de unidade (siglas) para formatação específica e ajustes de layout.
        query_params (dict): Dicionário com parâmetros da query string contendo filtros aplicados (mes, ano, dre, lotes).
        colunas (list[tuple]): Lista de tuplas no formato (período, campo) definindo a estrutura das colunas da tabela.
        linhas (list[list[str | float]]): Matriz de dados onde cada lista interna representa uma linha do relatório.
        modulo_da_unidade (object): Módulo específico contendo funções de formatação para o tipo de unidade (EMEF/EMEI, CEI, CEMEI, etc.).

    Returns:
        bytes: Conteúdo binário do arquivo Excel gerado, pronto para ser salvo em disco ou enviado como resposta HTTP.

    """
    file = io.BytesIO()

    with pd.ExcelWriter(file, engine="xlsxwriter") as writer:
        mes = query_params.get("mes")
        ano = query_params.get("ano")
        aba = f"Relatório Consolidado {mes}-{ano}"

        workbook = writer.book
        worksheet = workbook.add_worksheet(aba)
        worksheet.set_default_row(20)
        df = modulo_da_unidade.insere_tabela_periodos_na_planilha(
            aba, colunas, linhas, writer
        )
        _preenche_titulo(workbook, worksheet, df.columns)
        _preenche_linha_dos_filtros_selecionados(
            workbook, worksheet, query_params, df.columns, tipos_de_unidade
        )
        modulo_da_unidade.ajusta_layout_tabela(workbook, worksheet, df)
        _formata_total_geral(workbook, worksheet, df, tipos_de_unidade)

    return file.getvalue()


def _formata_total_geral(
    workbook: Workbook,
    worksheet: Worksheet,
    df: pd.DataFrame,
    tipos_de_unidade: list[str] | None = None,
) -> None:
    """
    Adiciona e formata a linha de total geral na planilha Excel.

    Insere uma linha mesclada com o label "TOTAL" na parte inferior da tabela,
    com tratamento especial para unidades do grupo EMEBS que requerem linha adicional.

    Args:
        workbook (Workbook): Objeto Workbook do xlsxwriter para criação de formatos personalizados.
        worksheet (Worksheet): Objeto Worksheet onde o total será inserido.
        df (pd.DataFrame): DataFrame com os dados da tabela, usado para calcular a posição da linha de total.
        tipos_de_unidade (list[str] | None, optional): Lista de tipos de unidade (siglas) para verificar se pertencem ao grupo EMEBS
        e ajustar a posição do total. Defaults to None.

    Returns:
        None: A função modifica o worksheet in-place e não retorna valores.
    """
    linha_adicional = 0
    if tipos_de_unidade is not None and set(tipos_de_unidade).issubset(
        ORDEM_UNIDADES_GRUPO_EMEBS
    ):
        linha_adicional = 1
    ultima_linha = len(df.values) + 4 + linha_adicional

    estilo_base = {
        "align": "center",
        "valign": "vcenter",
        "bold": True,
    }
    formatacao = workbook.add_format({**estilo_base})

    worksheet.merge_range(
        ultima_linha,
        0,
        ultima_linha,
        2,
        "TOTAL",
        formatacao,
    )
    worksheet.set_row(ultima_linha, 20, formatacao)


def _preenche_titulo(
    workbook: Workbook, worksheet: Worksheet, colunas: pd.MultiIndex
) -> None:
    """
    Adiciona e formata o título principal do relatório na planilha Excel.

    Cria um título mesclado centralizado na primeira linha da planilha com  formatação visual destacada, servindo como cabeçalho
    principal para o relatório de medição inicial.

    Args:
        workbook (Workbook): Objeto Workbook do xlsxwriter para criação de formatos personalizados.
        worksheet (Worksheet): Objeto Worksheet onde o título será inserido.
        colunas (pd.MultiIndex): MultiIndex das colunas do DataFrame, usado para determinar a largura do título mesclado.

    Returns:
        None: A função modifica o worksheet in-place e não retorna valores.
    """
    formatacao = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#D6F2E7",
            "font_color": "#42474A",
            "bold": True,
        }
    )

    worksheet.merge_range(
        0,
        0,
        0,
        len(colunas) - 1,
        "Relatório de Totalização da Medição Inicial do Serviço de Fornecimento da Alimentação Escolar",
        formatacao,
    )
    worksheet.set_row(0, 30)


def _preenche_linha_dos_filtros_selecionados(
    workbook: Workbook,
    worksheet: Worksheet,
    query_params: dict,
    colunas: pd.MultiIndex,
    tipos_de_unidade: list[str],
) -> None:
    """
    Adiciona e formata a linha de filtros selecionados na planilha Excel.

    Insere na segunda linha da planilha uma célula mesclada contendo a descrição formatada dos filtros aplicados ao relatório,
    utilizando formatação visual que destaca os critérios de filtragem.

    Args:
        workbook (Workbook): Objeto Workbook do xlsxwriter para criação de formatos personalizados.
        worksheet (Worksheet):  Objeto Worksheet onde os filtros serão inseridos.
        query_params (dict): Dicionário com parâmetros da query string contendo os filtros aplicados (mes, ano, dre, lotes).
        colunas (pd.MultiIndex): MultiIndex das colunas do DataFrame, usado para determinar a largura da célula mesclada.
        tipos_de_unidade (list[str]): Lista de tipos de unidade (siglas) selecionados para o relatório.

    Returns:
        None: A função modifica o worksheet in-place e não retorna valores.
    """
    filtros = _formata_filtros(query_params, tipos_de_unidade)
    formatacao = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#EAFFF6",
            "font_color": "#0C6B45",
            "bold": True,
        }
    )

    worksheet.merge_range(1, 0, 1, len(colunas) - 1, filtros.upper(), formatacao)
    worksheet.set_row(1, 30)


def _formata_filtros(query_params: dict, tipos_de_unidade: list[str]) -> str:
    """
    Formata string descritiva dos filtros aplicados no relatório.

    Constrói uma string legível que descreve todos os filtros aplicados
    na geração do relatório, incluindo período, DRE, lotes e tipos de unidade.

    Args:
        query_params (dict): Dicionário com parâmetros da query string contendo os filtros aplicados (mes, ano, dre, lotes).
        tipos_de_unidade (list[str]): Lista de tipos de unidade (siglas) selecionados para o relatório.

    Returns:
        str: String formatada com a descrição dos filtros no formato: "Mês/Ano - DRE - Lotes - Tipos de Unidade"
    """
    mes = query_params.get("mes")
    ano = query_params.get("ano")
    filtros = f"{converte_numero_em_mes(int(mes))}/{ano}"

    dre_uuid = query_params.get("dre")
    if dre_uuid:
        dre = DiretoriaRegional.objects.filter(uuid=dre_uuid).first()
        filtros += f" - {dre.nome}"

    lotes_uuid = query_params.get("lotes")
    if lotes_uuid:
        lotes = Lote.objects.filter(uuid__in=lotes_uuid).values_list("nome", flat=True)
        filtros += f" - {', '.join(lotes)}"

    if tipos_de_unidade:
        filtros += f" - {', '.join(tipos_de_unidade)}"

    return filtros
