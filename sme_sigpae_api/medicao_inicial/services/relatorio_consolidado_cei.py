import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import FloatField, Sum
from django.db.models.functions import Cast
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_HEADERS_CEI,
    ORDEM_UNIDADES_GRUPO_CEI,
)
from sme_sigpae_api.escola.models import FaixaEtaria
from sme_sigpae_api.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial
from sme_sigpae_api.medicao_inicial.services.utils import (
    generate_columns,
    gera_colunas_alimentacao,
    get_categorias_dietas,
    get_nome_periodo,
    get_valores_iniciais,
    update_dietas_alimentacoes,
    update_periodos_alimentacoes,
)


def get_alimentacoes_por_periodo(
    solicitacoes: list[SolicitacaoMedicaoInicial],
) -> list[tuple]:
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = get_nome_periodo(medicao)
            lista_faixas = _get_faixas_etarias(medicao)
            periodos_alimentacoes = update_periodos_alimentacoes(
                periodos_alimentacoes, nome_periodo, lista_faixas
            )

            categorias_dietas = get_categorias_dietas(medicao)

            for categoria in categorias_dietas:
                lista_faixa_dietas = _get_lista_alimentacoes_dietas_por_faixa(
                    medicao, categoria
                )
                if nome_periodo.upper() in ["INTEGRAL", "PARCIAL"]:
                    categoria = f"{categoria} - {nome_periodo.upper()}"

                dietas_alimentacoes = update_dietas_alimentacoes(
                    dietas_alimentacoes, categoria, lista_faixa_dietas
                )

    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = generate_columns(dict_periodos_dietas)

    return columns


def _get_faixas_etarias(medicao: Medicao) -> list[int]:
    lista_faixas = list(
        faixa.id
        for faixa in FaixaEtaria.objects.filter(
            id__in=medicao.valores_medicao.filter(nome_campo="frequencia").values_list(
                "faixa_etaria", flat=True
            )
        )
        .distinct()
        .order_by("inicio")
    )

    return lista_faixas


def _get_lista_alimentacoes_dietas_por_faixa(
    medicao: Medicao, categoria: str
) -> list[int]:
    dietas_por_faixa = list(
        faixa.id
        for faixa in FaixaEtaria.objects.filter(
            id__in=medicao.valores_medicao.filter(
                categoria_medicao__nome=categoria, nome_campo="frequencia"
            ).values_list("faixa_etaria", flat=True)
        )
        .distinct()
        .order_by("inicio")
    )

    return dietas_por_faixa


def _sort_and_merge(periodos_alimentacoes: dict, dietas_alimentacoes: dict) -> dict:
    ORDEM_CAMPOS = [
        faixa.id for faixa in FaixaEtaria.objects.filter(ativo=True).order_by("inicio")
    ]

    periodos_alimentacoes = {
        chave: sorted(list(set(valores)), key=lambda valor: ORDEM_CAMPOS.index(valor))
        for chave, valores in periodos_alimentacoes.items()
    }

    dietas_alimentacoes = {
        chave: sorted(list(set(valores)), key=lambda valor: ORDEM_CAMPOS.index(valor))
        for chave, valores in dietas_alimentacoes.items()
    }
    dict_periodos_dietas = {**periodos_alimentacoes, **dietas_alimentacoes}

    dict_periodos_dietas = dict(
        sorted(
            dict_periodos_dietas.items(), key=lambda item: ORDEM_HEADERS_CEI[item[0]]
        )
    )

    return dict_periodos_dietas


def get_valores_tabela(
    solicitacoes: list[SolicitacaoMedicaoInicial],
    colunas: list[tuple],
    tipos_de_unidade: list[str],
) -> list[list[str | float]]:
    valores = []
    for solicitacao in get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade):
        valores_solicitacao_atual = []
        valores_solicitacao_atual += get_valores_iniciais(solicitacao)
        for periodo, faixa_etaria in colunas:
            valores_solicitacao_atual = _processa_periodo_campo(
                solicitacao, periodo, faixa_etaria, valores_solicitacao_atual
            )
        valores.append(valores_solicitacao_atual)
    return valores


def get_solicitacoes_ordenadas(
    solicitacoes: list[SolicitacaoMedicaoInicial], tipos_de_unidade: list[str]
) -> list[SolicitacaoMedicaoInicial]:
    if set(tipos_de_unidade).issubset(ORDEM_UNIDADES_GRUPO_CEI):
        ordem_unidades = ORDEM_UNIDADES_GRUPO_CEI

    return sorted(
        solicitacoes,
        key=lambda k: ordem_unidades[k.escola.tipo_unidade.iniciais],
    )


def _processa_periodo_campo(
    solicitacao: SolicitacaoMedicaoInicial,
    periodo: str,
    faixa_etaria: int,
    valores: list[str],
) -> list[str | float]:
    filtros = _define_filtro(periodo)

    try:
        if "DIETA ESPECIAL" in periodo:
            total = processa_dieta_especial(solicitacao, filtros, faixa_etaria, periodo)
        else:
            total = processa_periodo_regular(
                solicitacao, filtros, faixa_etaria, periodo
            )
        valores.append(total)
    except Exception:
        valores.append("-")
    return valores


def _define_filtro(periodo: str) -> dict:
    filtros = {}
    if periodo == "Solicitações de Alimentação":
        filtros["grupo__nome"] = periodo
    elif "DIETA ESPECIAL" in periodo:
        if "INTEGRAL" in periodo or "PARCIAL" in periodo:
            filtros["periodo_escolar__nome"] = periodo.split(" - ")[-1]
        else:
            filtros["periodo_escolar__nome__in"] = ["MANHA", "TARDE"]
    else:
        filtros["periodo_escolar__nome"] = periodo
    return filtros


def processa_dieta_especial(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict,
    faixa_etaria: int,
    periodo: str,
) -> float | str:
    medicoes = solicitacao.medicoes.filter(**filtros)
    if not medicoes.exists():
        return "-"

    total = 0.0
    periodo = periodo.replace(" - INTEGRAL", "").replace(" - PARCIAL", "")
    for medicao in medicoes:
        soma = _calcula_soma_medicao(medicao, faixa_etaria, periodo)
        if soma is not None:
            total += soma

    return "-" if total == 0.0 else total


def processa_periodo_regular(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict,
    faixa_etaria: int,
    periodo: str,
) -> float | str:
    try:
        medicao = solicitacao.medicoes.get(**filtros)
    except ObjectDoesNotExist:
        return "-"

    categoria = "ALIMENTAÇÃO"
    if periodo == "Solicitações de Alimentação":
        categoria = periodo.upper()

    soma = _calcula_soma_medicao(medicao, faixa_etaria, categoria)
    return soma if soma is not None else "-"


def _calcula_soma_medicao(
    medicao: Medicao, faixa_etaria: int, categoria: str
) -> float | None:
    return (
        medicao.valores_medicao.filter(
            nome_campo="frequencia",
            faixa_etaria_id=faixa_etaria,
            categoria_medicao__nome=categoria,
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))["total"]
    )


def insere_tabela_periodos_na_planilha(
    aba: str,
    colunas: list[tuple],
    linhas: list[list[str | float]],
    writer: pd.ExcelWriter,
) -> pd.DataFrame:
    NOMES_CAMPOS = {
        faixa.id: faixa.__str__() for faixa in FaixaEtaria.objects.filter(ativo=True)
    }
    df = gera_colunas_alimentacao(aba, colunas, linhas, writer, NOMES_CAMPOS)
    return df


def ajusta_layout_tabela(
    workbook: Workbook, worksheet: Worksheet, df: pd.DataFrame
) -> None:
    formatacao_base = {
        "align": "center",
        "valign": "vcenter",
        "font_color": "#FFFFFF",
        "bold": True,
        "border": 1,
        "border_color": "#999999",
    }
    formatacao_integral = workbook.add_format(
        {**formatacao_base, "bg_color": "#198459"}
    )
    formatacao_parcial = workbook.add_format({**formatacao_base, "bg_color": "#D06D12"})
    formatacao_manha = workbook.add_format({**formatacao_base, "bg_color": "#C13FD6"})
    formatacao_tarde = workbook.add_format({**formatacao_base, "bg_color": "#2F80ED"})
    formatacao_dieta_a = workbook.add_format({**formatacao_base, "bg_color": "#20AA73"})
    formatacao_dieta_b = workbook.add_format({**formatacao_base, "bg_color": "#198459"})

    formatacao_level2 = workbook.add_format(
        {
            **formatacao_base,
            "bg_color": "#F7FBF9",
            "font_color": "#000000",
            "text_wrap": True,
        }
    )

    formatacao_level1 = {
        "": {"formatacao": formatacao_level2, "nome": ""},
        "INTEGRAL": {
            "formatacao": formatacao_integral,
            "nome": "INTEGRAL",
        },
        "DIETA ESPECIAL - TIPO A - INTEGRAL": {
            "formatacao": formatacao_integral,
            "nome": "DIETA ESPECIAL - TIPO A",
        },
        "DIETA ESPECIAL - TIPO B - INTEGRAL": {
            "formatacao": formatacao_integral,
            "nome": "DIETA ESPECIAL - TIPO B",
        },
        "PARCIAL": {
            "formatacao": formatacao_parcial,
            "nome": "PARCIAL",
        },
        "DIETA ESPECIAL - TIPO A - PARCIAL": {
            "formatacao": formatacao_parcial,
            "nome": "DIETA ESPECIAL - TIPO A",
        },
        "DIETA ESPECIAL - TIPO B - PARCIAL": {
            "formatacao": formatacao_parcial,
            "nome": "DIETA ESPECIAL - TIPO B",
        },
        "MANHA": {
            "formatacao": formatacao_manha,
            "nome": "MANHA",
        },
        "TARDE": {
            "formatacao": formatacao_tarde,
            "nome": "TARDE",
        },
        "DIETA ESPECIAL - TIPO A": {
            "formatacao": formatacao_dieta_a,
            "nome": "DIETA ESPECIAL - TIPO A",
        },
        "DIETA ESPECIAL - TIPO B": {
            "formatacao": formatacao_dieta_b,
            "nome": "DIETA ESPECIAL - TIPO B",
        },
    }

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(
            2,
            col_num,
            formatacao_level1[value[0]]["nome"],
            formatacao_level1[value[0]]["formatacao"],
        )
        worksheet.write(3, col_num, value[1], formatacao_level2)

    formatacao = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
        }
    )

    worksheet.set_column(0, len(df.columns) - 1, 15, formatacao)
    worksheet.set_column(2, 2, 30)

    worksheet.set_row(4, None, None, {"hidden": True})
    worksheet.set_row(2, 25)
    worksheet.set_row(3, 40)
