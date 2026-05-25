import datetime
from collections import defaultdict
from datetime import timedelta

from django.db.models import QuerySet

from src.dieta_especial.solicitacao_dieta_especial.models import ClassificacaoDieta
from src.escola.models import Escola
from src.medicao_inicial.models import (
    CategoriaMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)
from src.medicao_inicial.recreio_nas_ferias.utils import gerar_dias_letivos_recreio
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_common import (
    agrupar_tipos_alimentacao_por_categoria,
    buscar_valores_lancamento_alimentacoes_recreio,
    existe_colaborador,
    get_classificacoes_dietas_recreio,
    get_linhas_da_tabela_alimentacoes_recreio,
    get_tipos_alimentacao_recreio,
    valida_campo_participantes,
)
from src.medicao_inicial.validators import (
    erros_unicos,
    get_classificacoes_dietas,
    lista_erros_com_periodo,
)

CATEGORIA_ALIMENTACAO_NOME = "ALIMENTAÇÃO"
CATEGORIA_DIETA_TIPO_A_ENTERAL_RESTRICAO_NOME = (
    "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
)
GRUPO_RECREIO = "Recreio nas Férias"


def cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de participantes do Recreio nas Férias.

    Cria registros de ``ValorMedicao`` para cada dia do período do recreio,
    considerando os grupos participantes disponíveis na unidade escolar.

    Os valores são criados apenas quando ainda não existem para o dia,
    categoria e grupo informados.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    recreio = instance.recreio_nas_ferias
    participantes = recreio.unidades_participantes.filter(
        unidade_educacional=instance.escola
    ).first()

    informacoes_participantes = {
        GRUPO_RECREIO: participantes.num_inscritos,
    }
    if existe_colaborador(participantes):
        informacoes_participantes["Colaboradores"] = participantes.num_colaboradores

    valida_campo_participantes(instance, informacoes_participantes)


def cria_valores_medicao_participantes_dietas_autorizadas_emef_emei_cieja_ceugestao(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de dietas autorizadas do recreio.

    Cria registros de ``ValorMedicao`` para categorias de dietas especiais
    durante o período do Recreio nas Férias, utilizando os logs de dietas
    autorizadas da escola.

    Os valores são criados apenas quando ainda não existem para o dia,
    categoria e grupo informados

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    escola = instance.escola
    recreio = instance.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    cria_valores_medicao_dietas_autorizadas_do_recreio(
        instance, logs_do_recreio, GRUPO_RECREIO
    )


def indexar_logs_dieta_autorizadas_por_data(
    logs_do_recreio: QuerySet,
) -> dict[datetime.date, dict[str, int]]:
    """Indexa logs de dietas autorizadas por data e nomenclatura da classificação.

    Agrupa os logs por data, somando as quantidades para cada classificação de dieta
    no dia correspondente. Os nomes das classificações são convertidos para minúsculas
    para facilitar a busca.

    Args:
        logs_do_recreio (QuerySet): QuerySet contendo os logs de dietas autorizadas
            para o período do recreio, com campos 'data', 'classificacao__nome' e 'quantidade'.

    Returns:
        dict[datetime.date, dict[str, int]]: Dicionário indexado por data, onde cada
            data mapeia para um dicionário de nomes de classificação (minúsculos) para
            a soma das quantidades.
    """
    logs_por_dia = defaultdict(lambda: defaultdict(int))

    for data_log, classificacao_nome, quantidade in logs_do_recreio.values_list(
        "data",
        "classificacao__nome",
        "quantidade",
    ):
        logs_por_dia[data_log][classificacao_nome.lower()] += quantidade

    return logs_por_dia


def _categoria_tem_logs_dieta_autorizada(
    categoria: CategoriaMedicao,
    logs_por_dia: dict[datetime.date, dict[str, int]],
) -> bool:
    """Verifica se uma categoria de medição possui logs de dietas autorizadas nos dados indexados.

    Para a categoria especial 'DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS',
    verifica se há logs contendo 'tipo a enteral' ou 'tipo a restrição de aminoácidos'.
    Para outras categorias, verifica se há logs contendo o termo extraído do nome da categoria,
    excluindo 'enteral' e 'aminoácidos'.

    Args:
        categoria (CategoriaMedicao): A categoria de medição a ser verificada.
        logs_por_dia (dict[datetime.date, dict[str, int]]): Dados indexados dos logs por data.

    Returns:
        bool: True se a categoria possui logs autorizados, False caso contrário.
    """
    if categoria.nome == CATEGORIA_DIETA_TIPO_A_ENTERAL_RESTRICAO_NOME:
        return any(
            any(
                "tipo a enteral" in nome or "tipo a restrição de aminoácidos" in nome
                for nome in logs_por_dia_do_dia
            )
            for logs_por_dia_do_dia in logs_por_dia.values()
        )

    termo = categoria.nome.split(" - ")[1].lower()
    return any(
        any(
            termo in nome and "enteral" not in nome and "aminoácidos" not in nome
            for nome in logs_por_dia_do_dia
        )
        for logs_por_dia_do_dia in logs_por_dia.values()
    )


def retorna_valor_para_log_dieta_autorizada(
    categoria: CategoriaMedicao,
    logs_por_dia: dict[datetime.date, dict[str, int]],
    data: datetime.date,
) -> int:
    """Retorna o valor total autorizado para a categoria e dia informados.

    Para categorias do tipo enteral/restrição de aminoácidos, realiza a soma
    das duas classificações.

    Args:
        categoria (CategoriaMedicao): Categoria de medição da dieta.
        logs_por_dia (dict): Logs de dietas autorizadas indexados por data.
        data (datetime.date): Data utilizada para filtrar os logs.

    Returns:
        int: Quantidade total autorizada para a categoria no dia informado.
    """
    logs_do_dia = logs_por_dia.get(data, {})
    if categoria.nome == CATEGORIA_DIETA_TIPO_A_ENTERAL_RESTRICAO_NOME:
        return sum(
            quantidade
            for nome, quantidade in logs_do_dia.items()
            if "tipo a enteral" in nome or "tipo a restrição de aminoácidos" in nome
        )

    termo = categoria.nome.split(" - ")[1].lower()
    return next(
        (
            quantidade
            for nome, quantidade in logs_do_dia.items()
            if termo in nome and "enteral" not in nome and "aminoácidos" not in nome
        ),
        0,
    )


def validate_lancamento_alimentacoes_medicao_recreio(
    solicitacao: SolicitacaoMedicaoInicial, lista_erros: list
) -> list:
    """Valida o preenchimento das alimentações do recreio.

    Verifica se todos os dias letivos do período do recreio possuem
    lançamentos preenchidos para os grupos e alimentações esperadas.

    Quando existem dias sem preenchimento e sem justificativa
    de observação, adiciona erro à lista de erros.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição inicial do recreio.
        lista_erros (list): Lista acumulada de erros de validação.

    Returns:
        list: Lista de erros sem duplicidade.
    """

    recreio = solicitacao.recreio_nas_ferias
    participantes = recreio.unidades_participantes.filter(
        unidade_educacional=solicitacao.escola
    ).first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )
    tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)
    informacoes_alimentacao = {
        GRUPO_RECREIO: tipos_alimentacao_map.get("Inscritos", [])
    }
    if existe_colaborador(participantes):
        informacoes_alimentacao["Colaboradores"] = tipos_alimentacao_map.get(
            "Colaboradores", []
        )
    dias_letivos_geral = gerar_dias_letivos_recreio(
        recreio.data_inicio, recreio.data_fim
    )
    dias_letivos_geral_formatado = [f"{dia:02d}" for dia in dias_letivos_geral]
    categoria_alimentacao = CategoriaMedicao.objects.get(
        nome=CATEGORIA_ALIMENTACAO_NOME
    )

    informacoes = {
        "solicitacao": solicitacao,
        "grupos_recreio": informacoes_alimentacao,
        "dias_letivos": dias_letivos_geral_formatado,
        "categoria_alimentacao": categoria_alimentacao,
    }
    lista_erros = validar_lancamentos_alimentacoes_recreio(informacoes, lista_erros)
    return lista_erros


def validate_lancamento_dietas_medicao_recreio(
    solicitacao: SolicitacaoMedicaoInicial, lista_erros: list
) -> list:
    """Valida os lançamentos de dietas do Recreio nas Férias.

    Verifica se todas as dietas autorizadas possuem lançamentos
    preenchidos na medição para todos os dias letivos do período
    do recreio.

    A validação considera:
        - categorias de dieta cadastradas;
        - classificações vinculadas às dietas;
        - dias letivos do período;
        - logs de dietas autorizadas;
        - valores lançados na medição.

    Quando existem dietas autorizadas sem lançamento correspondente,
    adiciona erro à lista e interrompe a validação do período.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
        lista_erros (list): Lista acumulada de erros de validação.

    Returns:
        list: Lista de erros sem duplicidade.
    """
    recreio = solicitacao.recreio_nas_ferias
    categorias = CategoriaMedicao.objects.filter(nome__icontains="dieta")
    medicao_recreio = solicitacao.medicoes.filter(grupo__nome=GRUPO_RECREIO).first()

    dias_letivos = [
        f"{dia:02d}"
        for dia in gerar_dias_letivos_recreio(
            recreio.data_inicio,
            recreio.data_fim,
        )
    ]

    tipos_alimentacao = get_tipos_alimentacao_recreio(solicitacao)
    valores_medicao = get_valores_medicao_set(
        medicao_recreio,
        categorias,
    )
    logs_indexados = get_logs_indexados_recreio(
        solicitacao.escola,
        recreio.data_inicio,
        recreio.data_fim,
    )
    categorias_validas = get_classificacoes_dietas_recreio(
        categorias, tipos_alimentacao
    )
    cache_classificacoes = {
        categoria.id: get_classificacoes_dietas(categoria)
        for categoria in categorias_validas
    }

    for categoria in categorias_validas:
        classificacoes = cache_classificacoes.get(categoria.id)
        nomes_campos = get_linhas_da_tabela_dieta_recreio(tipos_alimentacao, categoria)
        for dia in dias_letivos:

            if lista_erros_com_periodo(lista_erros, medicao_recreio, "dietas"):
                return erros_unicos(lista_erros)

            periodo_com_erro = validate_lancamento_dietas(
                dia=dia,
                categoria=categoria,
                classificacoes=classificacoes,
                valores_medicao=valores_medicao,
                nomes_campos=nomes_campos,
                mes=solicitacao.mes,
                ano=solicitacao.ano,
                logs_indexados=logs_indexados,
            )

            if periodo_com_erro:
                lista_erros.append(
                    {
                        "periodo_escolar": medicao_recreio.grupo.nome,
                        "erro": "Restam dias a serem lançados nas dietas.",
                    }
                )
                return erros_unicos(
                    lista_erros,
                )

    return erros_unicos(lista_erros)


def validate_lancamento_dietas(
    dia: str,
    categoria: CategoriaMedicao,
    classificacoes: list[ClassificacaoDieta],
    valores_medicao: dict,
    nomes_campos: list[str],
    mes: str,
    ano: str,
    logs_indexados: dict,
) -> bool:
    """Valida os lançamentos de dietas para um dia específico.

    Verifica se existem dietas autorizadas registradas nos logs
    para a categoria e dia informados e valida se todos os campos
    esperados possuem lançamento correspondente na medição.

    A validação considera:
        - classificações vinculadas à categoria;
        - quantidade total registrada nos logs;
        - campos obrigatórios da tabela de dietas;
        - valores lançados na medição.

    Args:
        dia (str):  Dia validado no formato ``DD``.
        categoria (CategoriaMedicao):  Categoria de medição da dieta.
        classificacoes (list[ClassificacaoDieta]):  Lista de classificações vinculadas à categoria.
        valores_medicao (dict): Estrutura indexada contendo os valores lançados na medição.
        nomes_campos (list[str]): Lista de campos obrigatórios da tabela de dietas.
        mes (str): Mês de referência da validação.
        ano (str):  Ano de referência da validação.
        logs_indexados (dict): Estrutura indexada contendo os logs de dietas
            autorizadas agrupados por data e classificação.

    Returns:
        bool: ``True`` quando existe lançamento pendente.
            ``False`` quando todos os lançamentos obrigatórios
            estão preenchidos ou não existem dietas autorizadas
            para o dia informado.
    """
    data_referencia = datetime.date(
        int(ano),
        int(mes),
        int(dia),
    )

    classificacoes_ids = {classificacao.id for classificacao in classificacoes}

    quantidade_total = sum(
        logs_indexados.get(
            (
                data_referencia,
                classificacao_id,
            ),
            0,
        )
        for classificacao_id in classificacoes_ids
    )

    if quantidade_total == 0:
        return False

    for nome_campo in nomes_campos:
        valor_existe = (
            nome_campo,
            categoria.id,
            dia,
        ) in valores_medicao

        if not valor_existe:
            return True

    return False


def get_linhas_da_tabela_dieta_recreio(
    alimentacoes: list[str], categoria: CategoriaMedicao
) -> list[str]:
    """Monta os campos esperados da tabela de dietas do recreio.

    Define os campos obrigatórios da tabela de lançamento de dietas
    com base nas alimentações configuradas para o recreio e na
    categoria de medição informada.

    A tabela sempre possui o campo de frequência e adiciona
    campos adicionais conforme os tipos de alimentação disponíveis.

    Args:
        alimentacoes (list[str]):  Lista de alimentações configuradas para o recreio.
        categoria (CategoriaMedicao): Categoria de medição utilizada na validação.

    Returns:
        list[str]:  Lista contendo os nomes dos campos esperados
            para lançamento das dietas.
    """
    nomes_campos = ["frequencia"]
    if "Lanche" in alimentacoes:
        nomes_campos.append("lanche")
    if "Lanche 4h" in alimentacoes:
        nomes_campos.append("lanche_4h")
    if "Refeição" in alimentacoes and "ENTERAL" in categoria.nome:
        nomes_campos.append("refeicao")
    return nomes_campos


def get_logs_indexados_recreio(
    escola: Escola,
    inicio_recreio: datetime.date,
    fim_recreio: datetime.date,
) -> dict:
    """Retorna os logs de dietas autorizadas indexados por data e classificação.

    Busca os logs de dietas autorizadas da escola dentro do período
    do recreio e agrupa as quantidades por data e classificação
    da dieta.

    A estrutura retornada é utilizada para otimizar consultas
    durante as validações de lançamento das dietas.


    Args:
        escola (Escola): Escola utilizada na busca dos logs.
        inicio_recreio (datetime.date): Data inicial do período do recreio.
        fim_recreio (datetime.date): Data final do período do recreio.

    Returns:
        dict: Dicionário indexado por tupla contendo:

            - data do log;
            - identificador da classificação da dieta.

            O valor armazenado representa a quantidade total
            registrada para a combinação informada.
    """
    logs = (
        escola.logs_dietas_autorizadas_recreio_ferias.filter(
            data__range=[
                inicio_recreio,
                fim_recreio,
            ]
        )
        .values_list(
            "data",
            "classificacao_id",
            "quantidade",
        )
        .distinct()
        .order_by(
            "data",
            "classificacao_id",
        )
    )

    logs_indexados = defaultdict(int)

    for (
        data_log,
        classificacao_id,
        quantidade,
    ) in logs:
        logs_indexados[
            (
                data_log,
                classificacao_id,
            )
        ] += quantidade

    return logs_indexados


def get_valores_medicao_set(
    medicao: Medicao,
    categorias: list[CategoriaMedicao],
) -> set:
    """Retorna os valores da medição indexados em formato de conjunto.

    Busca os valores de medição vinculados às categorias informadas
    e retorna uma estrutura otimizada para validações de existência
    durante o processamento das dietas.

    Cada item do conjunto contém:
        - nome do campo;
        - identificador da categoria de medição;
        - dia do lançamento.

    Args:
        medicao (Medicao):  Medição utilizada na busca dos valores lançados.
        categorias (list[CategoriaMedicao]):  Lista de categorias de medição utilizadas no filtro.

    Returns:
        set: onjunto contendo tuplas no formato: ``(nome_campo, categoria_medicao_id, dia)``
    """
    valores_medicao = (
        medicao.valores_medicao.filter(
            categoria_medicao__in=categorias,
        )
        .values_list(
            "nome_campo",
            "categoria_medicao_id",
            "dia",
        )
        .distinct()
    )

    return set(valores_medicao)


def cria_valores_medicao_dietas_autorizadas_do_recreio(
    instance: SolicitacaoMedicaoInicial, logs_do_recreio: QuerySet, grupo: str
) -> None:
    """Cria registros de ``ValorMedicao`` para dietas autorizadas do recreio.

    Processa os logs de dietas autorizadas do período do Recreio nas Férias,
    identifica as categorias de dietas aplicáveis e cria registros de
    ``ValorMedicao`` para os dias e categorias ainda não existentes.

    A criação considera apenas categorias que possuem logs associados e
    evita duplicidade para o mesmo dia e categoria.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial
            vinculada ao recreio.
        logs_do_recreio(QuerySet): Logs de dietas autorizadas filtrados para o período
            do recreio.
        grupo(str): Nome do grupo do recreio
    """
    recreio = instance.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)

    categorias = list(CategoriaMedicao.objects.filter(nome__icontains="dieta"))
    tipos_alimentacao = get_tipos_alimentacao_recreio(instance)
    categorias_validas = get_classificacoes_dietas_recreio(
        categorias, tipos_alimentacao
    )
    categorias_com_logs = [
        categoria
        for categoria in categorias_validas
        if _categoria_tem_logs_dieta_autorizada(categoria, logs_por_dia)
    ]

    if not categorias_com_logs:
        return

    medicao = instance.medicoes.get(grupo__nome=grupo)
    valores_existentes = set(
        medicao.valores_medicao.filter(
            categoria_medicao__in=categorias_com_logs,
            nome_campo="dietas_autorizadas",
        ).values_list("categoria_medicao_id", "dia")
    )

    valores_medicao_a_criar = []
    dias_totais = (fim_recreio - inicio_recreio).days

    for numero_dia in range(dias_totais + 1):
        data = inicio_recreio + timedelta(days=numero_dia)
        dia = f"{data.day:02d}"

        for categoria in categorias_com_logs:
            if (categoria.id, dia) in valores_existentes:
                continue

            valor = retorna_valor_para_log_dieta_autorizada(
                categoria, logs_por_dia, data
            )
            valores_medicao_a_criar.append(
                ValorMedicao(
                    medicao=medicao,
                    categoria_medicao=categoria,
                    dia=dia,
                    nome_campo="dietas_autorizadas",
                    valor=valor,
                )
            )

    ValorMedicao.objects.bulk_create(valores_medicao_a_criar)


def validar_lancamentos_alimentacoes_recreio(
    informacoes_alimentacao: dict, lista_erros: list
) -> list:
    """Valida os lançamentos de alimentações do recreio por grupo.

    Percorre os grupos do Recreio nas Férias, obtém as linhas da tabela
    de alimentações de cada grupo e busca inconsistências nos lançamentos
    realizados para a solicitação informada.

    Ao final, retorna a lista de erros consolidada sem duplicidades

    Args:
        informacoes_alimentacao (dict): Dicionário contendo as informações
            necessárias para validação dos colaboradores, incluindo:
            - ``grupos_recreio``: dados dos grupos de recreio a serem validados;
            - ``solicitacao``: solicitação de medição inicial;
            - ``dias_letivos``: lista de dias letivos formatados;
            - ``categoria_alimentacao``: categoria de medição utilizada na
        lista_erros (list): Lista acumulada de erros encontrados durante
            as validações.

    Returns:
        list: Lista de erros únicos identificados durante a validação dos
            lançamentos.
    """
    solicitacao = informacoes_alimentacao.get("solicitacao")
    grupos_recreio = informacoes_alimentacao.get("grupos_recreio")
    dias_letivos = informacoes_alimentacao.get("dias_letivos")
    categoria_alimentacao = informacoes_alimentacao.get("categoria_alimentacao")

    grupos = list(grupos_recreio.keys())
    for grupo in grupos:
        linhas_da_tabela = get_linhas_da_tabela_alimentacoes_recreio(
            grupos_recreio[grupo]
        )
        lista_erros = buscar_valores_lancamento_alimentacoes_recreio(
            linhas_da_tabela,
            solicitacao,
            grupo,
            dias_letivos,
            categoria_alimentacao,
            lista_erros,
        )
    return erros_unicos(lista_erros)
