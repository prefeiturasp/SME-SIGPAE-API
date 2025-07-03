from django.db.models import Q

from sme_sigpae_api.dados_comuns.constants import (
    NOMES_CAMPOS,
    ORDEM_CAMPOS,
    ORDEM_HEADERS_CEMEI,
    ORDEM_UNIDADES_GRUPO_CEMEI,
)
from sme_sigpae_api.escola.models import FaixaEtaria
from sme_sigpae_api.medicao_inicial.models import GrupoMedicao
from sme_sigpae_api.medicao_inicial.services import (
    relatorio_consolidado_cei,
    relatorio_consolidado_emei_emef,
)
from sme_sigpae_api.medicao_inicial.services.utils import (
    generate_columns,
    gera_colunas_alimentacao,
    get_categorias_dietas,
    get_nome_periodo,
    get_valores_iniciais,
    update_dietas_alimentacoes,
    update_periodos_alimentacoes,
)


def get_alimentacoes_por_periodo(solicitacoes):
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = get_nome_periodo(medicao)
            lista_alimentacoes = _get_lista_alimentacoes(medicao, nome_periodo)
            periodos_alimentacoes = update_periodos_alimentacoes(
                periodos_alimentacoes, nome_periodo, lista_alimentacoes
            )
            categorias_dietas = get_categorias_dietas(medicao)
            for categoria in categorias_dietas:
                lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
                    medicao, categoria
                )
                if "infantil" in nome_periodo.lower():
                    nome_categoria = categoria + " - INFANTIL"
                else:
                    nome_categoria = f"{categoria} - {nome_periodo.upper()}"
                dietas_alimentacoes = update_dietas_alimentacoes(
                    dietas_alimentacoes, nome_categoria, lista_alimentacoes_dietas
                )

    dietas_alimentacoes = _unificar_dietas(dietas_alimentacoes)
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = generate_columns(dict_periodos_dietas)
    return columns


def _get_lista_alimentacoes(medicao, nome_periodo):
    if medicao.periodo_escolar and nome_periodo in ["INTEGRAL", "PARCIAL"]:
        return list(
            faixa.id
            for faixa in FaixaEtaria.objects.filter(
                id__in=medicao.valores_medicao.filter(
                    nome_campo="frequencia"
                ).values_list("faixa_etaria", flat=True)
            )
            .distinct()
            .order_by("inicio")
        )
    else:
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

        if nome_periodo != "Solicitações de Alimentação":
            lista_alimentacoes += [
                "total_refeicoes_pagamento",
                "total_sobremesas_pagamento",
            ]

        return lista_alimentacoes


def _get_lista_alimentacoes_dietas(medicao, categoria):
    if medicao.periodo_escolar:
        return list(
            faixa.id
            for faixa in FaixaEtaria.objects.filter(
                id__in=medicao.valores_medicao.filter(
                    categoria_medicao__nome=categoria, nome_campo="frequencia"
                ).values_list("faixa_etaria", flat=True)
            )
            .distinct()
            .order_by("inicio")
        )
    else:
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


def _unificar_dietas(dietas_alimentacoes):
    dieta_principal = "DIETA ESPECIAL - TIPO A - INFANTIL"
    dieta_alternativa = (
        "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS - INFANTIL"
    )

    valor_principal = dietas_alimentacoes.get(dieta_principal, [])
    valor_alternativo = dietas_alimentacoes.get(dieta_alternativa, [])
    if valor_alternativo:
        dietas_alimentacoes[dieta_principal] = valor_principal + valor_alternativo
        dietas_alimentacoes.pop(dieta_alternativa, None)
    return dietas_alimentacoes


def _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes):
    ORDEM_CAMPOS_CEMEI = [
        faixa.id for faixa in FaixaEtaria.objects.filter(ativo=True).order_by("inicio")
    ] + ORDEM_CAMPOS

    periodos_alimentacoes = {
        chave: sorted(
            list(set(valores)), key=lambda valor: ORDEM_CAMPOS_CEMEI.index(valor)
        )
        for chave, valores in periodos_alimentacoes.items()
    }

    dietas_alimentacoes = {
        chave: sorted(
            list(set(valores)), key=lambda valor: ORDEM_CAMPOS_CEMEI.index(valor)
        )
        for chave, valores in dietas_alimentacoes.items()
    }
    dict_periodos_dietas = {**periodos_alimentacoes, **dietas_alimentacoes}

    dict_periodos_dietas = dict(
        sorted(
            dict_periodos_dietas.items(), key=lambda item: ORDEM_HEADERS_CEMEI[item[0]]
        )
    )

    return dict_periodos_dietas


def get_valores_tabela(solicitacoes, colunas):
    grupos_medicao = GrupoMedicao.objects.filter(
        nome__icontains="Infantil"
    ).values_list("nome", flat=True)
    valores = []
    for solicitacao in get_solicitacoes_ordenadas(solicitacoes):
        valores_solicitacao_atual = []
        valores_solicitacao_atual += get_valores_iniciais(solicitacao)
        for periodo, campo in colunas:
            valores_solicitacao_atual = _processa_periodo_campo(
                solicitacao,
                periodo,
                campo,
                valores_solicitacao_atual,
                grupos_medicao,
            )
        valores.append(valores_solicitacao_atual)
    return valores


def get_solicitacoes_ordenadas(solicitacoes):
    return sorted(
        solicitacoes,
        key=lambda k: ORDEM_UNIDADES_GRUPO_CEMEI[k.escola.tipo_unidade.iniciais],
    )


def _processa_periodo_campo(solicitacao, periodo, campo, valores, grupos_medicao):
    filtros = _define_filtro(periodo, grupos_medicao)
    try:
        if "DIETA ESPECIAL" in periodo:
            total = _processa_dieta_especial(solicitacao, filtros, campo, periodo)
        else:
            total = _processa_periodo_regular(solicitacao, filtros, campo, periodo)
        valores.append(total)
    except Exception:
        valores.append("-")
    return valores


def _define_filtro(periodo, grupos_medicao):
    filtros = {}
    if periodo in ["Solicitações de Alimentação"] + list(grupos_medicao):
        filtros["grupo__nome"] = periodo
    elif "DIETA ESPECIAL" in periodo:
        if "INFANTIL" in periodo:
            filtros["grupo__nome__in"] = grupos_medicao
        else:
            filtros["periodo_escolar__nome"] = periodo.split(" - ")[-1]
    else:
        filtros["periodo_escolar__nome"] = periodo
    return filtros


def _processa_dieta_especial(solicitacao, filtros, campo, periodo):
    periodo = (
        periodo.replace(" - INFANTIL", "")
        .replace(" - INTEGRAL", "")
        .replace(" - PARCIAL", "")
    )
    soma = "-"
    if any("periodo_escolar" in chave for chave in filtros.keys()):
        soma = relatorio_consolidado_cei.processa_dieta_especial(
            solicitacao, filtros, campo, periodo
        )
    elif any("grupo" in chave for chave in filtros.keys()):
        soma = relatorio_consolidado_emei_emef.processa_dieta_especial(
            solicitacao, filtros, campo, periodo
        )
    return soma


def _processa_periodo_regular(solicitacao, filtros, campo, periodo):
    soma = "-"
    if any("periodo_escolar" in chave for chave in filtros.keys()):
        soma = relatorio_consolidado_cei.processa_periodo_regular(
            solicitacao, filtros, campo, periodo
        )
    elif any("grupo" in chave for chave in filtros.keys()):
        soma = relatorio_consolidado_emei_emef.processa_periodo_regular(
            solicitacao, filtros, campo, periodo, tipo_unidade="EMEI"
        )
    return soma


def insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer):
    NOMES_CAMPOS.update(
        {faixa.id: faixa.__str__() for faixa in FaixaEtaria.objects.filter(ativo=True)}
    )
    df = gera_colunas_alimentacao(aba, colunas, linhas, writer, NOMES_CAMPOS)
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
    formatacao_integral_cei = workbook.add_format(
        {**formatacao_base, "bg_color": "#198459"}
    )
    formatacao_parcial = workbook.add_format({**formatacao_base, "bg_color": "#D06D12"})
    formatacao_manha = workbook.add_format({**formatacao_base, "bg_color": "#C13FD6"})
    formatacao_integral = workbook.add_format(
        {**formatacao_base, "bg_color": "#B40C02"}
    )
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
            "formatacao": formatacao_integral_cei,
            "nome": "INTEGRAL",
        },
        "DIETA ESPECIAL - TIPO A - INTEGRAL": {
            "formatacao": formatacao_integral_cei,
            "nome": "DIETA ESPECIAL - TIPO A",
        },
        "DIETA ESPECIAL - TIPO B - INTEGRAL": {
            "formatacao": formatacao_integral_cei,
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
        "INFANTIL INTEGRAL": {
            "formatacao": formatacao_integral,
            "nome": "INFANTIL INTEGRAL",
        },
        "INFANTIL MANHA": {
            "formatacao": formatacao_manha,
            "nome": "INFANTIL MANHA",
        },
        "INFANTIL TARDE": {
            "formatacao": formatacao_tarde,
            "nome": "INFANTIL TARDE",
        },
        "DIETA ESPECIAL - TIPO A - INFANTIL": {
            "formatacao": formatacao_dieta_a,
            "nome": "DIETA ESPECIAL - TIPO A",
        },
        "DIETA ESPECIAL - TIPO B - INFANTIL": {
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
