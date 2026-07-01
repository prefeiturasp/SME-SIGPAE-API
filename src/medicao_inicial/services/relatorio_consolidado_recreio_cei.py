from src.dados_comuns.constants import ORDEM_HEADERS_RECREIO_CEI, ORDEM_CAMPOS_RECREIO
from src.escola.models import FaixaEtaria
from src.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial
from src.medicao_inicial.services.utils import filtra_queryset_pelo_intervalo_de_dias, generate_columns, get_categorias_dietas, get_nome_periodo, update_dietas_alimentacoes, update_periodos_alimentacoes
from django.db.models import Q


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
            lista_alimentacoes = _get_lista_alimentacoes(medicao, nome_periodo, query_params)
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
            dict_periodos_dietas.items(), key=lambda item: ORDEM_HEADERS_RECREIO_CEI[item[0]]
        )
    )

    return dict_periodos_dietas
