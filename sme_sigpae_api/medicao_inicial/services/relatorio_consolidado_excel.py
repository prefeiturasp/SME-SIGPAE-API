import io

import pandas as pd

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_UNIDADES_GRUPO_CEI,
    ORDEM_UNIDADES_GRUPO_EMEF,
    ORDEM_UNIDADES_GRUPO_EMEI,
)
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import DiretoriaRegional, Lote
from sme_sigpae_api.medicao_inicial.services import (
    relatorio_consolidado_cei,
    relatorio_consolidado_emei_emef,
)

from ..models import SolicitacaoMedicaoInicial


def gera_relatorio_consolidado_xlsx(solicitacoes_uuid, tipos_de_unidade, query_params):
    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(uuid__in=solicitacoes_uuid)
    try:
        if set(tipos_de_unidade).issubset(
            ORDEM_UNIDADES_GRUPO_EMEF | ORDEM_UNIDADES_GRUPO_EMEI
        ):
            colunas = relatorio_consolidado_emei_emef.get_alimentacoes_por_periodo(
                solicitacoes
            )
            linhas = relatorio_consolidado_emei_emef.get_valores_tabela(
                solicitacoes, colunas, tipos_de_unidade
            )
        elif set(tipos_de_unidade).issubset(ORDEM_UNIDADES_GRUPO_CEI):
            colunas = relatorio_consolidado_cei.get_alimentacoes_por_periodo(
                solicitacoes
            )
            linhas = relatorio_consolidado_cei.get_valores_tabela(
                solicitacoes, colunas, tipos_de_unidade
            )
        else:
            raise ValueError(f"Unidades inválidas: {tipos_de_unidade}")

        arquivo_excel = _gera_excel(tipos_de_unidade, query_params, colunas, linhas)
    except Exception as e:
        raise e
    return arquivo_excel


def _gera_excel(tipos_de_unidade, query_params, colunas, linhas):
    file = io.BytesIO()

    with pd.ExcelWriter(file, engine="xlsxwriter") as writer:
        mes = query_params.get("mes")
        ano = query_params.get("ano")
        aba = f"Relatório Consolidado {mes}-{ano}"

        workbook = writer.book
        worksheet = workbook.add_worksheet(aba)
        worksheet.set_default_row(20)
        df = _insere_tabela_periodos_na_planilha(
            tipos_de_unidade, aba, colunas, linhas, writer
        )
        _preenche_titulo(workbook, worksheet, df.columns)
        _preenche_linha_dos_filtros_selecionados(
            workbook, worksheet, query_params, df.columns, tipos_de_unidade
        )
        _ajusta_layout_tabela(tipos_de_unidade, workbook, worksheet, df)
        _formata_total_geral(workbook, worksheet, df)

    return file.getvalue()


def _insere_tabela_periodos_na_planilha(tipos_de_unidade, aba, colunas, linhas, writer):
    if set(tipos_de_unidade).issubset(
        ORDEM_UNIDADES_GRUPO_EMEF | ORDEM_UNIDADES_GRUPO_EMEI
    ):
        df = relatorio_consolidado_emei_emef.insere_tabela_periodos_na_planilha(
            aba, colunas, linhas, writer
        )
    elif set(tipos_de_unidade).issubset(ORDEM_UNIDADES_GRUPO_CEI):
        df = relatorio_consolidado_cei.insere_tabela_periodos_na_planilha(
            aba, colunas, linhas, writer
        )
    else:
        raise ValueError(f"Unidades inválidas: {tipos_de_unidade}")

    return df


def _ajusta_layout_tabela(tipos_de_unidade, workbook, worksheet, df):
    if set(tipos_de_unidade).issubset(
        ORDEM_UNIDADES_GRUPO_EMEF | ORDEM_UNIDADES_GRUPO_EMEI
    ):
        relatorio_consolidado_emei_emef.ajusta_layout_tabela(workbook, worksheet, df)
    elif set(tipos_de_unidade).issubset(ORDEM_UNIDADES_GRUPO_CEI):
        relatorio_consolidado_cei.ajusta_layout_tabela(workbook, worksheet, df)
    else:
        raise ValueError(f"Unidades inválidas: {tipos_de_unidade}")


def _formata_total_geral(workbook, worksheet, df):
    ultima_linha = len(df.values) + 4

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


def _preenche_titulo(workbook, worksheet, colunas):
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
    workbook, worksheet, query_params, colunas, tipos_de_unidade
):
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


def _formata_filtros(query_params, tipos_de_unidade):
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
