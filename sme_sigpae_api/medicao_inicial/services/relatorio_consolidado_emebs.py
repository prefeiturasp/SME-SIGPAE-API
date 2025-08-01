import calendar
import logging

from django.db.models import FloatField, Q, Sum
from django.db.models.functions import Cast

from sme_sigpae_api.dados_comuns.constants import (
    NOMES_CAMPOS,
    ORDEM_CAMPOS,
    ORDEM_HEADERS_EMEBS,
)
from sme_sigpae_api.escola.models import PeriodoEscolar
from sme_sigpae_api.medicao_inicial.models import CategoriaMedicao
from sme_sigpae_api.medicao_inicial.services.utils import (
    gera_colunas_alimentacao,
    get_nome_periodo,
    get_valores_iniciais,
)

logger = logging.getLogger(__name__)


def get_alimentacoes_por_periodo(solicitacoes):
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = get_nome_periodo(medicao)
            alimentacoes_infantil, alimentacoes_fundamental = _get_lista_alimentacoes(
                medicao, nome_periodo
            )
            periodos_alimentacoes = _update_periodos_alimentacoes(
                periodos_alimentacoes,
                nome_periodo,
                lista_alimentacoes=alimentacoes_infantil,
                turma="INFANTIL",
            )
            periodos_alimentacoes = _update_periodos_alimentacoes(
                periodos_alimentacoes,
                nome_periodo,
                lista_alimentacoes=alimentacoes_fundamental,
                turma="FUNDAMENTAL",
            )
            dietas_infantil, dietas_fundamental = _get_categorias_dietas(medicao)
            dietas_alimentacoes = _obter_dietas_especiais(
                dietas_alimentacoes,
                medicao,
                dietas_turma=dietas_infantil,
                turma="INFANTIL",
            )
            dietas_alimentacoes = _obter_dietas_especiais(
                dietas_alimentacoes,
                medicao,
                dietas_turma=dietas_fundamental,
                turma="FUNDAMENTAL",
            )

    dietas_alimentacoes = _unificar_dietas_tipo_a(dietas_alimentacoes, turma="INFANTIL")
    dietas_alimentacoes = _unificar_dietas_tipo_a(
        dietas_alimentacoes, turma="FUNDAMENTAL"
    )
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = _generate_columns(dict_periodos_dietas)

    return columns


def _get_lista_alimentacoes(medicao, nome_periodo):
    lista_alimentacoes = medicao.valores_medicao.exclude(
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

    infantil = list(
        lista_alimentacoes.filter(infantil_ou_fundamental="INFANTIL")
        .values_list("nome_campo", flat=True)
        .distinct()
    )
    fundamental = list(
        lista_alimentacoes.filter(infantil_ou_fundamental="FUNDAMENTAL")
        .values_list("nome_campo", flat=True)
        .distinct()
    )

    if nome_periodo != "Solicitações de Alimentação":
        if nome_periodo.upper() != "NOITE" and len(infantil) > 0:
            infantil += [
                "total_refeicoes_pagamento",
                "total_sobremesas_pagamento",
            ]
        if len(fundamental) > 0:
            fundamental += [
                "total_refeicoes_pagamento",
                "total_sobremesas_pagamento",
            ]

    return infantil, fundamental


def _update_periodos_alimentacoes(
    periodos_alimentacoes, nome_periodo, lista_alimentacoes, turma
):
    if turma not in periodos_alimentacoes:
        periodos_alimentacoes[turma] = dict()

    if nome_periodo in periodos_alimentacoes[turma]:
        periodos_alimentacoes[turma][nome_periodo] += lista_alimentacoes
    else:
        periodos_alimentacoes[turma][nome_periodo] = lista_alimentacoes

    return periodos_alimentacoes


def _get_categorias_dietas(medicao):
    lista_dietas = medicao.valores_medicao.exclude(
        categoria_medicao__nome__icontains="ALIMENTAÇÃO"
    )
    infantil = list(
        lista_dietas.filter(infantil_ou_fundamental="INFANTIL")
        .values_list("categoria_medicao__nome", flat=True)
        .distinct()
    )
    fundamental = list(
        lista_dietas.filter(infantil_ou_fundamental="FUNDAMENTAL")
        .values_list("categoria_medicao__nome", flat=True)
        .distinct()
    )

    return infantil, fundamental


def _obter_dietas_especiais(dietas_alimentacoes, medicao, dietas_turma, turma):
    for categoria in dietas_turma:
        lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
            medicao, categoria, turma
        )
        dietas_alimentacoes = _update_dietas_alimentacoes(
            dietas_alimentacoes,
            categoria,
            lista_alimentacoes_dietas,
            turma,
        )
    return dietas_alimentacoes


def _get_lista_alimentacoes_dietas(medicao, categoria, turma):
    return list(
        medicao.valores_medicao.filter(
            categoria_medicao__nome=categoria, infantil_ou_fundamental=turma
        )
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
    dietas_alimentacoes, categoria, lista_alimentacoes_dietas, turma
):
    if lista_alimentacoes_dietas:
        if turma not in dietas_alimentacoes:
            dietas_alimentacoes[turma] = dict()

        if categoria in dietas_alimentacoes[turma]:
            dietas_alimentacoes[turma][categoria] += lista_alimentacoes_dietas
        else:
            dietas_alimentacoes[turma][categoria] = lista_alimentacoes_dietas
    return dietas_alimentacoes


def _unificar_dietas_tipo_a(dietas_alimentacoes, turma):
    dieta_principal = "DIETA ESPECIAL - TIPO A"
    dieta_alternativa = "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    valor_principal = dietas_alimentacoes.get(turma, {}).get(dieta_principal, [])
    valor_alternativo = dietas_alimentacoes.get(turma, {}).get(dieta_alternativa, [])
    if valor_alternativo:
        if turma not in dietas_alimentacoes:
            dietas_alimentacoes[turma] = dict()
        dietas_alimentacoes[turma][dieta_principal] = (
            valor_principal + valor_alternativo
        )
        dietas_alimentacoes[turma].pop(dieta_alternativa, None)
    return dietas_alimentacoes


def _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes):
    periodos_alimentacoes = {
        nivel: {
            chave: sorted(
                list(set(valores)), key=lambda valor: ORDEM_CAMPOS.index(valor)
            )
            for chave, valores in periodos.items()
        }
        for nivel, periodos in periodos_alimentacoes.items()
    }

    dietas_alimentacoes = {
        nivel: {
            chave: sorted(
                list(set(valores)), key=lambda valor: ORDEM_CAMPOS.index(valor)
            )
            for chave, valores in dietas.items()
        }
        for nivel, dietas in dietas_alimentacoes.items()
    }

    dict_periodos_dietas = {}
    for nivel in periodos_alimentacoes.keys():
        dict_periodos_dietas[nivel] = {
            **periodos_alimentacoes[nivel],
            **dietas_alimentacoes.get(nivel, {}),
        }

    dict_periodos_dietas = {
        nivel: dict(
            sorted(items.items(), key=lambda item: ORDEM_HEADERS_EMEBS[item[0]])
        )
        for nivel, items in dict_periodos_dietas.items()
    }

    return dict_periodos_dietas


def _generate_columns(dict_periodos_dietas):
    solicitacoes = []
    if "INFANTIL" in dict_periodos_dietas:
        solicitacoes += dict_periodos_dietas["INFANTIL"].pop(
            "Solicitações de Alimentação", []
        )
    if "FUNDAMENTAL" in dict_periodos_dietas:
        solicitacoes += dict_periodos_dietas["FUNDAMENTAL"].pop(
            "Solicitações de Alimentação", []
        )
    ordem_solicitacoes = ["lanche_emergencial", "kit_lanche"]
    solicitacoes = sorted(solicitacoes, key=lambda x: ordem_solicitacoes.index(x))
    columns = [("", "Solicitações de Alimentação", valor) for valor in solicitacoes]
    for turma, categorias in dict_periodos_dietas.items():
        for categoria, valores in categorias.items():
            for valor in valores:
                columns.append((turma, categoria, valor))
    return columns


def get_valores_tabela(solicitacoes, colunas):
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)
    periodos_escolares = PeriodoEscolar.objects.all().values_list("nome", flat=True)
    valores = []
    for solicitacao in get_solicitacoes_ordenadas(solicitacoes):
        valores_solicitacao_atual = []
        valores_solicitacao_atual += get_valores_iniciais(solicitacao)
        for turma, periodo, campo in colunas:
            valores_solicitacao_atual = _processa_periodo_campo(
                solicitacao,
                turma,
                periodo,
                campo,
                valores_solicitacao_atual,
                dietas_especiais,
                periodos_escolares,
            )
        valores.append(valores_solicitacao_atual)
    return valores


def get_solicitacoes_ordenadas(solicitacoes):
    return sorted(
        solicitacoes,
        key=lambda k: k.escola.nome,
    )


def _processa_periodo_campo(
    solicitacao, turma, periodo, campo, valores, dietas_especiais, periodos_escolares
):
    filtros = _define_filtro(periodo, dietas_especiais, periodos_escolares)

    try:
        if periodo in dietas_especiais:
            total = processa_dieta_especial(solicitacao, filtros, campo, periodo, turma)
        else:
            total = processa_periodo_regular(
                solicitacao, filtros, campo, periodo, turma
            )
        valores.append(total)
    except (TypeError, AttributeError, ValueError) as exception:
        valores.append("-")
        logger.error(
            f"Erro ao atribuir valores para a solicitacao {solicitacao.uuid} para o campo {campo} no período {periodo} e turma {turma}:",
            exception,
        )
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


def processa_dieta_especial(solicitacao, filtros, campo, periodo, turma):
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
        soma = _calcula_soma_medicao(medicao, campo, categorias, [turma])
        if soma is not None:
            total += soma

    return "-" if total == 0.0 else total


def processa_periodo_regular(solicitacao, filtros, campo, periodo, turma):
    medicao = solicitacao.medicoes.get(**filtros)

    if campo in ["total_refeicoes_pagamento", "total_sobremesas_pagamento"]:
        return _get_total_pagamento(medicao, campo, turma)

    if periodo == "Solicitações de Alimentação":
        categorias = [periodo.upper()]
        turma = ["INFANTIL", "FUNDAMENTAL"]
    else:
        categorias = ["ALIMENTAÇÃO"]
        turma = [turma]

    soma = _calcula_soma_medicao(medicao, campo, categorias, turma)
    return soma if soma is not None else "-"


def _calcula_soma_medicao(medicao, campo, categorias, turma):
    return (
        medicao.valores_medicao.filter(
            nome_campo=campo,
            categoria_medicao__nome__in=categorias,
            infantil_ou_fundamental__in=turma,
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))["total"]
    )


def _get_total_pagamento(medicao, nome_campo, turma):
    if turma == "INFANTIL":
        total_valores = medicao.valores_medicao.filter(
            infantil_ou_fundamental=turma
        ).count()
        if (
            total_valores > 0
            and medicao.periodo_escolar
            in medicao.solicitacao_medicao_inicial.escola.periodos_escolares()
        ) or (medicao.grupo and medicao.grupo.nome == "Programas e Projetos"):
            valor_padrao = 0
        else:
            valor_padrao = "-"
        return _total_pagamento_infantil(medicao, nome_campo, valor_padrao)
    elif turma == "FUNDAMENTAL":
        return _total_pagamento_fundamental(medicao, nome_campo)


def _total_pagamento_infantil(medicao, nome_campo, valor_padrao):
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
            nome_campo__in=lista_campos,
            categoria_medicao__nome="ALIMENTAÇÃO",
            infantil_ou_fundamental="INFANTIL",
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))
    )
    total = total_pagamento["total"]
    return total if total is not None else valor_padrao


def _total_pagamento_fundamental(medicao, nome_campo):
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
            nome_campo="matriculados",
            dia=f"{dia:02d}",
            infantil_ou_fundamental="FUNDAMENTAL",
        ).first()
        numero_de_alunos = medicao.valores_medicao.filter(
            nome_campo="numero_de_alunos",
            dia=f"{dia:02d}",
            infantil_ou_fundamental="FUNDAMENTAL",
        ).first()

        totais = []
        for campo in lista_campos:
            valor_campo_obj = medicao.valores_medicao.filter(
                nome_campo=campo,
                dia=f"{dia:02d}",
                infantil_ou_fundamental="FUNDAMENTAL",
            ).first()
            if valor_campo_obj:
                valor_campo = valor_campo_obj.valor
                totais.append(int(valor_campo))

        total_dia = sum(totais)
        valor_comparativo = (
            matriculados.valor
            if matriculados
            else numero_de_alunos.valor if numero_de_alunos else 0
        )
        total_pagamento += min(int(total_dia), int(valor_comparativo))

    return total_pagamento


def insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer):
    colunas_fixas = [
        ("", "", "Tipo"),
        ("", "", "Cód. EOL"),
        ("", "", "Unidade Escolar"),
    ]

    headers = []
    for turma, chave, valor in colunas:
        if chave == "Solicitações de Alimentação":
            headers.append(("", "", NOMES_CAMPOS[valor]))
        else:
            headers.append((turma, chave.upper(), NOMES_CAMPOS[valor]))

    df = gera_colunas_alimentacao(
        aba,
        None,
        linhas,
        writer,
        None,
        colunas_fixas=colunas_fixas,
        headers=headers,
    )
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
    formatacao_programas = workbook.add_format(
        {**formatacao_base, "bg_color": "#72BC17"}
    )
    formatacao_dieta_a = workbook.add_format({**formatacao_base, "bg_color": "#198459"})
    formatacao_dieta_b = workbook.add_format({**formatacao_base, "bg_color": "#20AA73"})

    formatacao_infantil = workbook.add_format(
        {**formatacao_base, "bg_color": "#4a9a74"}
    )
    formatacao_fundamental = workbook.add_format(
        {**formatacao_base, "bg_color": "#2e7453"}
    )

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
        "PROGRAMAS E PROJETOS": formatacao_programas,
        "DIETA ESPECIAL - TIPO A": formatacao_dieta_a,
        "DIETA ESPECIAL - TIPO B": formatacao_dieta_b,
    }
    formatacao_turma = {
        "": {"formatacao": formatacao_level2, "nome": ""},
        "INFANTIL": {
            "formatacao": formatacao_infantil,
            "nome": "INFANTIL (4 a 6 anos)",
        },
        "FUNDAMENTAL": {
            "formatacao": formatacao_fundamental,
            "nome": "FUNDAMENTAL (acima de 6 anos)",
        },
    }

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(
            2,
            col_num,
            formatacao_turma[value[0]]["nome"],
            formatacao_turma[value[0]]["formatacao"],
        )
        worksheet.write(3, col_num, value[1], formatacao_level1[value[1]])
        worksheet.write(4, col_num, value[2], formatacao_level2)

    formatacao = workbook.add_format(
        {
            "align": "center",
            "valign": "vcenter",
        }
    )

    worksheet.set_column(0, len(df.columns) - 1, 15, formatacao)
    worksheet.set_column(2, 2, 30)

    worksheet.set_row(5, None, None, {"hidden": True})
    worksheet.set_row(2, 25)
    worksheet.set_row(3, 25)
    worksheet.set_row(4, 40)
