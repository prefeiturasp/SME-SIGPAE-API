import pandas as pd

from sme_sigpae_api.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial


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


def get_categorias_dietas(medicao: Medicao) -> list:
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
        medicao.valores_medicao.exclude(
            categoria_medicao__nome__icontains="ALIMENTAÇÃO"
        )
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
    columns = [
        (chave, valor)
        for chave, valores in dict_periodos_dietas.items()
        for valor in valores
    ]
    return columns


def get_valores_iniciais(solicitacao: SolicitacaoMedicaoInicial) -> list[str]:
    return [
        solicitacao.escola.tipo_unidade.iniciais,
        solicitacao.escola.codigo_eol,
        solicitacao.escola.nome,
    ]


def gera_colunas_alimentacao(
    aba: str,
    colunas: list[tuple],
    linhas: list[list[str | float]],
    writer: pd.ExcelWriter,
    nomes_campos: dict,
    colunas_fixas: list[tuple] | None = None,
    headers: list[tuple] | None = None,
) -> pd.DataFrame:
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

    df.to_excel(writer, sheet_name=aba, startrow=2, startcol=-1)
    return df
