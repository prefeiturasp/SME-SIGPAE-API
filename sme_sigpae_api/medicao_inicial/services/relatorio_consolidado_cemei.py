from django.db.models import FloatField, Q, Sum

from sme_sigpae_api.dados_comuns.constants import ORDEM_CAMPOS, ORDEM_HEADERS_CEMEI
from sme_sigpae_api.escola.models import FaixaEtaria


def get_alimentacoes_por_periodo(solicitacoes):
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = _get_nome_periodo(medicao)
            lista_alimentacoes = _get_lista_alimentacoes(medicao, nome_periodo)
            periodos_alimentacoes = _update_periodos_alimentacoes(
                periodos_alimentacoes, nome_periodo, lista_alimentacoes
            )
            categorias_dietas = _get_categorias_dietas(medicao)
            for categoria in categorias_dietas:
                lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
                    medicao, categoria
                )
                if "infantil" in nome_periodo.lower():
                    nome_categoria = categoria + " - INFANTIL"
                else:
                    nome_categoria = categoria + " - CEI"
                dietas_alimentacoes = _update_dietas_alimentacoes(
                    dietas_alimentacoes, nome_categoria, lista_alimentacoes_dietas
                )
    # TODO: Ao cadastrar as dietas especiais para CEMEI, a parte de infantil(tipo EMEI) são dividas em lanche, lanche 4H e refeição.
    # Já a parte que é por faixa etaria(CEI) não tem essa divisão, é só um campo com frequencia.
    # Para somar as dietas EMEI+CEI, os dados da CEI eu somo com lanche, lanche 4h ou refeicao?
    dietas_alimentacoes = _unificar_dietas(dietas_alimentacoes)
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


def _update_dietas_alimentacoes(
    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
):
    if lista_alimentacoes_dietas:
        if categoria in dietas_alimentacoes:
            dietas_alimentacoes[categoria] += lista_alimentacoes_dietas
        else:
            dietas_alimentacoes[categoria] = lista_alimentacoes_dietas
    return dietas_alimentacoes


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


def _generate_columns(dict_periodos_dietas):
    columns = [
        (chave, valor)
        for chave, valores in dict_periodos_dietas.items()
        for valor in valores
    ]
    return columns


def get_valores_tabela(solicitacoes, colunas, tipos_de_unidade):
    pass


def insere_tabela_periodos_na_planilha(aba, colunas, linhas, writer):
    pass


def ajusta_layout_tabela(workbook, worksheet, df):
    pass
