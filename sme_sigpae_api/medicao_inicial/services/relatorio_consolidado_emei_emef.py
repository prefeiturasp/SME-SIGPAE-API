import calendar

import pandas as pd
from django.db.models import FloatField, Q, Sum
from django.db.models.functions import Cast

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_CAMPOS,
    ORDEM_HEADERS_EMEI_EMEF,
    ORDEM_UNIDADES_GRUPO_EMEF,
    ORDEM_UNIDADES_GRUPO_EMEI,
)
from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.services.utils import get_nome_periodo

from ..models import CategoriaMedicao


def get_alimentacoes_por_periodo(solicitacoes):
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = get_nome_periodo(medicao)
            lista_alimentacoes = _get_lista_alimentacoes(medicao, nome_periodo)
            periodos_alimentacoes = _update_periodos_alimentacoes(
                periodos_alimentacoes, nome_periodo, lista_alimentacoes
            )

            categorias_dietas = _get_categorias_dietas(medicao)

            for categoria in categorias_dietas:
                lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
                    medicao, categoria
                )
                dietas_alimentacoes = _update_dietas_alimentacoes(
                    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
                )

    dietas_alimentacoes = _unificar_dietas_tipo_a(dietas_alimentacoes)
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = _generate_columns(dict_periodos_dietas)

    return columns


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

    if nome_periodo != "Solicitações de Alimentação":
        lista_alimentacoes += [
            "total_refeicoes_pagamento",
            "total_sobremesas_pagamento",
        ]

    return lista_alimentacoes


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


def _update_dietas_alimentacoes(
    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
):
    if lista_alimentacoes_dietas:
        if categoria in dietas_alimentacoes:
            dietas_alimentacoes[categoria] += lista_alimentacoes_dietas
        else:
            dietas_alimentacoes[categoria] = lista_alimentacoes_dietas
    return dietas_alimentacoes


def _unificar_dietas_tipo_a(dietas_alimentacoes):
    dieta_principal = "DIETA ESPECIAL - TIPO A"
    dieta_alternativa = "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    valor_principal = dietas_alimentacoes.get(dieta_principal, [])
    valor_alternativo = dietas_alimentacoes.get(dieta_alternativa, [])
    if valor_alternativo:
        dietas_alimentacoes[dieta_principal] = valor_principal + valor_alternativo
        dietas_alimentacoes.pop(dieta_alternativa, None)
    return dietas_alimentacoes


def _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes):
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
            dict_periodos_dietas.items(),
            key=lambda item: ORDEM_HEADERS_EMEI_EMEF[item[0]],
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
        for periodo, campo in colunas:
            valores_solicitacao_atual = _processa_periodo_campo(
                solicitacao,
                periodo,
                campo,
                valores_solicitacao_atual,
                dietas_especiais,
                periodos_escolares,
            )
        valores.append(valores_solicitacao_atual)
    return valores


def get_solicitacoes_ordenadas(solicitacoes, tipos_de_unidade):
    if set(tipos_de_unidade).issubset(ORDEM_UNIDADES_GRUPO_EMEF):
        ordem_unidades = ORDEM_UNIDADES_GRUPO_EMEF
    else:
        ordem_unidades = ORDEM_UNIDADES_GRUPO_EMEI

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
    solicitacao, periodo, campo, valores, dietas_especiais, periodos_escolares
):
    filtros = _define_filtro(periodo, dietas_especiais, periodos_escolares)

    try:
        if periodo in dietas_especiais:
            total = processa_dieta_especial(solicitacao, filtros, campo, periodo)
        else:
            total = processa_periodo_regular(solicitacao, filtros, campo, periodo)
        valores.append(total)
    except Exception:
        valores.append("-")
    return valores


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
        filtros["grupo__nome__in"] = ["Programas e Projetos", "ETEC"]
    else:
        filtros["periodo_escolar__nome"] = periodo
    return filtros


def processa_dieta_especial(solicitacao, filtros, campo, periodo):
    condicoes = Q()
    for filtro, valor in filtros.items():
        condicoes = condicoes | Q(**{filtro: valor})

    medicoes = solicitacao.medicoes.filter(condicoes)
    if not medicoes.exists():
        return "-"

    categorias = (
        [
            "DIETA ESPECIAL - TIPO A",
            "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
        ]
        if periodo == "DIETA ESPECIAL - TIPO A"
        else [periodo]
    )
    total = 0.0
    for medicao in medicoes:
        soma = _calcula_soma_medicao(medicao, campo, categorias)
        if soma is not None:
            total += soma

    return "-" if total == 0.0 else total


def processa_periodo_regular(solicitacao, filtros, campo, periodo, tipo_unidade=None):
    medicao = solicitacao.medicoes.get(**filtros)

    iniciais = (
        solicitacao.escola.tipo_unidade.iniciais
        if tipo_unidade is None
        else tipo_unidade
    )
    if campo in ["total_refeicoes_pagamento", "total_sobremesas_pagamento"]:
        return _get_total_pagamento(medicao, campo, iniciais)

    categorias = (
        [periodo.upper()]
        if periodo == "Solicitações de Alimentação"
        else ["ALIMENTAÇÃO"]
    )
    soma = _calcula_soma_medicao(medicao, campo, categorias)
    return soma if soma is not None else "-"


def _calcula_soma_medicao(medicao, campo, categorias):
    return (
        medicao.valores_medicao.filter(
            nome_campo=campo, categoria_medicao__nome__in=categorias
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))["total"]
    )


def _get_total_pagamento(medicao, nome_campo, tipo_unidade):
    if tipo_unidade in ORDEM_UNIDADES_GRUPO_EMEF.keys():
        return _total_pagamento_emef(medicao, nome_campo)
    elif tipo_unidade in ORDEM_UNIDADES_GRUPO_EMEI.keys():
        return _total_pagamento_emei(medicao, nome_campo)


def _total_pagamento_emef(medicao, nome_campo):
    """
    Para EMEF: O total é sempre menor valor entre os matriculados e o que foi servido.
    """
    campos_refeicoes = [
        "refeicao",
        "repeticao_refeicao",
        "2_refeicao_1_oferta",
        "repeticao_2_refeicao",
    ]
    campos_sobremesas = [
        "sobremesa",
        "repeticao_sobremesa",
        "2_sobremesa_1_oferta",
        "repeticao_2_sobremesa",
    ]
    lista_campos = (
        campos_refeicoes
        if nome_campo == "total_refeicoes_pagamento"
        else campos_sobremesas
    )
    mes = medicao.solicitacao_medicao_inicial.mes
    ano = medicao.solicitacao_medicao_inicial.ano
    total_dias_no_mes = calendar.monthrange(int(ano), int(mes))[1]
    total_pagamento = 0

    for dia in range(1, total_dias_no_mes + 1):
        matriculados = medicao.valores_medicao.filter(
            nome_campo="matriculados", dia=f"{dia:02d}"
        ).first()
        numero_de_alunos = medicao.valores_medicao.filter(
            nome_campo="numero_de_alunos", dia=f"{dia:02d}"
        ).first()

        totais = []
        for campo in lista_campos:
            valor_campo_obj = medicao.valores_medicao.filter(
                nome_campo=campo, dia=f"{dia:02d}"
            ).first()
            if valor_campo_obj:
                valor_campo = valor_campo_obj.valor
                totais.append(int(valor_campo))

        total_dia = sum(totais)
        valor_comparativo = (
            matriculados.valor
            if matriculados
            else numero_de_alunos.valor
            if numero_de_alunos
            else 0
        )
        total_pagamento += min(int(total_dia), int(valor_comparativo))

    return total_pagamento


def _total_pagamento_emei(medicao, nome_campo):
    """
    Para EMEI: o que vai pagamento é só o que foi servido em "refeicao" e "2_refeicao_1_oferta"
    """
    campos_refeicoes = [
        "refeicao",
        "2_refeicao_1_oferta",
    ]
    campos_sobremesas = [
        "sobremesa",
        "2_sobremesa_1_oferta",
    ]
    lista_campos = (
        campos_refeicoes
        if nome_campo == "total_refeicoes_pagamento"
        else campos_sobremesas
    )

    total_pagamento = (
        medicao.valores_medicao.filter(
            nome_campo__in=lista_campos, categoria_medicao__nome="ALIMENTAÇÃO"
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))
    )

    return total_pagamento["total"]


def insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer):
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


def ajusta_layout_tabela(workbook, worksheet, df):
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
