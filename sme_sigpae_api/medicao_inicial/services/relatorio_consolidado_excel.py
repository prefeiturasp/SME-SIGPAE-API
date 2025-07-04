import io
from uuid import UUID

import pandas as pd
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_UNIDADES_GRUPO_CEI,
    ORDEM_UNIDADES_GRUPO_CEMEI,
    ORDEM_UNIDADES_GRUPO_EMEBS,
    ORDEM_UNIDADES_GRUPO_EMEF,
    ORDEM_UNIDADES_GRUPO_EMEI,
)
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import DiretoriaRegional, Lote
from sme_sigpae_api.medicao_inicial.services import (
    relatorio_consolidado_cei,
    relatorio_consolidado_cemei,
    relatorio_consolidado_emebs,
    relatorio_consolidado_emei_emef,
)

from ..models import SolicitacaoMedicaoInicial


def gera_relatorio_consolidado_xlsx(
    solicitacoes_uuid: list[UUID], tipos_de_unidade: list[str], query_params: dict
) -> bytes:
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
):
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
