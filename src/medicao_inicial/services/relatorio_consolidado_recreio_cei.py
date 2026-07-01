import math

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import FloatField, Q, Sum
from django.db.models.functions import Cast

from src.dados_comuns.constants import ORDEM_CAMPOS_RECREIO, ORDEM_HEADERS_RECREIO_CEI
from src.escola.models import FaixaEtaria
from src.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial
from src.medicao_inicial.services.ordenacao_unidades import ordenar_unidades
from src.medicao_inicial.services.utils import (
    filtra_queryset_pelo_intervalo_de_dias,
    generate_columns,
    get_categorias_dietas,
    get_nome_periodo,
    get_valores_iniciais,
    total_pagamento_colaboradores,
    update_dietas_alimentacoes,
    update_periodos_alimentacoes,
)


def get_alimentacoes_por_periodo(
    solicitacoes: list[SolicitacaoMedicaoInicial],
    query_params: dict | None = None,
) -> list[tuple]:
    """
     Obtém as alimentações organizadas por período e categoria de dieta.

    Percorre todas as medições das solicitações informadas, agrupando as
    alimentações de acordo com o período de atendimento e, quando existente,
    pelas categorias de dietas especiais. Ao final, os dados são ordenados e
    convertidos para o formato de colunas utilizado na geração dos relatórios.

    Args:
        solicitacoes (list[SolicitacaoMedicaoInicial]): Lista de solicitações de medição inicial que serão processadas.
        query_params (dict | None, optional):  Parâmetros utilizados para filtrar os valores das medições,
            normalmente relacionados ao intervalo de dias da consulta.
            Defaults to None.

    Returns:
        list[tuple]: Lista de colunas contendo os períodos, categorias de dietas e suas
            respectivas alimentações, pronta para utilização nos relatórios.
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

    dict_periodos_dietas = _sort_and_merge(periodos_alimentacoes, dietas_alimentacoes)
    columns = generate_columns(dict_periodos_dietas)

    return columns


def _get_lista_alimentacoes(
    medicao: Medicao, nome_periodo: str, query_params: dict | None = None
) -> list[int | str]:
    """
    Obtém a lista de alimentações disponíveis para uma medição.

    Para o grupo de colaboradores, retorna os nomes dos campos referentes às
    alimentações, desconsiderando campos de controle e categorias de dieta
    especial. Também adiciona os totais de refeições e sobremesas para
    pagamento.

    Para os demais grupos, retorna os identificadores das faixas etárias
    encontradas na medição, ordenadas pela idade inicial.

    Args:
        medicao (Medicao): Medição da qual serão extraídas as alimentações.
        nome_periodo (str):  Nome do período correspondente à medição.
        query_params (dict | None, optional): Parâmetros utilizados para filtrar os valores da medição.
            Defaults to None.

    Returns:
        list[int | str]:  Lista contendo os nomes das alimentações (para colaboradores)
            ou os identificadores das faixas etárias (demais grupos).
    """
    if nome_periodo == "Colaboradores":
        lista_alimentacoes = list(
            filtra_queryset_pelo_intervalo_de_dias(
                medicao.valores_medicao, query_params
            )
            .exclude(
                Q(
                    nome_campo__in=[
                        "observacoes",
                        "participantes",
                        "frequencia",
                    ]
                )
                | Q(categoria_medicao__nome__icontains="DIETA ESPECIAL")
            )
            .values_list("nome_campo", flat=True)
            .distinct()
        )
        lista_alimentacoes += [
            "total_refeicoes_pagamento",
            "total_sobremesas_pagamento",
        ]
        return lista_alimentacoes
    else:
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


def _get_lista_alimentacoes_dietas(
    medicao: Medicao, categoria: str, query_params: dict | None = None
) -> list[int | str]:
    """
    Obtém as alimentações pertencentes a uma categoria de dieta especial.

    Para colaboradores, retorna os nomes dos campos relacionados à categoria
    informada, excluindo campos utilizados apenas para controle.

    Para os demais grupos, retorna os identificadores das faixas etárias que
    possuem registros de frequência para a categoria de dieta

    Args:
        medicao (Medicao): Medição utilizada na consulta.
        categoria (str): Nome da categoria de dieta especial.
        query_params (dict | None, optional): Parâmetros utilizados para filtrar os valores da medição.
            Defaults to None.

    Returns:
        list[int | str]: Lista contendo os nomes das alimentações (para colaboradores)
            ou os identificadores das faixas etárias (demais grupos)
    """
    if medicao.grupo.nome == "Colaboradores":
        return list(
            filtra_queryset_pelo_intervalo_de_dias(
                medicao.valores_medicao, query_params
            )
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
    else:
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


def _sort_and_merge(periodos_alimentacoes: dict, dietas_alimentacoes: dict) -> dict:
    """
    Remove duplicidades, ordena e combina as alimentações por período e dieta.

    As alimentações são ordenadas conforme a ordem definida para as faixas
    etárias e para os campos de recreio. Em seguida, os períodos e categorias
    de dietas são agrupados em um único dicionário, cuja ordenação das chaves
    segue a configuração estabelecida em ``ORDEM_HEADERS_RECREIO_CEI``.

    Args:
        periodos_alimentacoes (dict): Dicionário contendo as alimentações agrupadas por período.
        dietas_alimentacoes (dict): Dicionário contendo as alimentações agrupadas por categoria de
            dieta especial.

    Returns:
        dict: Dicionário consolidado contendo períodos e dietas ordenados para
            utilização na geração do relatório.
    """
    ORDEM_CAMPOS = [
        faixa.id for faixa in FaixaEtaria.objects.filter(ativo=True).order_by("inicio")
    ] + ORDEM_CAMPOS_RECREIO

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
            key=lambda item: ORDEM_HEADERS_RECREIO_CEI[item[0]],
        )
    )

    return dict_periodos_dietas


def get_valores_tabela(
    solicitacoes: list[SolicitacaoMedicaoInicial],
    colunas: list[tuple],
    tipos_de_unidade: list[str],
    query_params: dict | None = None,
) -> list[list[str | float]]:
    """
    Monta as linhas da tabela do relatório de Recreio nas Férias.

    Para cada solicitação de medição inicial, são obtidas as informações
    iniciais da unidade e os valores correspondentes às colunas previamente
    definidas. Cada linha representa uma unidade educacional e contém os
    totais calculados para cada período e categoria de dieta especial.


    Args:
        solicitacoes (list[SolicitacaoMedicaoInicial]): Lista de solicitações que serão processadas.
        colunas (list[tuple]): Lista de colunas do relatório, composta pelo período e respectivo
            campo ou faixa etária.
        tipos_de_unidade (list[str]): Tipos de unidades considerados na geração da tabela.
        query_params (dict | None, optional):Parâmetros utilizados para filtrar os valores das medições,
            normalmente relacionados ao intervalo de dias.
            Defaults to None.

    Returns:
        list[list[str | float]]: Lista de linhas que compõem a tabela do relatório.
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


def _processa_periodo_campo(
    solicitacao: SolicitacaoMedicaoInicial,
    grupo: str,
    campo: int | str,
    valores: list[str],
    query_params: dict | None = None,
) -> list[str | float]:
    """
    Processa uma coluna do relatório para uma solicitação específica.

    Quando a coluna representa uma categoria de dieta especial, calcula o
    total correspondente ao campo informado e adiciona o resultado à lista de
    valores da linha. Caso ocorra algum erro durante o processamento,
    adiciona "-" para indicar ausência de informação

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação que está sendo processada.
        grupo (str): Nome do grupo ou da categoria correspondente à coluna.
        campo (int | str): Identificador do campo associado à coluna. Dependendo do contexto,
            pode representar uma faixa etária ou outro identificador utilizado
            no cálculo dos valores.
        valores (list[str]): Lista de valores da linha atualmente em construção.
        query_params (dict | None, optional):  Parâmetros utilizados para filtrar os valores das medições,
            normalmente relacionados ao intervalo de dias.
            Defaults to None.
    Returns:
        list[str | float]: Lista de valores atualizada com o resultado da coluna processada.
    """
    filtros = {}
    try:
        if "DIETA ESPECIAL" in grupo:
            filtros["grupo__nome"] = "Recreio nas Férias"
            total = processa_dieta_especial(
                solicitacao, filtros, campo, grupo, query_params
            )
        else:
            filtros["grupo__nome"] = grupo
            total = processa_grupos_recreio(
                solicitacao, filtros, campo, grupo, query_params
            )
        valores.append(total)
    except Exception:
        valores.append("-")
    return valores


def processa_dieta_especial(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict,
    faixa_etaria: int,
    periodo: str,
    query_params: dict | None = None,
) -> float | str:
    """
     Calcula o total de atendimentos de uma categoria de dieta especial.

    Percorre todas as medições da solicitação que atendem aos filtros
    informados, somando os valores registrados para a faixa etária e categoria
    de dieta. Caso não existam registros ou o total seja igual a zero, retorna
    "-"

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação cujas medições serão processadas.
        filtros (dict): Filtros utilizados para selecionar as medições.
        faixa_etaria (int): Identificador da faixa etária considerada no cálculo.
        periodo (str): Nome da categoria de dieta especial.
        query_params (dict | None, optional): Parâmetros utilizados para filtrar os valores das medições.
            Defaults to None.

    Returns:
        float | str: Soma dos valores encontrados ou "-" quando não houver registros
            válidos.
    """
    medicoes = solicitacao.medicoes.filter(**filtros)
    if not medicoes.exists():
        return "-"

    total = 0.0
    for medicao in medicoes:
        soma = _calcula_soma_medicao(
            medicao, "frequencia", faixa_etaria, periodo, query_params
        )
        if soma is not None:
            total += soma

    return "-" if math.isclose(total, 0.0, rel_tol=1e-9) else total


def _calcula_soma_medicao(
    medicao: Medicao,
    nome_campo: str,
    faixa_etaria: int,
    categoria: str,
    query_params: dict | None = None,
) -> float | None:
    """
    Calcula a soma dos valores registrados para uma medição.

    Considera apenas os registros que correspondem ao nome do campo, à faixa
    etária e à categoria informados, aplicando os filtros do intervalo de dias
    quando necessário.

    Args:
        medicao (Medicao):  Medição utilizada no cálculo.
        nome_campo (str): Nome do campo cujos valores serão somados.
        faixa_etaria (int):  Identificador da faixa etária utilizada na consulta. Pode ser
        ``None`` quando o cálculo não depende de faixa etária.
        categoria (str): Nome da categoria da medição.
        query_params (dict | None, optional): Parâmetros utilizados para filtrar os valores da medição.
            Defaults to None.

    Returns:
        float | None: Soma dos valores encontrados ou ``None`` quando não existirem
            registros correspondentes.
    """
    return (
        filtra_queryset_pelo_intervalo_de_dias(medicao.valores_medicao, query_params)
        .filter(
            nome_campo=nome_campo,
            faixa_etaria_id=faixa_etaria,
            categoria_medicao__nome=categoria,
        )
        .annotate(valor_float=Cast("valor", output_field=FloatField()))
        .aggregate(total=Sum("valor_float"))["total"]
    )


def processa_grupos_recreio(
    solicitacao: SolicitacaoMedicaoInicial,
    filtros: dict,
    campo_de_busca: int | str,
    periodo: str,
    query_params: dict | None = None,
) -> float | str:
    """
    Processa os valores de um grupo do relatório de Recreio nas Férias.

    Localiza a medição correspondente aos filtros informados e calcula o valor da
    coluna de acordo com o período. Para colaboradores, o cálculo pode considerar
    campos específicos ou os totais de pagamento de refeições e sobremesas. Para
    os demais grupos, o cálculo é realizado com base na faixa etária.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação cujas medições serão processadas.
        filtros (dict): Filtros utilizados para localizar a medição.
        campo_de_busca (int | str): Identificador utilizado no cálculo da coluna. Dependendo do período,
            pode representar o nome de um campo ou o identificador de uma faixa etária.
        periodo (str): Nome do período correspondente à coluna do relatório.
        query_params (dict | None, optional): Parâmetros utilizados para filtrar os valores das medições.
            Defaults to None.
    Returns:
        float | str: Valor calculado para a coluna ou "-" quando não houver registros
            correspondentes.
    """

    try:
        medicao = solicitacao.medicoes.get(**filtros)
    except ObjectDoesNotExist:
        return "-"

    if periodo == "Colaboradores":
        nome_campo = campo_de_busca
        faixa_etaria_id = None
    else:
        nome_campo = "frequencia"
        faixa_etaria_id = campo_de_busca

    if (
        nome_campo in ["total_refeicoes_pagamento", "total_sobremesas_pagamento"]
        and periodo == "Colaboradores"
    ):
        return total_pagamento_colaboradores(medicao, nome_campo, query_params)
    else:
        soma = _calcula_soma_medicao(
            medicao, nome_campo, faixa_etaria_id, "ALIMENTAÇÃO", query_params
        )
        return soma if soma is not None else "-"
