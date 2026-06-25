import math

import pandas as pd
from django.db.models import FloatField, Q, Sum
from django.db.models.functions import Cast
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from src.dados_comuns.constants import (
    NOMES_CAMPOS,
    ORDEM_CAMPOS,
    ORDEM_HEADERS_RECREIO_EMEI_EMEF,
)
from src.medicao_inicial.models import (
    CategoriaMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
)
from src.medicao_inicial.services.ordenacao_unidades import ordenar_unidades
from src.medicao_inicial.services.relatorio_consolidado_emei_emef import (
    _get_total_pagamento,
)
from src.medicao_inicial.services.utils import (
    filtra_queryset_pelo_intervalo_de_dias,
    generate_columns,
    gera_colunas_alimentacao,
    get_categorias_dietas,
    get_nome_periodo,
    get_valores_iniciais,
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


def get_valores_tabela(
    solicitacoes: list[SolicitacaoMedicaoInicial],
    colunas: list[tuple],
    tipos_de_unidade: list[str],
    query_params: dict[str, str],
) -> list:
    """
    Monta as linhas da tabela consolidada do relatório.

    Para cada solicitação de medição, calcula os valores correspondentes às colunas previamente geradas pelo relatório. Cada linha resultante representa uma unidade
    educacional e contém os valores agregados para períodos de alimentação e dietas especiais.

    Args:
        solicitacoes (list[SolicitacaoMedicaoInicial]): Lista de solicitações de medição que compõem o relatório.
        colunas (list[tuple]): Lista de colunas formatadas para composição do relatório consolidado.
        tipos_de_unidade (list[str]): Tipos de unidade considerados na geração do relatório.
        query_params (dict[str, str]): Filtros utilizados para restringir os registros processados.

    Returns:
        list: Lista contendo uma linha para cada solicitação processada.
    """
    dietas_especiais = CategoriaMedicao.objects.filter(
        nome__icontains="DIETA ESPECIAL"
    ).values_list("nome", flat=True)
    valores = []
    for solicitacao in ordenar_unidades(solicitacoes):
        valores_solicitacao_atual = []
        valores_solicitacao_atual += get_valores_iniciais(solicitacao)
        for grupo, campo in colunas:
            valores_solicitacao_atual = _processa_periodo_campo(
                solicitacao,
                grupo,
                campo,
                valores_solicitacao_atual,
                dietas_especiais,
                query_params,
            )
        valores.append(valores_solicitacao_atual)
    return valores


def _processa_periodo_campo(
    solicitacao: SolicitacaoMedicaoInicial,
    grupo: str,
    campo: str,
    valores: list[str],
    dietas_especiais: list[CategoriaMedicao],
    query_params: dict[str, str],
) -> list:
    """
    Processa uma combinação de período e campo da tabela.

    Determina os filtros aplicáveis ao período informado e calcula o valor correspondente para a solicitação atual. Em caso de erro durante
    o processamento, adiciona "-" como valor padrão.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição em processamento.
        grupo (str): Nome do grupo ou categoria de dieta especial.
        campo (str): Nome do campo que será totalizado.
        valores (list[str]): Lista acumuladora dos valores da linha atual.
        dietas_especiais (list[CategoriaMedicao]): Lista contendo os nomes das categorias de dietas especiais.
        query_params (dict[str, str]): Filtros utilizados para restringir os registros processados.

    Returns:
        list: Lista atualizada com o valor calculado para o campo.
    """
    filtros = {}
    try:
        if grupo in dietas_especiais:
            filtros["grupo__nome"] = "Recreio nas Férias"
            total = processa_dieta_especial(
                solicitacao, filtros, campo, grupo, query_params
            )
        else:
            filtros["grupo__nome"] = grupo
            total = processa_grupos_recreio(
                solicitacao, filtros, campo, grupo, query_params
            )
        if total is None:
            total = "-"
        valores.append(total)
    except Exception:
        valores.append("-")
    return valores


def processa_dieta_especial(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict[str, str],
    campo: str,
    grupo: str,
    query_params: dict[str, str],
) -> str | float:
    """
    Calcula o total de um campo para uma dieta especial.

    Localiza as medições compatíveis com os filtros informados e soma os
    valores do campo para a categoria de dieta correspondente.

    A categoria "DIETA ESPECIAL - TIPO A" considera também os registros da
    categoria "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE
    AMINOÁCIDOS", consolidando ambos os resultados.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição em processamento.
        filtros (dict[str, str]): Filtros utilizados para localizar as medições.
        campo (str): Nome do campo que será totalizado.
        grupo (str): Nome da categoria de dieta especial.
        query_params (dict[str, str]): Filtros utilizados para restringir os registros processados.

    Returns:
        str | float: Valor total calculado ou "-" quando não houver dados.
    """
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
        if grupo == "DIETA ESPECIAL - TIPO A"
        else [grupo]
    )
    total = 0.0
    for medicao in medicoes:
        soma = _calcula_soma_medicao(medicao, campo, categorias, query_params)
        if soma is not None:
            total += soma

    return "-" if math.isclose(total, 0.0, rel_tol=1e-9) else total


def _calcula_soma_medicao(
    medicao: Medicao, campo: str, categorias: list[str], query_params: dict[str, str]
) -> float:
    """
    Calcula a soma de um campo em uma medição.

    Filtra os valores da medição pelo intervalo de dias informado e realiza
    a soma dos registros pertencentes às categorias especificadas.


    Args:
        medicao (Medicao): Medição que será processada.
        campo (str): Nome do campo que será totalizado.
        categorias (list[str]): Categorias de medição consideradas na soma.
        query_params (dict[str, str]): Filtros utilizados para restringir os registros processados.

    Returns:
        float: Soma dos valores encontrados ou None quando não houver registros.
    """
    return (
        filtra_queryset_pelo_intervalo_de_dias(medicao.valores_medicao, query_params)
        .filter(nome_campo=campo, categoria_medicao__nome__in=categorias)
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))["total"]
    )


def processa_grupos_recreio(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict[str, str],
    campo: str,
    grupo: str,
    query_params: dict[str, str],
    tipo_unidade: str = None,
) -> str | float:
    """
    Calcula o valor de um campo para um grupo de alimentação do Recreio.

    Localiza a medição correspondente aos filtros informados e retorna o valor agregado para o campo solicitado.

    Para os campos de pagamento, o cálculo é delegado para ``_get_total_pagamento()``, que aplica as regras específicas conforme o tipo da unidade educacional.
    Para os demais campos, realiza a soma dos valores registrados na medição utilizando as categorias apropriadas para o grupo informado.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição em processamento.
        filtros (dict[str, str]): Filtros utilizados para localizar a medição.
        campo (str): Nome do campo que será calculado.
        grupo (str): Nome do grupo ou período de alimentação.
        query_params (dict[str, str]): Filtros utilizados para restringir os registros processados.
        tipo_unidade (str, optional): Sigla do tipo de unidade utilizada no cálculo dos campos de pagamento. Quando não informado,
            utiliza o tipo da unidade associada à escola da solicitação. Defaults: None.

    Returns:
        str | float: Valor total calculado para o campo informado ou "-" quando não existirem registros compatíveis.
    """
    medicao = solicitacao.medicoes.get(**filtros)

    iniciais = (
        solicitacao.escola.tipo_unidade.iniciais
        if tipo_unidade is None
        else tipo_unidade
    )
    if campo in ["total_refeicoes_pagamento", "total_sobremesas_pagamento"]:
        return _get_total_pagamento(medicao, campo, iniciais, query_params)

    categorias = (
        [grupo.upper()] if grupo == "Solicitações de Alimentação" else ["ALIMENTAÇÃO"]
    )
    soma = _calcula_soma_medicao(medicao, campo, categorias, query_params)
    return soma if soma is not None else "-"


def insere_tabela_periodos_na_planilha(
    aba: str, colunas: list[tuple], linhas: list[list[str]], writer: pd.ExcelWriter
) -> pd.DataFrame:
    """
    Gera e insere a tabela consolidada de períodos na planilha Excel.

    Cria um DataFrame estruturado a partir das colunas e linhas do relatório e o escreve na aba informada do arquivo Excel utilizando o writer fornecido.

    A estrutura gerada contém os dados consolidados de alimentações, colaboradores e dietas especiais que serão posteriormente formatados para exibição
    o relatório.

    Args:
        aba (str): Nome da aba onde a tabela será inserida.
        colunas (list[tuple]): Estrutura de colunas utilizada na composição da tabela.
        linhas (list[list[str]]): Dados que compõem as linhas da tabela. Cada item representa uma unidade educacional.
        writer (pd.ExcelWriter): Instância do ExcelWriter responsável pela escrita do arquivo.

    Returns:
        pd.DataFrame: DataFrame gerado e inserido na planilha.
    """
    df = gera_colunas_alimentacao(aba, colunas, linhas, writer, NOMES_CAMPOS)
    return df


def ajusta_layout_tabela(
    workbook: Workbook, worksheet: Worksheet, df: pd.DataFrame
) -> None:
    """
    Aplica a formatação visual da tabela no arquivo Excel.

    Configura estilos, cores, alinhamentos, larguras de coluna e alturas de linha para o relatório consolidado.

    A formatação é aplicada de acordo com o grupo representado no primeiro nível das colunas do DataFrame:
        - Alimentações de alunos participantes.
        - Colaboradores.
        - Dieta Especial - Tipo A.
        - Dieta Especial - Tipo B.

    Também configura os cabeçalhos multinível da planilha e ajusta o layout para melhorar a visualização dos dados exportados.

    Args:
        workbook (Workbook): Instância do workbook do XlsxWriter utilizada para criação dos formatos da planilha.
        worksheet (Worksheet): Aba que receberá a formatação.
        df (pd.DataFrame): DataFrame utilizado como origem dos cabeçalhos da tabela. Espera-se que as colunas estejam estruturadas como MultiIndex.

    Returns:
        None.

    """
    formatacao_base = {
        "align": "center",
        "valign": "vcenter",
        "font_color": "#FFFFFF",
        "bold": True,
        "border": 1,
        "border_color": "#999999",
    }
    formatacao_alunos = workbook.add_format({**formatacao_base, "bg_color": "#198459"})
    formatacao_colaboradores = workbook.add_format(
        {**formatacao_base, "bg_color": "#B40C02"}
    )
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
        "ALIMENTAÇÕES ALUNOS PARTICIPANTES": formatacao_alunos,
        "COLABORADORES": formatacao_colaboradores,
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
