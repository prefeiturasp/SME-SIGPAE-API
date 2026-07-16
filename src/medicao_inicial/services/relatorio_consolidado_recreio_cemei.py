import pandas as pd
from django.db.models import Q
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from src.dados_comuns.constants import (
    NOMES_CAMPOS,
    ORDEM_CAMPOS_RECREIO,
    ORDEM_HEADERS_RECREIO_CEMEI,
    ORDEM_UNIDADES_GRUPO_CEMEI,
)
from src.escola.models import FaixaEtaria
from src.medicao_inicial.models import (
    Medicao,
    SolicitacaoMedicaoInicial,
)
from src.medicao_inicial.services import (
    relatorio_consolidado_recreio_cei,
    relatorio_consolidado_recreio_emei_emef,
)
from src.medicao_inicial.services.ordenacao_unidades import ordenar_unidades
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

PROGRAMAS_E_PROJETOS = "PROGRAMAS E PROJETOS"
DIETA_ESPECIAL_TIPO_A = "DIETA ESPECIAL - TIPO A"
DIETA_ESPECIAL_TIPO_A_ENTERAL = (
    "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
)
RECREIO_NAS_FERIAS_CEI = "Recreio nas Férias - de 0 a 3 anos e 11 meses"
RECREIO_NAS_FERIAS_EMEI = "Recreio nas Férias - 4 a 14 anos"


def get_alimentacoes_por_periodo(
    solicitacoes: list[SolicitacaoMedicaoInicial],
    query_params: dict | None = None,
) -> list[tuple]:
    """Obtém as colunas de alimentações agrupadas por período e categoria de dieta.

    Percorre todas as medições das solicitações informadas, identifica os tipos
    de alimentação existentes em cada período e nas categorias de dieta especial,
    unifica as dietas equivalentes e retorna a estrutura de colunas utilizada na
    geração do relatório consolidado.

    Args:
        solicitacoes: Lista de solicitações de medição inicial.
        query_params: Parâmetros utilizados para filtrar os valores da medição,
            como intervalo de dias.

    Returns:
        Lista de tuplas representando as colunas do relatório consolidado.
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
                if "infantil" in nome_periodo.lower():
                    nome_categoria = categoria + " - INFANTIL"
                else:
                    nome_categoria = f"{categoria} - {nome_periodo.upper()}"
                dietas_alimentacoes = update_dietas_alimentacoes(
                    dietas_alimentacoes, nome_categoria, lista_alimentacoes_dietas
                )

    dietas_alimentacoes = _unificar_dietas(dietas_alimentacoes)
    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = generate_columns(dict_periodos_dietas)
    return columns


def _get_lista_alimentacoes(
    medicao: Medicao, nome_periodo: str, query_params: dict | None = None
) -> list[int | str]:
    """Obtém as alimentações disponíveis para uma medição.

    Para grupos de Recreio nas Férias destinados ao CEI são retornadas as
    faixas etárias ou os campos específicos de colaboradores. Para os demais
    grupos, retorna os nomes dos campos de alimentação existentes na medição.

    Args:
        medicao: Medição utilizada na consulta.
        nome_periodo: Nome do período correspondente à medição.
        query_params: Parâmetros utilizados para filtrar os valores da medição.

    Returns:
        Lista contendo os identificadores das faixas etárias ou os nomes dos
        campos de alimentação.
    """
    if medicao.grupo.nome == RECREIO_NAS_FERIAS_CEI:
        return list(
            faixa.id
            for faixa in FaixaEtaria.objects.filter(
                id__in=filtra_queryset_pelo_intervalo_de_dias(
                    medicao.valores_medicao, query_params
                )
                .filter(nome_campo="frequencia")
                .values_list("faixa_etaria", flat=True)
            )
            .distinct()
            .order_by("inicio")
        )
    else:
        lista_alimentacoes = sorted(
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
    medicao: Medicao, categoria: str, query_params: dict | None = None
) -> list[int | str]:
    """Obtém as alimentações disponíveis para uma categoria de dieta especial.

    Args:
        medicao: Medição utilizada na consulta.
        categoria: Categoria da dieta especial.
        query_params: Parâmetros utilizados para filtrar os valores da medição.

    Returns:
        Lista contendo os identificadores das faixas etárias ou os nomes dos
        campos associados à categoria informada.
    """
    if medicao.grupo.nome == RECREIO_NAS_FERIAS_CEI:
        return list(
            faixa.id
            for faixa in FaixaEtaria.objects.filter(
                id__in=filtra_queryset_pelo_intervalo_de_dias(
                    medicao.valores_medicao, query_params
                )
                .filter(categoria_medicao__nome=categoria, nome_campo="frequencia")
                .values_list("faixa_etaria", flat=True)
            )
            .distinct()
            .order_by("inicio")
        )
    else:
        return sorted(
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


def _unificar_dietas(dietas_alimentacoes: dict) -> dict:
    """Unifica categorias equivalentes de dieta especial.

    As dietas do tipo "Tipo A - Enteral / Restrição de Aminoácidos" são
    agrupadas juntamente com as dietas do tipo "Tipo A".

    Args:
        dietas_alimentacoes: Dicionário contendo as categorias de dieta e suas
            respectivas alimentações.

    Returns:
        Dicionário com as categorias de dieta unificadas.
    """
    dietas_unificadas = {}

    for categoria, alimentacoes in dietas_alimentacoes.items():
        categoria_normalizada = categoria.replace(
            DIETA_ESPECIAL_TIPO_A_ENTERAL,
            DIETA_ESPECIAL_TIPO_A,
            1,
        )
        dietas_unificadas.setdefault(categoria_normalizada, [])
        dietas_unificadas[categoria_normalizada].extend(alimentacoes)

    return dietas_unificadas


def _sort_and_merge(periodos_alimentacoes: dict, dietas_alimentacoes: dict) -> dict:
    """Ordena e combina os períodos e categorias de dieta.

    Remove valores duplicados, ordena as alimentações conforme a configuração
    definida para o relatório CEMEI e une os períodos regulares às categorias de
    dieta especial.

    Args:
        periodos_alimentacoes: Alimentações agrupadas por período.
        dietas_alimentacoes: Alimentações agrupadas por categoria de dieta.

    Returns:
        Dicionário ordenado contendo períodos e dietas.
    """
    ORDEM_CAMPOS_CEMEI = [
        faixa.id for faixa in FaixaEtaria.objects.filter(ativo=True).order_by("inicio")
    ] + ORDEM_CAMPOS_RECREIO

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
            dict_periodos_dietas.items(), key=lambda item: ORDEM_HEADERS_RECREIO_CEMEI[item[0]]
        )
    )
    return dict_periodos_dietas


def get_valores_tabela(
    solicitacoes: list[SolicitacaoMedicaoInicial],
    colunas: list[tuple],
    query_params: dict | None = None,
) -> list[list[str | float]]:
    """Monta as linhas da tabela do relatório consolidado.

    Para cada solicitação são obtidos os dados iniciais e os valores
    correspondentes a todas as colunas do relatório.

    Args:
        solicitacoes: Lista de solicitações de medição inicial.
        colunas: Colunas que compõem o relatório.
        query_params: Parâmetros utilizados para filtrar os valores da medição.

    Returns:
        Lista de linhas da tabela consolidada.
    """
    valores = []
    for solicitacao in ordenar_unidades(solicitacoes):
        valores_solicitacao_atual = []
        valores_solicitacao_atual += get_valores_iniciais(solicitacao)
        for periodo, campo in colunas:
            valores_solicitacao_atual = _processa_periodo_campo(
                solicitacao,
                periodo,
                campo,
                valores_solicitacao_atual,
                query_params,
            )
        valores.append(valores_solicitacao_atual)
    return valores


def get_solicitacoes_ordenadas(
    solicitacoes: list[SolicitacaoMedicaoInicial],
) -> list[SolicitacaoMedicaoInicial]:
    """Ordena as solicitações conforme o tipo de unidade escolar.

    Args:
        solicitacoes: Lista de solicitações de medição inicial.

    Returns:
        Lista de solicitações ordenadas.
    """
    return sorted(
        solicitacoes,
        key=lambda k: ORDEM_UNIDADES_GRUPO_CEMEI[k.escola.tipo_unidade.iniciais],
    )


def _define_filtro(periodo: str) -> dict:
    """Define os filtros utilizados para localizar uma medição.

    Para períodos de dieta especial é utilizado um filtro por trecho do nome
    do grupo. Nos demais casos é realizada uma comparação exata.

    Args:
        periodo: Nome do período ou categoria do relatório.

    Returns:
        Dicionário contendo os filtros para consulta das medições.
    """
    filtros = {}
    if "DIETA ESPECIAL" in periodo:
        filtros["grupo__nome__icontains"] = periodo.split(" - ")[-1]
    else:
        filtros["grupo__nome"] = periodo
    return filtros


def _processa_periodo_campo(
    solicitacao: SolicitacaoMedicaoInicial,
    periodo: str,
    campo: str,
    valores: list[str],
    query_params: dict | None = None,
) -> list[str | float]:
    """Processa um campo do relatório para um determinado período.

    Direciona o processamento para o fluxo de dieta especial ou período
    regular e adiciona o resultado à lista de valores. Em caso de erro,
    adiciona "-" como valor padrão.

    Args:
        solicitacao: Solicitação de medição inicial.
        periodo: Período ou categoria do relatório.
        campo: Campo de alimentação a ser processado.
        valores: Lista de valores da linha em construção.
        query_params: Parâmetros utilizados para filtrar os valores da medição.

    Returns:
        Lista de valores atualizada.
    """
    filtros = _define_filtro(periodo)
    try:
        if "DIETA ESPECIAL" in periodo:
            total = _processa_dieta_especial(
                solicitacao, filtros, campo, periodo, query_params
            )
        else:
            total = _processa_periodo_regular(
                solicitacao, filtros, campo, periodo, query_params
            )
        valores.append(total)
    except Exception:
        valores.append("-")
    return valores


def _processa_dieta_especial(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict,
    campo: str,
    periodo: str,
    query_params: dict | None = None,
) -> str | float:
    """Processa um campo referente às dietas especiais.

    Encaminha o processamento para o serviço correspondente ao tipo de
    Recreio nas Férias (CEI ou EMEI).

    Args:
        solicitacao: Solicitação de medição inicial.
        filtros: Filtros utilizados para localizar a medição.
        campo: Campo de alimentação.
        periodo: Categoria de dieta especial.
        query_params: Parâmetros utilizados para filtrar os valores da medição.

    Returns:
        Valor calculado para o campo ou "-" quando não aplicável.
    """
    soma = "-"
    periodo_nome = periodo.split(" - ")[-1]
    categoria = " - ".join(periodo.split(" - ")[:2])
    if periodo_nome in RECREIO_NAS_FERIAS_CEI.upper():
        soma = relatorio_consolidado_recreio_cei.processa_dieta_especial(
            solicitacao, filtros, campo, categoria, query_params
        )
    elif periodo_nome in RECREIO_NAS_FERIAS_EMEI.upper():
        soma = relatorio_consolidado_recreio_emei_emef.processa_dieta_especial(
            solicitacao, filtros, campo, categoria, query_params
        )
    return soma


def _processa_periodo_regular(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict,
    campo: str,
    periodo: str,
    query_params: dict | None = None,
) -> str | float:
    """Processa um campo de um período regular do relatório.

    Encaminha o processamento para o serviço responsável pelo tipo de grupo
    correspondente ao período informado.

    Args:
        solicitacao: Solicitação de medição inicial.
        filtros: Filtros utilizados para localizar a medição.
        campo: Campo de alimentação.
        periodo: Nome do período.
        query_params: Parâmetros utilizados para filtrar os valores da medição.

    Returns:
        Valor calculado para o campo ou "-" quando não aplicável.
    """
    soma = "-"
    if periodo == RECREIO_NAS_FERIAS_CEI:
        soma = relatorio_consolidado_recreio_cei.processa_grupos_recreio(
            solicitacao, filtros, campo, periodo, query_params
        )
    elif periodo in [RECREIO_NAS_FERIAS_EMEI, "Solicitações de Alimentação", "Colaboradores"]:
        soma = relatorio_consolidado_recreio_emei_emef.processa_grupos_recreio(
            solicitacao,
            filtros,
            campo,
            periodo,
            query_params=query_params,
            tipo_unidade="EMEI",
        )
    return soma


def insere_tabela_periodos_na_planilha(
    aba: str,
    colunas: list[tuple],
    linhas: list[list[str | float]],
    writer: pd.ExcelWriter,
) -> pd.DataFrame:
    """Insere a tabela consolidada na planilha Excel.

    Atualiza o mapeamento de nomes das faixas etárias e delega a criação do
    DataFrame formatado para a geração do relatório.

    Args:
        aba: Nome da aba da planilha.
        colunas: Colunas da tabela.
        linhas: Linhas da tabela.
        writer: Escritor utilizado para gerar o arquivo Excel.

    Returns:
        DataFrame correspondente à tabela gerada.
    """
    NOMES_CAMPOS.update(
        {faixa.id: faixa.__str__() for faixa in FaixaEtaria.objects.filter(ativo=True)}
    )
    df = gera_colunas_alimentacao(aba, colunas, linhas, writer, NOMES_CAMPOS)
    return df


def ajusta_layout_tabela(
    workbook: Workbook, worksheet: Worksheet, df: pd.DataFrame
) -> None:
    """Aplica a formatação visual da tabela na planilha Excel.

    Configura as cores dos cabeçalhos, largura das colunas, altura das linhas
    e demais estilos utilizados no relatório consolidado.

    Args:
        workbook: Workbook do arquivo Excel.
        worksheet: Planilha que receberá a formatação.
        df: DataFrame utilizado como base para os cabeçalhos.
    """
    formatacao_base = {
        "align": "center",
        "valign": "vcenter",
        "font_color": "#FFFFFF",
        "bold": True,
        "border": 1,
        "border_color": "#999999",
    }
    formatacao_alunos = workbook.add_format({**formatacao_base, "bg_color": "#E8BE25"})

    formatacao_colaboradores = workbook.add_format(
        {**formatacao_base, "bg_color": "#B40C02"}
    )
    formatacao_infantil = workbook.add_format({**formatacao_base, "bg_color": "#2F80ED"})
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
        "ALIMENTAÇÕES TURMA INFANTIL": formatacao_infantil,
        "COLABORADORES": formatacao_colaboradores,
        "DIETA TIPO A": formatacao_dieta_a,
        "DIETA TIPO A - INFANTIL": formatacao_dieta_a,
        "DIETA TIPO B": formatacao_dieta_b,
    }

    for col_num, value in enumerate(df.columns.values):
        worksheet.write(
            2,
            col_num,
            value[0],
            formatacao_level1[value[0]],
        )
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
