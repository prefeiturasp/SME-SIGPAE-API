import pandas as pd
from django.db.models import FloatField, Q, Sum
from django.db.models.functions import Cast

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_HEADERS_CEI,
    ORDEM_UNIDADES_GRUPO_CEI,
)
from sme_sigpae_api.dados_comuns.utils import converte_numero_em_mes
from sme_sigpae_api.escola.models import (
    DiretoriaRegional,
    FaixaEtaria,
    Lote,
    PeriodoEscolar,
)
from sme_sigpae_api.escola.utils import string_to_faixa

from ..models import CategoriaMedicao


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


def _get_alimentacoes_por_periodo(solicitacoes):
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = _get_nome_periodo(medicao)
            # lista_alimentacoes = _get_lista_alimentacoes(medicao, nome_periodo)
            lista_faixas = _get_faixas_etarias(medicao, nome_periodo)
            periodos_alimentacoes = _update_periodos_alimentacoes(
                periodos_alimentacoes, nome_periodo, lista_faixas
            )

            categorias_dietas = _get_categorias_dietas(medicao)

            for categoria in categorias_dietas:
                # lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
                #     medicao, categoria
                # )

                lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas_por_faixa(
                    medicao, categoria
                )
                dietas_alimentacoes = _update_dietas_alimentacoes(
                    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
                )

    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = _generate_columns(dict_periodos_dietas)

    return columns


def _get_nome_periodo(medicao):
    # TODO: se a mediçao tiver o grupo dá erro no merge
    return (
        medicao.periodo_escolar.nome
        if not medicao.grupo
        else (
            f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
            if medicao.periodo_escolar
            else medicao.grupo.nome
        )
    )


def _get_lista_alimentacoes(medicao, nome_periodo):
    lista_alimentacoes = list(
        medicao.valores_medicao.exclude(
            Q(
                nome_campo__in=[
                    "observacoes",
                    "dietas_autorizadas",
                    "matriculados",
                    "frequencia",
                    "numero_de_alunos",
                ]
            )
            | Q(categoria_medicao__nome__icontains="DIETA ESPECIAL")
        )
        .values_list("nome_campo", flat=True)
        .distinct()
    )

    return lista_alimentacoes


def _get_faixas_etarias(medicao, nome_periodo):
    lista_faixas = list(
        faixa.__str__()
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


def _get_lista_alimentacoes_dietas(medicao, categoria):
    return list(
        medicao.valores_medicao.filter(categoria_medicao__nome=categoria)
        .exclude(
            nome_campo__in=[
                "dietas_autorizadas",
                "observacoes",
                "frequencia",
                "matriculados",
                "numero_de_alunos",
            ]
        )
        .values_list("nome_campo", flat=True)
        .distinct()
    )


def _get_lista_alimentacoes_dietas_por_faixa(medicao, categoria):
    dietas_por_faixa = list(
        faixa.__str__()
        for faixa in FaixaEtaria.objects.filter(
            id__in=medicao.valores_medicao.filter(
                categoria_medicao__nome=categoria, nome_campo="frequencia"
            ).values_list("faixa_etaria", flat=True)
        )
        .distinct()
        .order_by("inicio")
    )

    return dietas_por_faixa


def _update_dietas_alimentacoes(
    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
):
    if lista_alimentacoes_dietas:
        if categoria in dietas_alimentacoes:
            dietas_alimentacoes[categoria] += lista_alimentacoes_dietas
        else:
            dietas_alimentacoes[categoria] = lista_alimentacoes_dietas
    return dietas_alimentacoes


def _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes):
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


def _get_valores_tabela(solicitacoes, colunas, tipos_de_unidade):
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


def _define_filtro(periodo, dietas_especiais, periodos_escolares):
    filtros = {}
    if periodo in [
        "Programas e Projetos",
        "ETEC",
        "Solicitações de Alimentação",
    ]:
        filtros["grupo__nome"] = periodo
    elif periodo in dietas_especiais:
        filtros["periodo_escolar__nome__in"] = periodos_escolares
    else:
        filtros["periodo_escolar__nome"] = periodo
    return filtros


def _processa_periodo_campo(
    solicitacao, periodo, faixa_etaria, valores, dietas_especiais, periodos_escolares
):
    filtros = _define_filtro(periodo, dietas_especiais, periodos_escolares)

    try:
        if periodo in dietas_especiais:
            total = _processa_dieta_especial(
                solicitacao, filtros, faixa_etaria, periodo
            )
        else:
            total = _processa_periodo_regular(
                solicitacao, filtros, faixa_etaria, periodo
            )
        valores.append(total)
    except Exception as e:
        print(e)
        valores.append("-")
    return valores


def _processa_dieta_especial(solicitacao, filtros, faixa_etaria, periodo):
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
    medicao = solicitacao.medicoes.get(**filtros)
    categoria = "ALIMENTAÇÃO"
    if periodo == "Solicitações de Alimentação":
        categoria = periodo.upper()

    soma = _calcula_soma_medicao(medicao, faixa_etaria, categoria)
    return soma if soma is not None else "-"


def _calcula_soma_medicao(medicao, faixa_etaria, categoria):
    inicio, fim = string_to_faixa(faixa_etaria)
    return (
        medicao.valores_medicao.filter(
            nome_campo="frequencia",
            faixa_etaria__inicio=inicio,
            faixa_etaria__fim=fim,
            categoria_medicao__nome=categoria,
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))["total"]
    )


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


def _insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer):
    NOMES_CAMPOS = {
        "lanche": "Lanche",
        "lanche_4h": "Lanche 4h",
        "2_lanche_4h": "2º Lanche 4h",
        "2_lanche_5h": "2º Lanche 5h",
        "lanche_extra": "Lanche Extra",
        "refeicao": "Refeição",
        "repeticao_refeicao": "Repetição de Refeição",
        "2_refeicao_1_oferta": "2ª Refeição 1ª Oferta",
        "repeticao_2_refeicao": "Repetição 2ª Refeição",
        "kit_lanche": "Kit Lanche",
        "total_refeicoes_pagamento": "Refeições p/ Pagamento",
        "sobremesa": "Sobremesa",
        "repeticao_sobremesa": "Repetição de Sobremesa",
        "2_sobremesa_1_oferta": "2ª Sobremesa 1ª Oferta",
        "repeticao_2_sobremesa": "Repetição 2ª Sobremesa",
        "total_sobremesas_pagamento": "Sobremesas p/ Pagamento",
        "lanche_emergencial": "Lanche Emerg.",
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


def _ajusta_layout_tabela(workbook, worksheet, df):
    formatacao_base = {
        "align": "center",
        "valign": "vcenter",
        "font_color": "#FFFFFF",
        "bold": True,
        "border": 1,
        "border_color": "#999999",
    }
    formatacao_manha = workbook.add_format({**formatacao_base, "bg_color": "#198459"})
    formatacao_tarde = workbook.add_format({**formatacao_base, "bg_color": "#D06D12"})
    formatacao_integral = workbook.add_format(
        {**formatacao_base, "bg_color": "#2F80ED"}
    )
    formatacao_noite = workbook.add_format({**formatacao_base, "bg_color": "#B40C02"})
    formatacao_vespertino = workbook.add_format(
        {**formatacao_base, "bg_color": "#C13FD6"}
    )
    formatacao_intermediario = workbook.add_format(
        {**formatacao_base, "bg_color": "#2F80ED"}
    )
    formatacao_programas = workbook.add_format(
        {**formatacao_base, "bg_color": "#72BC17"}
    )
    formatacao_etec = workbook.add_format({**formatacao_base, "bg_color": "#DE9524"})
    formatacao_dieta_a = workbook.add_format({**formatacao_base, "bg_color": "#198459"})
    formatacao_dieta_b = workbook.add_format({**formatacao_base, "bg_color": "#20AA73"})

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
        "MANHA": formatacao_manha,
        "TARDE": formatacao_tarde,
        "INTEGRAL": formatacao_integral,
        "NOITE": formatacao_noite,
        "VESPERTINO": formatacao_vespertino,
        "INTERMEDIARIO": formatacao_intermediario,
        "PROGRAMAS E PROJETOS": formatacao_programas,
        "ETEC": formatacao_etec,
        "DIETA ESPECIAL - TIPO A": formatacao_dieta_a,
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS": formatacao_dieta_a,
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
