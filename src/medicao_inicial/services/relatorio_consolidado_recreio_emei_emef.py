from django.db.models import Q

from src.dados_comuns.constants import ORDEM_CAMPOS, ORDEM_HEADERS_RECREIO_EMEI_EMEF
from src.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial
from src.medicao_inicial.services.utils import (
    filtra_queryset_pelo_intervalo_de_dias,
    generate_columns,
    get_categorias_dietas,
    get_nome_periodo,
    update_dietas_alimentacoes,
    update_periodos_alimentacoes,
)


def get_alimentacoes_por_periodo(
    solicitacoes: list[SolicitacaoMedicaoInicial], query_params: dict[str, str]
) -> list[tuple]:
    """Consolida as alimentações encontradas nas medições agrupando-as por período
    e por categoria de dieta especial.

    O processamento executa os seguintes passos:

    1. Percorre todas as solicitações de medição.
    2. Obtém os tipos de alimentação de cada período da medição.
    3. Obtém as categorias de dietas especiais existentes na medição.
    4. Agrupa os campos encontrados por período e por dieta.
    5. Unifica as dietas do tipo A.
    6. Ordena os campos e os grupos conforme as constantes de ordenação.
    7. Gera a estrutura final de colunas utilizada pelo relatório.

    Args:
        solicitacoes (list[SolicitacaoMedicaoInicial]): Lista de solicitações de medição que serão processadas.
        query_params (dict):  Filtros utilizados para restringir os dados considerados na geração do relatório.
            Exemplo:

                {
                    "dre": UUID da Diretoria Regional,
                    "status": "MEDICAO_APROVADA_PELA_CODAE",
                    "grupo_escolar":  UUID da Grupo escolar,
                    "mes": "12",
                    "ano": "2025",
                    "recreio_uuid": UUID do recreio nas férias
                }

    Returns:
        list[tuple]:  Lista de colunas formatadas para composição do relatório consolidado.

    Example:
        >>> columns = get_alimentacoes_por_periodo(
        ...     solicitacoes,
        ...     query_params
        ... )
        [('Recreio nas Férias', 'lanche'), ('Colaboradores', 'refeicao')]
    """
    periodos_alimentacoes = {}
    dietas_alimentacoes = {}

    for solicitacao in solicitacoes:
        for medicao in solicitacao.medicoes.all():
            nome_periodo = get_nome_periodo(medicao)
            lista_alimentacoes = _get_lista_alimentacoes(
                medicao, nome_periodo, query_params
            )
            periodos_alimentacoes = update_periodos_alimentacoes(
                periodos_alimentacoes, nome_periodo, lista_alimentacoes
            )
            categorias_dietas = get_categorias_dietas(
                filtra_queryset_pelo_intervalo_de_dias(
                    medicao.valores_medicao, query_params
                )
            )
            for categoria in categorias_dietas:
                lista_alimentacoes_dietas = _get_lista_alimentacoes_dietas(
                    medicao, categoria, query_params
                )
                dietas_alimentacoes = update_dietas_alimentacoes(
                    dietas_alimentacoes, categoria, lista_alimentacoes_dietas
                )
    dietas_alimentacoes = _unificar_dietas_tipo_a(dietas_alimentacoes)
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = generate_columns(dict_periodos_dietas)
    return columns


def _get_lista_alimentacoes(
    medicao: Medicao, nome_periodo: str, query_params: dict[str, str]
) -> list[str]:
    """Retorna os tipos de alimentação encontrados para um período específico
    da medição.

    São desconsiderados campos que não representam alimentações efetivas,
    como observações, frequência e participantes.

    Para todos os períodos, exceto "Solicitações de Alimentação", também são
    adicionados os campos calculados:

    - total_refeicoes_pagamento
    - total_sobremesas_pagamento

    Args:
        medicao (Medicao):  Instância da medição a ser processada.
        nome_periodo (str):  Nome do período identificado na medição.
        query_params (dict): Filtros utilizados para restringir os dias considerados.
            Exemplo:

                {
                    "dre": UUID da Diretoria Regional,
                    "status": "MEDICAO_APROVADA_PELA_CODAE",
                    "grupo_escolar":  UUID da Grupo escolar,
                    "mes": "12",
                    "ano": "2025",
                    "recreio_uuid": UUID do recreio nas férias
                }

    Returns:
        list[str]:  Lista única contendo os nomes dos campos de alimentação encontrados.

    Example:
        >>> _get_lista_alimentacoes(
        ...     medicao,
        ...     "Recreio nas Férias",
        ...     query_params
        ... )
        [
            "lanche",
            "refeicao",
            "total_refeicoes_pagamento",
            "total_sobremesas_pagamento"
        ]
    """
    lista_alimentacoes = list(
        filtra_queryset_pelo_intervalo_de_dias(medicao.valores_medicao, query_params)
        .exclude(
            Q(
                nome_campo__in=[
                    "observacoes",
                    "dietas_autorizadas",
                    "participantes",
                    "frequencia",
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


def _get_lista_alimentacoes_dietas(
    medicao: Medicao, categoria: str, query_params: dict[str, str]
) -> list[str]:
    """Retorna os tipos de alimentação associados a uma categoria específica
    de dieta especial.

    Campos administrativos ou informativos são removidos do resultado,
    mantendo apenas os campos relevantes para composição do relatório.

    Args:
        medicao (Medicao):  Instância da medição.
        categoria (str): Nome da categoria de dieta especial.
        query_params (dict):  Filtros utilizados para restringir os dias considerados.
            Exemplo:

                    {
                        "dre": UUID da Diretoria Regional,
                        "status": "MEDICAO_APROVADA_PELA_CODAE",
                        "grupo_escolar":  UUID da Grupo escolar,
                        "mes": "12",
                        "ano": "2025",
                        "recreio_uuid": UUID do recreio nas férias
                    }


    Returns:
        list[str]:  Lista dos nomes dos campos de alimentação encontrados para a dieta.

    Example:
        >>> _get_lista_alimentacoes_dietas(
        ...     medicao,
        ...     "DIETA ESPECIAL - TIPO A",
        ...     query_params
        ... )
        ["lanche", "refeicao"]
    """
    return list(
        filtra_queryset_pelo_intervalo_de_dias(medicao.valores_medicao, query_params)
        .filter(categoria_medicao__nome=categoria)
        .exclude(
            nome_campo__in=[
                "dietas_autorizadas",
                "observacoes",
                "frequencia",
                "participantes",
            ]
        )
        .values_list("nome_campo", flat=True)
        .distinct()
    )


def _unificar_dietas_tipo_a(
    dietas_alimentacoes: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Unifica as categorias de Dieta Especial Tipo A.

    Algumas medições podem possuir registros separados para:

    - DIETA ESPECIAL - TIPO A
    - DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS

    Neste cenário, os campos da categoria alternativa são incorporados à
    categoria principal e a chave alternativa é removida.

    Args:
        dietas_alimentacoes (dict):  Dicionário contendo as dietas e suas respectivas alimentações.

    Returns:
        dict[str, list[str]]:  Dicionário com as dietas do Tipo A consolidadas.

    Example:
        >>> _unificar_dietas_tipo_a(
        ...     {
        ...         "DIETA ESPECIAL - TIPO A": ["lanche"],
        ...         "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS": [
        ...             "refeicao"
        ...         ]
        ...     }
        ... )
        {
            "DIETA ESPECIAL - TIPO A": [
                "lanche",
                "refeicao"
            ]
        }
    """
    dieta_principal = "DIETA ESPECIAL - TIPO A"
    dieta_alternativa = "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
    valor_principal = dietas_alimentacoes.get(dieta_principal, [])
    valor_alternativo = dietas_alimentacoes.get(dieta_alternativa, [])
    if valor_alternativo:
        dietas_alimentacoes[dieta_principal] = valor_principal + valor_alternativo
        dietas_alimentacoes.pop(dieta_alternativa, None)
    return dietas_alimentacoes


def _sort_and_merge(
    periodos_alimentacoes: dict[str, list[str]],
    dietas_alimentacoes: dict[str, list[str]],
) -> dict[str, list[str]]:
    """
    Ordena e consolida os grupos de períodos e dietas.

    Regras aplicadas:

    - Remove valores duplicados.
    - Ordena os campos internos conforme ORDEM_CAMPOS.
    - Junta períodos e dietas em um único dicionário.
    - Ordena os grupos conforme ORDEM_HEADERS_RECREIO_EMEI_EMEF.

    Args:
        periodos_alimentacoes (dict): Alimentações agrupadas por período.
        dietas_alimentacoes (dict): Alimentações agrupadas por categoria de dieta.


    Returns:
        dict[str, list[str]]: Dicionário consolidado e ordenado pronto para geração das colunas.

    Example:
        >>> _sort_and_merge(
        ...     {
        ...         "Recreio nas Férias": ["refeicao", "lanche"]
        ...     },
        ...     {
        ...         "DIETA ESPECIAL - TIPO A": ["refeicao"]
        ...     }
        ... )
        {
            "Recreio nas Férias": ["lanche", "refeicao"],
            "DIETA ESPECIAL - TIPO A": ["refeicao"]
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
            key=lambda item: ORDEM_HEADERS_RECREIO_EMEI_EMEF[item[0]],
        )
    )

    return dict_periodos_dietas
