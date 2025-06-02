import calendar

import pandas as pd
from django.db.models import FloatField, Q, Sum
from django.db.models.functions import Cast

from sme_sigpae_api.dados_comuns.constants import (
    ORDEM_CAMPOS,
    ORDEM_HEADERS_EMEBS,
    ORDEM_UNIDADES_GRUPO_EMEBS,
)
from sme_sigpae_api.escola.constants import INFANTIL_OU_FUNDAMENTAL
from sme_sigpae_api.escola.models import PeriodoEscolar

from ..models import CategoriaMedicao


def get_alimentacoes_por_periodo(solicitacoes):
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            for turma in ["INFANTIL", "FUNDAMENTAL"]:
                nome_periodo = _get_nome_periodo(medicao)
                if nome_periodo == "NOITE" and turma == "INFANTIL":
                    continue
                lista_alimentacoes = _get_lista_alimentacoes(
                    medicao, nome_periodo, turma
                )
                if nome_periodo not in [
                    "Programas e Projetos",
                    "Solicitações de Alimentação",
                ]:
                    nome_periodo = nome_periodo + " - " + turma
                periodos_alimentacoes = _update_periodos_alimentacoes(
                    periodos_alimentacoes, nome_periodo, lista_alimentacoes
                )

                categorias_dietas = _get_categorias_dietas(medicao, turma)

                for categoria in categorias_dietas:
                    lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
                        medicao, categoria
                    )
                    categoria = categoria + " - " + turma
                    dietas_alimentacoes = _update_dietas_alimentacoes(
                        dietas_alimentacoes, categoria, lista_alimentacoes_dietas
                    )

    dietas_alimentacoes = _unificar_dietas_tipo_a(dietas_alimentacoes)
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


def _get_lista_alimentacoes(medicao, nome_periodo, turma):
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
        .filter(infantil_ou_fundamental=turma)
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


def _get_categorias_dietas(medicao, turma):
    return list(
        medicao.valores_medicao.exclude(
            categoria_medicao__nome__icontains="ALIMENTAÇÃO"
        )
        .filter(infantil_ou_fundamental=turma)
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
    for turma in ["INFANTIL", "FUNDAMENTAL"]:
        dieta_principal = f"DIETA ESPECIAL - TIPO A - {turma}"
        dieta_alternativa = (
            f"DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS - {turma}"
        )
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
            key=lambda item: ORDEM_HEADERS_EMEBS[item[0]],
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


def get_valores_tabela(solicitacoes, colunas):
    return []
