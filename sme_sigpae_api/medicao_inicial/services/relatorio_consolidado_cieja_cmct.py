from django.db.models import Q

from sme_sigpae_api.dados_comuns.constants import ORDEM_CAMPOS, ORDEM_HEADERS_CIEJA_CMCT
from sme_sigpae_api.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial
from sme_sigpae_api.medicao_inicial.services.utils import (
    generate_columns,
    get_categorias_dietas,
    get_nome_periodo,
    update_dietas_alimentacoes,
    update_periodos_alimentacoes,
)


def get_alimentacoes_por_periodo(solicitacoes: list[SolicitacaoMedicaoInicial]) -> list:
    """
    Agrupa e organiza alimentações por período e dieta a partir de solicitações

    Processa uma lista de solicitações de medição inicial para extrair, consolidar
    e organizar todas as alimentações por período escolar e categorias de dieta.

    O fluxo de processamento inclui:
    1. Extrair períodos e alimentações regulares de cada medição
    2. Extrair categorias de dieta e suas alimentações específicas
    3. Unificar variações da dieta Tipo A
    4. Ordenar e mesclar períodos e dietas em uma estrutura única
    5. Gerar lista final de colunas para relatórios

    Args:
        solicitacoes (list[SolicitacaoMedicaoInicial]): Lista de solicitações de medição inicial contendo as medições a serem processadas

    Returns:
        list: Lista de tuplas no formato [(categoria, alimentação), ...] representando todas as colunas organizadas para geração de relatórios ou exibição.

    Examples:
        >>> colunas = get_alimentacoes_por_periodo(solicitacoes)
        [
            ('MANHA', 'lanche'),
            ('Solicitações de Alimentação', 'kit_lanche'),
            ('DIETA ESPECIAL - TIPO A', 'lanche_4h'),
        ]
    """
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

    dietas_alimentacoes = _unificar_dietas_tipo_a(dietas_alimentacoes)
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = generate_columns(dict_periodos_dietas)

    return columns


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


def _unificar_dietas_tipo_a(dietas_alimentacoes: dict) -> dict:
    """
    Unifica dietas do Tipo A com  as dietas Tipo A enteral/restrição de aminoácidos

    Args:
        dietas_alimentacoes (dict): Dicionário contendo categorias de dietas como chaves e listas de alimentações como valores.

    Returns:
        dict: Dicionário com as dietas do Tipo A unificadas. Se existir a dieta alternativa, suas alimentações são mescladas na dieta principal e a alternativa é removida.
    """
    dieta_principal = "DIETA ESPECIAL - TIPO A"
    dieta_alternativa = "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    valor_principal = dietas_alimentacoes.get(dieta_principal, [])
    valor_alternativo = dietas_alimentacoes.get(dieta_alternativa, [])
    if valor_alternativo:
        dietas_alimentacoes[dieta_principal] = valor_principal + valor_alternativo
        dietas_alimentacoes.pop(dieta_alternativa, None)
    return dietas_alimentacoes


def _sort_and_merge(periodos_alimentacoes: dict, dietas_alimentacoes: dict) -> dict:
    """
    Ordena e mescla dicionários de períodos e dietas em um único dicionário ordenado.

    Processa dois dicionários independentes (períodos e dietas) realizando as seguintes operações:
    1. Remove duplicatas e ordena os valores de cada chave com base em ORDEM_CAMPOS
    2. Mescla os dois dicionários em um único
    3. Ordena as chaves do dicionário resultante com base em ORDEM_HEADERS_CIEJA_CMCT

    Args:
        periodos_alimentacoes (dict): Dicionário com períodos como chaves e listas de alimentações como valores.
        dietas_alimentacoes (dict): Dicionário com categorias de dieta como chaves e listas de alimentações como valores.

    Returns:
        dict: Dicionário com os períodos e dietas

    Example:
    >>> _sort_and_merge({'MANHA': ['lanche_4h', 'total_refeicoes_pagamento']}, {'DIETA ESPECIAL - TIPO B': ['lanche', 'lanche_4h', 'lanche', 'lanche_4h']})
    {
        'MANHA': ['lanche_4h', 'total_refeicoes_pagamento'],
        'DIETA ESPECIAL - TIPO B': ['lanche', 'lanche_4h']
    }
    """
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
            key=lambda item: ORDEM_HEADERS_CIEJA_CMCT[item[0]],
        )
    )

    return dict_periodos_dietas
