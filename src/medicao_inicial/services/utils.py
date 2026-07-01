import datetime
from calendar import monthrange

import pandas as pd

from src.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial


def get_nome_periodo(medicao: Medicao) -> str:
    """
    Obtém o nome formatado do período com base na medição.
    A formatação segue a seguinte lógica:
    - Se não há grupo associado: retorna apenas o nome do período escolar.
    - Se há grupo e período escolar: retorna "Nome do Grupo - Nome do Período".
    - Se há grupo mas não há período escolar: retorna apenas o nome do grupo.

    Args:
        medicao (Medicao): Objeto de medição contendo informações do período escolar e grupo associado.

    Returns:
        str: _Nome do período formatado de acordo com as regras descritas.
    """
    return (
        medicao.periodo_escolar.nome
        if not medicao.grupo
        else (
            f"{medicao.grupo.nome} - {medicao.periodo_escolar.nome}"
            if medicao.periodo_escolar
            else medicao.grupo.nome
        )
    )


def update_periodos_alimentacoes(
    periodos_alimentacoes: dict, nome_periodo: str, lista_alimentacoes: list
) -> dict:
    """
    Atualiza o dicionário de períodos com suas respectivas alimentações.

    Args:
        periodos_alimentacoes (dict): Dicionário onde as chaves são nomes de períodos e os valores são listas de alimentações.
        nome_periodo (str): Nome do período a ser atualizado ou criado.
        lista_alimentacoes (list): Lista de alimentações a ser adicionada ao período.

    Returns:
        dict: Dicionário atualizado com as alimentações do período.
    """
    if nome_periodo in periodos_alimentacoes:
        periodos_alimentacoes[nome_periodo] += lista_alimentacoes
    else:
        periodos_alimentacoes[nome_periodo] = lista_alimentacoes
    return periodos_alimentacoes


def get_categorias_dietas(medicao_ou_queryset) -> list:
    """
    Obtém lista de categorias de dietas especiais da medição.

    Args:
        medicao (Medicao):  Objeto de medição contendo os valores_medicao a serem consultados.

    Returns:
        list: Lista de strings com os nomes distintos das categorias de dietas especiais.

    Examples:
        >>> get_categorias_dietas(medicao)
        ['DIETA ESPECIAL - TIPO B', 'DIETA ESPECIAL - TIPO A - ENTERAL]
    """
    return list(
        (
            medicao_ou_queryset.valores_medicao
            if hasattr(medicao_ou_queryset, "valores_medicao")
            else medicao_ou_queryset
        )
        .exclude(categoria_medicao__nome__icontains="ALIMENTAÇÃO")
        .values_list("categoria_medicao__nome", flat=True)
        .distinct()
    )


def update_dietas_alimentacoes(
    dietas_alimentacoes: dict, categoria: str, lista_alimentacoes_dietas: list
):
    """
    Atualiza o dicionário de dietas com alimentações específicas da categoria.

    Args:
        dietas_alimentacoes (dict): Dicionário onde as chaves são nomes de categorias de dieta e os valores são listas de alimentações específicas.
        categoria (str): Nome da categoria de dieta a ser atualizada ou criada.
        lista_alimentacoes_dietas (list): Lista de alimentações específicas da categoria a ser adicionada.

    Returns:
        _type_: Dicionário atualizado com as alimentações da categoria, ou o dicionário original inalterado se a lista estiver vazia.
    """
    if lista_alimentacoes_dietas:
        if categoria in dietas_alimentacoes:
            dietas_alimentacoes[categoria] += lista_alimentacoes_dietas
        else:
            dietas_alimentacoes[categoria] = lista_alimentacoes_dietas
    return dietas_alimentacoes


def generate_columns(dict_periodos_dietas: dict) -> list:
    """
    Gera lista de colunas a partir de dicionário de períodos e dietas.
    Transforma um dicionário hierárquico em uma lista plana de tuplas, onde cada tupla representa uma coluna no formato (categoria, alimentação).

    Args:
        dict_periodos_dietas (dict):  Dicionário onde as chaves são categorias (períodos ou dietas) e os valores são listas de alimentações

    Returns:
        list: Lista de tuplas no formato [(categoria, alimentação), ...], contendo todas as combinações possíveis de categorias e suas respectivas alimentações.

    Examples:
        >>> generate_columns({"MANHA": ["lanche", "refeicao"],)
        [('MANHA', 'lanche'), ('MANHA', 'refeicao')]
    """
    columns = [
        (chave, valor)
        for chave, valores in dict_periodos_dietas.items()
        for valor in valores
    ]
    return columns


def get_valores_iniciais(solicitacao: SolicitacaoMedicaoInicial) -> list[str]:
    """
    Extrai informações iniciais básicas da escola da solicitação.

    Obtém um conjunto de dados fundamentais da escola associada à solicitação
    de medição inicial, incluindo sigla do tipo de unidade, código EOL e nome.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Objeto de solicitação de medição inicial contendo a escola associada

    Returns:
        list[str]: Lista com três elementos na ordem:
            [0] (str): Iniciais do tipo de unidade escolar (ex: "EMEF", "CEI")
            [1] (str): Código EOL da escola
            [2] (str): Nome completo da escola
    """
    return [
        (
            solicitacao.escola.tipo_unidade_historico(
                solicitacao.data_referencia
            ).iniciais
            if solicitacao.escola.tipo_unidade_historico(solicitacao.data_referencia)
            else ""
        ),
        solicitacao.escola.codigo_eol,
        solicitacao.escola.nome_historico(solicitacao.data_referencia),
    ]


def get_filtros_intervalo_dias(query_params: dict | None) -> dict:
    """
    Retorna os filtros de dia para o intervalo informado na query string.

    O relatório consolidado continua sendo mensal; portanto, quando ambas as
    datas são informadas, o recorte é aplicado apenas sobre o campo `dia`
    armazenado em `ValorMedicao`.
    """
    if not query_params:
        return {}

    data_inicial = query_params.get("data_inicial")
    data_final = query_params.get("data_final")
    if not (data_inicial and data_final):
        return {}

    dia_inicial = datetime.date.fromisoformat(data_inicial).day
    dia_final = datetime.date.fromisoformat(data_final).day
    return {
        "dia__gte": f"{dia_inicial:02d}",
        "dia__lte": f"{dia_final:02d}",
    }


def filtra_queryset_pelo_intervalo_de_dias(queryset, query_params: dict | None):
    """
    Aplica o recorte de dias sobre um queryset de `ValorMedicao`, quando houver.
    """
    filtros_dias = get_filtros_intervalo_dias(query_params)
    return queryset.filter(**filtros_dias) if filtros_dias else queryset


def get_lista_dias_periodo(
    mes: str | int, ano: str | int, query_params: dict | None = None
) -> range:
    """
    Retorna os dias que devem compor o relatório dentro do mês/ano informado.
    """
    filtros_dias = get_filtros_intervalo_dias(query_params)
    dia_inicial = int(filtros_dias.get("dia__gte", 1))
    dia_final = int(filtros_dias.get("dia__lte", monthrange(int(ano), int(mes))[1]))
    return range(dia_inicial, dia_final + 1)


def gera_colunas_alimentacao(
    aba: str,
    colunas: list[tuple],
    linhas: list[list[str | float]],
    writer: pd.ExcelWriter,
    nomes_campos: dict,
    colunas_fixas: list[tuple] | None = None,
    headers: list[tuple] | None = None,
) -> pd.DataFrame:
    """
    Gera e exporta DataFrame com colunas de alimentação para relatório Excel.

    Cria um DataFrame estruturado com MultiIndex para headers, adiciona linha de total e exporta para uma aba específica do arquivo
    Excel usando o ExcelWriter fornecido.

    Args:
        aba (str): Nome da aba/planilha onde os dados serão exportados.
        colunas (list[tuple]): Lista de tuplas no formato (período, campo) que define a estrutura das colunas dinâmicas.
        linhas (list[list[str | float]]): Matriz de dados onde cada lista interna representa uma linha do relatório
        writer (pd.ExcelWriter): Objeto ExcelWriter para exportação do DataFrame.
        nomes_campos (dict): Dicionário de mapeamento de campos para seus nomes exibíveis no header
        colunas_fixas (list[tuple] | None, optional): Colunas fixas iniciais do relatório. Defaults to [("", "Tipo"), ("", "Cód. EOL"), ("", "Unidade Escolar")].
        headers (list[tuple] | None, optional): Headers customizados. Se None, gera automaticamente baseado nas colunas e nomes_campos.

    Returns:
        pd.DataFrame: DataFrame processado com MultiIndex e linha de total.
    """
    if colunas_fixas is None:
        colunas_fixas = [
            ("", "Tipo"),
            ("", "Cód. EOL"),
            ("", "Unidade Escolar"),
        ]
    if headers is None:
        headers = [
            (
                chave.upper() if chave != "Solicitações de Alimentação" else "",
                nomes_campos[valor],
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
    df.rename(
        columns={"RECREIO NAS FÉRIAS": "ALIMENTAÇÕES ALUNOS PARTICIPANTES"},
        level=0,
        inplace=True,
    )
    df.to_excel(writer, sheet_name=aba, startrow=2, startcol=-1)
    return df
