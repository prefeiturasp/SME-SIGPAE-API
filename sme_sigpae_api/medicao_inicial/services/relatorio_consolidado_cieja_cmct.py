from django.db.models import Q

from sme_sigpae_api.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial
from sme_sigpae_api.medicao_inicial.services.utils import (
    get_categorias_dietas,
    get_nome_periodo,
    update_dietas_alimentacoes,
    update_periodos_alimentacoes,
)


def get_alimentacoes_por_periodo(solicitacoes: list[SolicitacaoMedicaoInicial]) -> list:
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
                dietas_alimentacoes = update_dietas_alimentacoes(
                    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
                )

    print(periodos_alimentacoes)
    print(dietas_alimentacoes)


def _get_lista_alimentacoes(medicao: Medicao, nome_periodo: str) -> list[str]:
    """ "
    Obtém a lista de alimentações baseada nos valores de medição.
    Filtra e retorna uma lista distinta de nomes de campos de alimentação excluindo campos específicos como observações, dietas autorizadas,
    informações de matrícula e categorias relacionadas a dieta especial.
    Adicionalmente, para períodos diferentes de "Solicitações de Alimentação", inclui campos específicos de pagamento.

    Args:
        medicao (Medicao): objeto de medição contendo os valores_medicao a serem filtrados
        nome_periodo (str): Nome do período para determinar se devem ser adicionados campos de pagamento.

    Returns:
        list: Lista de strings com os nomes dos campos de alimentação filtrados.

    Examples:
        >>>  _get_lista_alimentacoes(medicao, "MANHA")
        ['lanche', 'refeicao', 'repeticao_refeicao', 'repeticao_sobremesa', 'sobremesa', 'total_refeicoes_pagamento', 'total_sobremesas_pagamento']

    """
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


def _get_lista_alimentacoes_dietas(medicao: Medicao, categoria: str) -> list[str]:
    """
    Obtém lista de alimentações específicas de uma categoria de dieta.

    Filtra os valores de medição por categoria específica e retorna uma lista distinta de nomes de campos de alimentação,
    excluindo campos como dietas autorizadas, observações, frequência, etc.

    Args:
        medicao (Medicao):  Objeto de medição contendo os valores_medicao a serem filtrados.
        categoria (str):  Nome da categoria de dieta para filtrar os valores.

    Returns:
        list[str]:  Lista de strings com os nomes distintos dos campos de alimentação da categoria especificada.

    Examples:
        >>>  _get_lista_alimentacoes_dietas(medicao, "DIETA ESPECIAL - TIPO B")
        ['lanche', 'lanche_4h', 'refeicao']
    """
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
