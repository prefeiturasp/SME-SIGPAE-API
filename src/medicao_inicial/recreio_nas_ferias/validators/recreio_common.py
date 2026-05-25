from collections import defaultdict
from datetime import timedelta

from django.db.models import QuerySet

from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)
from src.medicao_inicial.recreio_nas_ferias.models import (
    RecreioNasFeriasUnidadeParticipante,
)
from src.medicao_inicial.utils import get_name_campo


def agrupar_tipos_alimentacao_por_categoria(
    tipos_alimentacao: QuerySet,
) -> dict[str, list]:
    """Agrupa tipos de alimentação por categoria removendo duplicados.

    Os tipos de alimentação são agrupados pelo nome da categoria e os
    valores duplicados são removidos preservando a ordem de inserção.

    Args:
        tipos_alimentacao (QuerySet):
            QuerySet contendo os tipos de alimentação com os relacionamentos
            ``categoria`` e ``tipo_alimentacao``.

    Returns:
        dict[str, list]: Dicionário onde a chave é o nome da categoria e o valor é a
            lista de tipos de alimentação sem duplicados.
    """
    agrupados = defaultdict(list)

    for tipo in tipos_alimentacao.select_related(
        "categoria",
        "tipo_alimentacao",
    ):
        agrupados[tipo.categoria.nome].append(tipo.tipo_alimentacao.nome)

    resultado = {
        categoria: list(dict.fromkeys(itens)) for categoria, itens in agrupados.items()
    }

    return resultado


def valida_campo_participantes(
    instance: SolicitacaoMedicaoInicial, informacoes_participantes: dict[str, int]
) -> None:
    """Cria valores de medição para o campo ``participantes``.

    Garante que exista um registro de ``ValorMedicao`` para o campo
    ``participantes`` da categoria ``ALIMENTAÇÃO`` para cada grupo e para
    todos os dias do período do Recreio nas Férias associado à solicitação
    de medição.

    Caso a medição do grupo ainda não exista, ela será criada. Os valores
    de medição são criados apenas quando ainda não existirem para evitar
    duplicidades.

    Args:
        instance (SolicitacaoMedicaoInicial): Instância da solicitação de medição inicial vinculada ao
            Recreio nas Férias.
        informacoes_participantes (dict[str, int]): Dicionário contendo a quantidade de participantes por grupo,
            onde a chave representa o nome do grupo e o valor a quantidade de participantes
    """
    recreio = instance.recreio_nas_ferias
    categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    grupos = list(informacoes_participantes.keys())
    grupos_medicao_existentes = {
        medicao.grupo.nome: medicao
        for medicao in instance.medicoes.filter(grupo__nome__in=grupos).select_related(
            "grupo"
        )
    }
    grupos_obj = {
        grupo.nome: grupo for grupo in GrupoMedicao.objects.filter(nome__in=grupos)
    }

    valores_medicao_a_criar = []
    inicio_recreio = recreio.data_inicio
    dias_totais = (recreio.data_fim - inicio_recreio).days

    for numero_dia in range(dias_totais + 1):
        dia = f"{(inicio_recreio + timedelta(days=numero_dia)).day:02d}"
        for grupo in grupos:
            medicao = grupos_medicao_existentes.get(grupo)
            if medicao is None:
                medicao = Medicao.objects.create(
                    solicitacao_medicao_inicial=instance,
                    grupo=grupos_obj[grupo],
                )
                grupos_medicao_existentes[grupo] = medicao

            if not medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                dia=dia,
                nome_campo="participantes",
            ).exists():
                valores_medicao_a_criar.append(
                    ValorMedicao(
                        medicao=medicao,
                        categoria_medicao=categoria,
                        dia=dia,
                        nome_campo="participantes",
                        valor=informacoes_participantes[grupo],
                    )
                )

    ValorMedicao.objects.bulk_create(valores_medicao_a_criar)


def get_linhas_da_tabela_alimentacoes_recreio(alimentacoes: list[str]) -> list[str]:
    """Monta as linhas esperadas da tabela de alimentações.

    Adiciona os campos obrigatórios de participantes e frequência,
    além das alimentações configuradas para o grupo.

    Também adiciona os campos de repetição quando aplicável.

    Args:
        alimentacoes (list[str]): Lista de alimentações configuradas para o grupo.

    Returns:
        list[str]:   Lista contendo os nomes dos campos esperados na tabela de lançamento.
    """
    linhas_da_tabela = ["participantes", "frequencia"]
    for alimentacao in alimentacoes:
        nome_formatado = get_name_campo(alimentacao)
        linhas_da_tabela.append(nome_formatado)
        if nome_formatado == "refeicao":
            linhas_da_tabela.append("repeticao_refeicao")
        if nome_formatado == "sobremesa":
            linhas_da_tabela.append("repeticao_sobremesa")
    return linhas_da_tabela


def buscar_valores_lancamento_alimentacoes_recreio(
    linhas_da_tabela: list[str],
    solicitacao: SolicitacaoMedicaoInicial,
    grupo: str,
    dias_letivos: list[str],
    categoria_medicao: CategoriaMedicao,
    lista_erros: list,
) -> list:
    """Valida os lançamentos das alimentações do recreio.

    Verifica se todos os campos esperados da tabela possuem
    valores preenchidos para todos os dias letivos do período.

    Quando existem dias sem preenchimento e sem observação
    justificando a ausência, adiciona erro na lista.

    Args:
        linhas_da_tabela (list[str]): Lista de campos esperados na tabela.
        solicitacao (SolicitacaoMedicaoInicial):  Solicitação de medição inicial.
        grupo (str):  Nome do grupo validado.
        dias_letivos (list[str]):  Lista de dias letivos formatados.
        categoria_medicao (CategoriaMedicao): Categoria de medição utilizada na validação.
        lista_erros (list): Lista acumulada de erros.

    Returns:
        list: Lista atualizada de erros encontrados.
    """
    periodo_com_erro = False
    dias_letivos_set = set(dias_letivos)

    for nome_campo in linhas_da_tabela:
        valores_da_medicao = set(
            ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao,
                nome_campo=nome_campo,
                medicao__grupo__nome=grupo,
                dia__in=dias_letivos,
                categoria_medicao=categoria_medicao,
            )
            .exclude(valor=None)
            .values_list("dia", flat=True)
        )

        if valores_da_medicao != dias_letivos_set:
            dias_sem_preenchimento = dias_letivos_set - valores_da_medicao
            if len(dias_sem_preenchimento) > 0:
                periodo_com_erro = True

    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": grupo,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def existe_colaborador(participantes: RecreioNasFeriasUnidadeParticipante) -> bool:
    """Verifica se existem colaboradores ativos no recreio.

    Retorna ``True`` quando a unidade participante possui número de
    colaboradores maior que zero e pelo menos um tipo de alimentação
    associado à categoria "Colaboradores". Caso contrário, retorna ``False``.

    Args:
        participantes (RecreioNasFeriasUnidadeParticipante): Instância de
            participante da unidade escolar no Recreio nas Férias.

    Returns:
        bool: ``True`` se houver colaboradores com alimentação configurada;
            ``False`` caso contrário.
    """
    if participantes.num_colaboradores > 0:
        tipos_alimentacao = participantes.tipos_alimentacao.filter(
            categoria__nome__in=["Colaboradores"]
        )
        tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(
            tipos_alimentacao
        )
        alimentacoes_colaboradores = tipos_alimentacao_map.get("Colaboradores", [])
        if len(alimentacoes_colaboradores) > 0:
            return True

    return False


def get_classificacoes_dietas_recreio(
    categorias: list[CategoriaMedicao], lista_alimentacoes: list[str]
) -> list[CategoriaMedicao]:
    """
    Filtra categorias de medição de dietas para recreio
    com base nos tipos de alimentação disponíveis.

    Regras:
    - Remove categorias contendo "ENTERAL" quando não existir:
        - Lanche
        - Lanche 4h
        - Refeição

    - Remove categorias contendo "DIETA ESPECIAL"quando não existir:
        - Lanche
        - Lanche 4h

    - Categorias ENTERAL são preservadas na regra de remoção de "DIETA ESPECIAL"

    Args:
        categorias (list[CategoriaMedicao]):  Lista de categorias de medição disponíveis.
        lista_alimentacoes (list[str]): Lista de alimentações habilitadas para a medição.

    Returns:
        list[CategoriaMedicao]: Lista de categorias filtradas conforme as regras de alimentação do recreio.
    """

    dicionario_alimentacao_dietas = {
        "Lanche": "lanche",
        "Lanche 4h": "lanche_4h",
        "Refeição": "refeicao",
    }
    alimentacoes = {
        dicionario_alimentacao_dietas[alimentacao]
        for alimentacao in lista_alimentacoes
        if alimentacao in dicionario_alimentacao_dietas
    }

    tem_lanche = "lanche" in alimentacoes or "lanche_4h" in alimentacoes
    tem_refeicao = "refeicao" in alimentacoes

    categorias_filtradas = []

    for categoria in categorias:
        nome = categoria.nome.upper()

        tem_enteral = "ENTERAL" in nome
        tem_dieta_especial = "DIETA ESPECIAL" in nome

        if not tem_lanche and not tem_refeicao and tem_enteral:
            continue

        if not tem_lanche and tem_dieta_especial and not tem_enteral:
            continue

        categorias_filtradas.append(categoria)
    return categorias_filtradas


def get_tipos_alimentacao_recreio(
    solicitacao: SolicitacaoMedicaoInicial,
) -> list[str]:
    """Retorna os tipos de alimentação dos inscritos no recreio.

    Busca os tipos de alimentação configurados para os participantes
    da categoria ``Inscritos`` e retorna os nomes agrupados por
    categoria.

    Args:
        recreio (RecreioNasFerias): Instância do recreio utilizada na consulta.

    Returns:
        list[str]: Lista contendo os tipos de alimentação dos inscritos.
    """
    recreio = solicitacao.recreio_nas_ferias
    participantes = recreio.unidades_participantes.filter(
        unidade_educacional=solicitacao.escola
    ).first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome="Inscritos",
    )

    return agrupar_tipos_alimentacao_por_categoria(
        tipos_alimentacao,
    ).get("Inscritos", [])
