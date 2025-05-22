import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import FloatField, Sum
from django.db.models.functions import Cast

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_HEADERS_CEI,
    ORDEM_UNIDADES_GRUPO_CEI,
)
from sme_sigpae_api.escola.models import FaixaEtaria, PeriodoEscolar

from ..models import CategoriaMedicao


def get_alimentacoes_por_periodo(solicitacoes):
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = _get_nome_periodo(medicao)
            lista_faixas = _get_faixas_etarias(medicao)
            periodos_alimentacoes = _update_periodos_alimentacoes(
                periodos_alimentacoes, nome_periodo, lista_faixas
            )

            categorias_dietas = _get_categorias_dietas(medicao)

            for categoria in categorias_dietas:
                lista_faixa_dietas = _get_lista_alimentacoes_dietas_por_faixa(
                    medicao, categoria
                )
                dietas_alimentacoes = _update_dietas_alimentacoes_por_faixa(
                    dietas_alimentacoes, categoria, lista_faixa_dietas
                )

    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = _generate_columns(dict_periodos_dietas)

    return columns


def _get_nome_periodo(medicao):
    return (
        medicao.periodo_escolar.nome
        if not medicao.grupo
        else (
            f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
            if medicao.periodo_escolar
            else medicao.grupo.nome
        )
    )


def _get_faixas_etarias(medicao):
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


def _update_periodos_alimentacoes(
    periodos_alimentacoes, nome_periodo, lista_alimentacoes
):
    if nome_periodo in periodos_alimentacoes:
        periodos_alimentacoes[nome_periodo] += lista_alimentacoes
    else:
        periodos_alimentacoes[nome_periodo] = lista_alimentacoes
    return periodos_alimentacoes


def _get_categorias_dietas(medicao):
    return list(
        medicao.valores_medicao.exclude(
            categoria_medicao__nome__icontains="ALIMENTAÇÃO"
        )
        .values_list("categoria_medicao__nome", flat=True)
        .distinct()
    )


def _get_lista_alimentacoes_dietas_por_faixa(medicao, categoria):
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


def _update_dietas_alimentacoes_por_faixa(
    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
):
    if lista_alimentacoes_dietas:
        if categoria in dietas_alimentacoes:
            dietas_alimentacoes[categoria] += lista_alimentacoes_dietas
        else:
            dietas_alimentacoes[categoria] = lista_alimentacoes_dietas
    return dietas_alimentacoes


def _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes):
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


def _generate_columns(dict_periodos_dietas):
    columns = [
        (chave, valor)
        for chave, valores in dict_periodos_dietas.items()
        for valor in valores
    ]
    return columns


def get_valores_tabela(solicitacoes, colunas, tipos_de_unidade):
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    valores = []
    for solicitacao in get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade):
        valores_solicitacao_atual = []
        valores_solicitacao_atual += _get_valores_iniciais(solicitacao)
        for periodo, faixa_etaria in colunas:
            valores_solicitacao_atual = _processa_periodo_campo(
                solicitacao,
                periodo,
                faixa_etaria,
                valores_solicitacao_atual,
                dietas_especiais,
                periodos_escolares,
            )
        valores.append(valores_solicitacao_atual)
    return valores


def get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade):
    if set(tipos_de_unidade).issubset(ORDEM_UNIDADES_GRUPO_CEI):
        ordem_unidades = ORDEM_UNIDADES_GRUPO_CEI

    return sorted(
        solicitacoes,
        key=lambda k: ordem_unidades[k.escola.tipo_unidade.iniciais],
    )


def _get_valores_iniciais(solicitacao):
    return [
        solicitacao.escola.tipo_unidade.iniciais,
        solicitacao.escola.codigo_eol,
        solicitacao.escola.nome,
    ]


def _processa_periodo_campo(
    solicitacao, periodo, faixa_etaria, valores, dietas_especiais, periodos_escolares
):
    filtros = _define_filtro(periodo, dietas_especiais, periodos_escolares)

    try:
        if periodo in dietas_especiais:
            total = processa_dieta_especial(solicitacao, filtros, faixa_etaria, periodo)
        else:
            total = _processa_periodo_regular(
                solicitacao, filtros, faixa_etaria, periodo
            )
        valores.append(total)
    except Exception:
        valores.append("-")
    return valores


def _define_filtro(periodo, dietas_especiais, periodos_escolares):
    filtros = {}
    if periodo in ["Solicitações de Alimentação"]:
        filtros["grupo__nome"] = periodo
    elif periodo in dietas_especiais:
        filtros["periodo_escolar__nome__in"] = periodos_escolares
    else:
        filtros["periodo_escolar__nome"] = periodo
    return filtros


def processa_dieta_especial(solicitacao, filtros, faixa_etaria, periodo):
    medicoes = solicitacao.medicoes.filter(**filtros)
    if not medicoes.exists():
        return "-"

    total = 0.0
    for medicao in medicoes:
        soma = _calcula_soma_medicao(medicao, faixa_etaria, periodo)
        if soma is not None:
            total += soma

    return "-" if total == 0.0 else total


def _processa_periodo_regular(solicitacao, filtros, faixa_etaria, periodo):
    try:
        medicao = solicitacao.medicoes.get(**filtros)
    except ObjectDoesNotExist:
        return "-"

    categoria = "ALIMENTAÇÃO"
    if periodo == "Solicitações de Alimentação":
        categoria = periodo.upper()

    soma = _calcula_soma_medicao(medicao, faixa_etaria, categoria)
    return soma if soma is not None else "-"


def _calcula_soma_medicao(medicao, faixa_etaria, categoria):
    return (
        medicao.valores_medicao.filter(
            nome_campo="frequencia",
            faixa_etaria_id=faixa_etaria,
            categoria_medicao__nome=categoria,
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))["total"]
    )


def insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer):
    NOMES_CAMPOS = {
        faixa.id: faixa.__str__() for faixa in FaixaEtaria.objects.filter(ativo=True)
    }

    colunas_fixas = [
        ("", "Tipo"),
        ("", "Cód. EOL"),
        ("", "Unidade Escolar"),
    ]
    headers = [
        (
            chave.upper() if chave != "Solicitações de Alimentação" else "",
            NOMES_CAMPOS[valor],
        )
        for chave, valor in colunas
    ]
    headers = colunas_fixas + headers

    index = pd.MultiIndex.from_tuples(headers)
    df = pd.DataFrame(
        data=linhas,
        index=None,
        columns=index,
    )
    df.loc["TOTAL"] = df.apply(pd.to_numeric, errors="coerce").sum()

    df.to_excel(writer, sheet_name=aba, startrow=2, startcol=-1)
    return df


def ajusta_layout_tabela(workbook, worksheet, df):
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
        "": formatacao_level2,
        "INTEGRAL": formatacao_integral,
        "PARCIAL": formatacao_parcial,
        "MANHA": formatacao_manha,
        "TARDE": formatacao_tarde,
        "DIETA ESPECIAL - TIPO A": formatacao_dieta_a,
        "DIETA ESPECIAL - TIPO B": formatacao_dieta_b,
    }

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(2, col_num, value[0], formatacao_level1[value[0]])
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
