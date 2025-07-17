import pandas as pd

from sme_sigpae_api.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial


def get_nome_periodo(medicao: Medicao) -> str:
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
    if nome_periodo in periodos_alimentacoes:
        periodos_alimentacoes[nome_periodo] += lista_alimentacoes
    else:
        periodos_alimentacoes[nome_periodo] = lista_alimentacoes
    return periodos_alimentacoes


def get_categorias_dietas(medicao: Medicao) -> list:
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
