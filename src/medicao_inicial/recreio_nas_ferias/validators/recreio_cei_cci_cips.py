import datetime
from collections import defaultdict
from datetime import timedelta

from django.db.models import QuerySet

from src.dieta_especial.solicitacao_dieta_especial.models import ClassificacaoDieta
from src.escola.models import Escola, FaixaEtaria
from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)
from src.medicao_inicial.recreio_nas_ferias.utils import gerar_dias_letivos_recreio
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    agrupar_tipos_alimentacao_por_categoria,
    buscar_valores_lancamento_alimentacoes_recreio,
    existe_colaborador,
    get_classificacoes_dietas_recreio,
    get_linhas_da_tabela_alimentacoes_recreio,
    get_tipos_alimentacao_recreio,
)
from src.medicao_inicial.validators import erros_unicos, lista_erros_com_periodo

CATEGORIA_ALIMENTACAO_NOME = "ALIMENTAÇÃO"
CATEGORIA_DIETA_TIPO_A = "DIETA ESPECIAL - TIPO A"


def cria_valores_medicao_participantes_cei(instance: SolicitacaoMedicaoInicial) -> None:
    """Cria os valores de medição de participantes do Recreio nas Férias de unidades CEI.

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
        "Recreio nas Férias": participantes.num_inscritos,
    }
    if existe_colaborador(participantes):
        informacoes_participantes["Colaboradores"] = participantes.num_colaboradores

    grupos = list(informacoes_participantes.keys())

    categoria = CategoriaMedicao.objects.get(nome=CATEGORIA_ALIMENTACAO_NOME)
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


def cria_valores_medicao_participantes_dietas_autorizadas_cei(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de dietas autorizadas do recreio CEI.

    Cria registros de ``ValorMedicao`` para categorias de dietas especiais
    durante o período do Recreio nas Férias, utilizando os logs de dietas
    autorizadas da escola indexados por data, faixa etária e classificação..

    Os valores são criados para cada combinação de categoria, dia e faixa
    etária, apenas quando ainda não existir um registro correspondente.

    Somente categorias que possuam logs compatíveis no período do recreio
    são consideradas para criação dos valores.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    escola = instance.escola
    recreio = instance.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio = escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
        data__range=[inicio_recreio, fim_recreio],
        faixa_etaria__isnull=False,
    )
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)

    grupo = "Recreio nas Férias"
    categorias = list(
        CategoriaMedicao.objects.filter(
            nome__in=[CATEGORIA_DIETA_TIPO_A, "DIETA ESPECIAL - TIPO B"]
        )
    )
    tipos_alimentacao = get_tipos_alimentacao_recreio(instance)
    categorias_validas = get_classificacoes_dietas_recreio(
        categorias, tipos_alimentacao
    )
    categorias_com_logs = [
        categoria
        for categoria in categorias_validas
        if _categoria_tem_logs_dieta_autorizada_cei(categoria, logs_por_dia)
    ]

    if not categorias_com_logs:
        return

    medicao = instance.medicoes.get(grupo__nome=grupo)
    valores_existentes = set(
        medicao.valores_medicao.filter(
            categoria_medicao__in=categorias_com_logs,
            nome_campo="dietas_autorizadas",
        ).values_list("categoria_medicao_id", "dia", "faixa_etaria")
    )

    valores_medicao_a_criar = []
    dias_totais = (fim_recreio - inicio_recreio).days
    faixas = FaixaEtaria.objects.filter(ativo=True)
    for numero_dia in range(dias_totais + 1):
        data = inicio_recreio + timedelta(days=numero_dia)
        dia = f"{data.day:02d}"
        for categoria in categorias_com_logs:
            for faixa_etaria in faixas:
                if (categoria.id, dia, faixa_etaria.id) in valores_existentes:
                    continue
                valor = retorna_valor_para_log_dieta_autorizada_cei(
                    categoria, logs_por_dia, data, faixa_etaria
                )
                valores_medicao_a_criar.append(
                    ValorMedicao(
                        medicao=medicao,
                        categoria_medicao=categoria,
                        dia=dia,
                        nome_campo="dietas_autorizadas",
                        valor=valor,
                        faixa_etaria=faixa_etaria,
                    )
                )

    ValorMedicao.objects.bulk_create(valores_medicao_a_criar)


def indexar_logs_dieta_autorizadas_por_data(
    logs_do_recreio: QuerySet,
) -> dict[datetime.date, dict[str, int]]:
    """Indexa logs de dietas autorizadas por data, faixa etária e classificação.

    Agrupa os logs por data e faixa etária, somando as quantidades para cada
    classificação de dieta correspondente. Os nomes das classificações são
    convertidos para minúsculas para facilitar buscas e comparações.

    Estrutura retornada:

        {
            data: {
                faixa_etaria: {
                    classificacao_nome: quantidade
                }
            }
        }

    Args:
        logs_do_recreio (QuerySet): QuerySet contendo os logs de dietas autorizadas
            para o período do recreio, com campos 'data', 'faixa_etaria', classificacao__nome' e 'quantidade'.

    Returns:
        dict[datetime.date, dict[str, int]]: Dicionário indexado por data, onde cada
            data mapeia para um dicionário de nomes de classificação (minúsculos) para
            a soma das quantidades.
    """
    logs_por_dia = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for (
        data_log,
        faixa_etaria,
        classificacao_nome,
        quantidade,
    ) in logs_do_recreio.values_list(
        "data", "faixa_etaria", "classificacao__nome", "quantidade"
    ):
        logs_por_dia[data_log][faixa_etaria][classificacao_nome.lower()] += quantidade

    return logs_por_dia


def _categoria_tem_logs_dieta_autorizada_cei(
    categoria: CategoriaMedicao,
    logs_por_dia: dict[datetime.date, dict[str, int]],
) -> bool:
    """Verifica se uma categoria de medição possui registros de dietas autorizadas.

    Percorre os logs indexados por data e faixa etária para identificar se há
    registros compatíveis com a categoria informada.

    Para a categoria especial ``TIPO A``, verifica a existência de qualquer
    classificação contendo ``"tipo a"`` nos logs.

    Para as demais categorias, extrai o termo da categoria a partir do nome
    (segmento após ``" - "``) e verifica se esse termo está presente nas
    classificações registradas.

    Os dados recebidos possuem a seguinte estrutura:

        {
            data: {
                faixa_etaria: {
                    classificacao_nome: quantidade
                }
            }
        }


    Args:
        categoria (CategoriaMedicao): A categoria de medição a ser verificada.
        logs_por_dia (dict[datetime.date, dict[str, int]]): Dados indexados dos logs por data.

    Returns:
        bool: True se a categoria possui logs autorizados, False caso contrário.
    """
    termo = (
        "tipo a"
        if categoria.nome == CATEGORIA_DIETA_TIPO_A
        else categoria.nome.split(" - ")[1].lower()
    )

    return any(
        termo in nome
        for logs_do_dia in logs_por_dia.values()
        for logs_por_faixa in logs_do_dia.values()
        for nome in logs_por_faixa
    )


def retorna_valor_para_log_dieta_autorizada_cei(
    categoria: CategoriaMedicao,
    logs_por_dia: dict[datetime.date, dict[str, int]],
    data: datetime.date,
    faixa_etaria: FaixaEtaria,
) -> int:
    """Retorna a quantidade autorizada para uma categoria, data e faixa etária.

    Os logs são indexados por data e faixa etária, contendo as classificações
    das dietas autorizadas e suas respectivas quantidades acumuladas.

    Estrutura esperada:

        {
            data: {
                faixa_etaria: {
                    classificacao_nome: quantidade
                }
            }
        }

    Para a categoria especial ``TIPO A``, realiza a soma de todas as
    classificações que contenham ``"tipo a"``.

    Para as demais categorias, retorna a primeira quantidade registrada para a
    faixa etária e data informadas.

    Args:
        categoria (CategoriaMedicao): Categoria de medição da dieta.
        logs_por_dia (dict): Logs de dietas autorizadas indexados por data e faixa etária..
        data (datetime.date): Data utilizada para filtrar os logs.
        faixa_etaria (FaixaEtaria): Faixa etária utilizada para filtrar os logs.

    Returns:
        int: Quantidade total autorizada para a categoria na data e faixa etária informado. Retorna ``0`` quando não houver registros.
    """
    logs_do_dia = logs_por_dia.get(data, {}).get(faixa_etaria.id, {})
    if categoria.nome == CATEGORIA_DIETA_TIPO_A:
        return sum(
            quantidade for nome, quantidade in logs_do_dia.items() if "tipo a" in nome
        )
    termo = categoria.nome.split(" - ")[1].lower()

    return sum(quantidade for nome, quantidade in logs_do_dia.items() if termo in nome)


def validate_lancamento_alimentacoes_medicao_recreio_cei(
    solicitacao: SolicitacaoMedicaoInicial, lista_erros: list
) -> list:
    """ "Valida os lançamentos das alimentações da medição do Recreio nas Férias para CEI.

    Realiza a validação dos lançamentos de alimentações dos participantes do
    grupo ``Recreio nas Férias`` e, quando existirem colaboradores na unidade,
    também valida os lançamentos do grupo ``Colaboradores``.

    As validações consideram os dias letivos do período do recreio e os tipos
    de alimentação configurados para cada categoria.

    Os erros encontrados durante as validações são acumulados e retornados sem
    duplicidades.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição inicial
            vinculada ao Recreio nas Férias.

        lista_erros (list): Lista acumulada de erros encontrados durante as
            validações.

    Returns:
        list: Lista de erros sem duplicidades após a validação dos lançamentos
            das alimentações do recreio.
    """
    recreio = solicitacao.recreio_nas_ferias
    participantes = recreio.unidades_participantes.filter(
        unidade_educacional=solicitacao.escola
    ).first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )
    tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)
    categoria_medicao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    dias_letivos_geral = gerar_dias_letivos_recreio(
        recreio.data_inicio, recreio.data_fim
    )
    dias_letivos_geral_formatado = [f"{dia:02d}" for dia in dias_letivos_geral]

    informacoes_inscritos = {
        "solicitacao": solicitacao,
        "dias_letivos": dias_letivos_geral_formatado,
        "categoria_alimentacao": categoria_medicao,
    }

    lista_erros = validate_lancamento_alimentacoes_inscritos(
        informacoes_inscritos, lista_erros
    )
    if existe_colaborador(participantes):
        alimentacao_colaboradores = tipos_alimentacao_map.get("Colaboradores", [])
        informacoes_colaboradores = {
            "alimentacoes": alimentacao_colaboradores,
            "solicitacao": solicitacao,
            "dias_letivos": dias_letivos_geral_formatado,
            "categoria_alimentacao": categoria_medicao,
        }
        lista_erros = validate_lancamento_alimentacoes_colaboradores(
            informacoes_colaboradores, lista_erros
        )

    return erros_unicos(lista_erros)


def validate_lancamento_alimentacoes_inscritos(
    informacoes_inscritos, lista_erros: list
) -> list:
    """Valida os lançamentos das alimentações dos inscritos do Recreio nas Férias.

    Verifica se todos os lançamentos esperados das alimentações por faixa
    etária foram preenchidos para os dias letivos informados no grupo
    ``Recreio nas Férias``.

    Os erros encontrados durante a validação são adicionados à lista e, ao
    final, são retornados sem duplicidades.

    Args:
        informacoes_inscritos (dict): Dicionário contendo as informações
            necessárias para validação dos inscritos, incluindo:
            - ``solicitacao``: solicitação de medição inicial;
            - ``dias_letivos``: lista de dias letivos formatados;
            - ``categoria_alimentacao``: categoria de medição utilizada na
            validação.

        lista_erros (list): Lista acumulada de erros encontrados durante as
            validações.

    Returns:
        list: Lista de erros sem duplicidades após a validação dos
            lançamentos das alimentações dos inscritos.
    """

    solicitacao = informacoes_inscritos.get("solicitacao")
    dias_letivos = informacoes_inscritos.get("dias_letivos")
    categoria_alimentacao = informacoes_inscritos.get("categoria_alimentacao")

    lista_erros = buscar_valores_lancamento_alimentacoes_faixa_etaria(
        solicitacao,
        "Recreio nas Férias",
        dias_letivos,
        categoria_alimentacao,
        lista_erros,
    )
    return erros_unicos(lista_erros)


def validate_lancamento_alimentacoes_colaboradores(
    informacoes_colaboradores: dict, lista_erros: list
) -> list:
    """Valida os lançamentos das alimentações do grupo de colaboradores.

    Obtém as linhas esperadas da tabela de alimentações do recreio e verifica
    se todos os lançamentos necessários do grupo ``Colaboradores`` foram
    preenchidos para os dias letivos informados.

    Os erros encontrados durante a validação são adicionados à lista e, ao
    final, são retornados sem duplicidades.

    Args:
        informacoes_colaboradores (dict): Dicionário contendo as informações
            necessárias para validação dos colaboradores, incluindo:
            - ``alimentacoes``: dados das alimentações configuradas;
            - ``solicitacao``: solicitação de medição inicial;
            - ``dias_letivos``: lista de dias letivos formatados;
            - ``categoria_alimentacao``: categoria de medição utilizada na
            validação.

        lista_erros (list): Lista acumulada de erros encontrados durante as
            validações.


    Returns:
        list: Lista de erros sem duplicidades após a validação dos
            lançamentos das alimentações dos colaboradores.

    """
    alimentacoes = informacoes_colaboradores.get("alimentacoes")
    solicitacao = informacoes_colaboradores.get("solicitacao")
    dias_letivos = informacoes_colaboradores.get("dias_letivos")
    categoria_alimentacao = informacoes_colaboradores.get("categoria_alimentacao")

    linhas_da_tabela = get_linhas_da_tabela_alimentacoes_recreio(alimentacoes)
    lista_erros = buscar_valores_lancamento_alimentacoes_recreio(
        linhas_da_tabela,
        solicitacao,
        "Colaboradores",
        dias_letivos,
        categoria_alimentacao,
        lista_erros,
    )
    return erros_unicos(lista_erros)


def buscar_valores_lancamento_alimentacoes_faixa_etaria(
    solicitacao: SolicitacaoMedicaoInicial,
    grupo: str,
    dias_letivos: list[str],
    categoria_medicao: CategoriaMedicao,
    lista_erros: list,
) -> list:
    """Valida os lançamentos das alimentações do recreio por faixa etária.

    Verifica se existem valores preenchidos para todos os dias letivos do
    período, considerando cada faixa etária ativa para o grupo e categoria
    informados.

    Quando existem dias sem preenchimento para alguma faixa etária, adiciona erro na lista.

    Args:
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

    valores = (
        ValorMedicao.objects.filter(
            medicao__solicitacao_medicao_inicial=solicitacao,
            nome_campo="frequencia",
            medicao__grupo__nome=grupo,
            dia__in=dias_letivos,
            categoria_medicao=categoria_medicao,
            faixa_etaria__ativo=True,
        )
        .exclude(valor=None)
        .values_list("faixa_etaria_id", "dia")
    )

    valores_por_faixa = defaultdict(set)

    for faixa_id, dia in valores:
        valores_por_faixa[faixa_id].add(dia)

    for faixa_id in FaixaEtaria.objects.filter(ativo=True).values_list("id", flat=True):
        valores_da_medicao = valores_por_faixa[faixa_id]
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


def validate_lancamento_dietas_medicao_recreio_cei(
    solicitacao: SolicitacaoMedicaoInicial, lista_erros: list
) -> list:
    """Valida os lançamentos de dietas do Recreio nas Férias para CEI.

    Verifica se todas as dietas autorizadas possuem lançamentos preenchidos
    na medição para todos os dias letivos do período do recreio, considerando
    as faixas etárias ativas.

    A validação considera:
        - categorias de dieta cadastradas;
        - classificações vinculadas às dietas;
        - dias letivos do período;
        - logs de dietas autorizadas indexados por data, classificação e faixa etária;
        - valores lançados na medição por faixa etária.

    Quando existem dietas autorizadas sem lançamento correspondente,
    adiciona erro à lista e interrompe a validação do período.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição inicial
            vinculada ao recreio.

        lista_erros (list): Lista acumulada de erros de validação.

    Returns:
        list: Lista de erros sem duplicidades.
    """
    recreio = solicitacao.recreio_nas_ferias
    categorias = list(
        CategoriaMedicao.objects.filter(
            nome__in=[CATEGORIA_DIETA_TIPO_A, "DIETA ESPECIAL - TIPO B"]
        )
    )
    medicao_recreio = solicitacao.medicoes.filter(
        grupo__nome="Recreio nas Férias"
    ).first()

    dias_letivos = [
        f"{dia:02d}"
        for dia in gerar_dias_letivos_recreio(
            recreio.data_inicio,
            recreio.data_fim,
        )
    ]

    tipos_alimentacao = get_tipos_alimentacao_recreio(solicitacao)
    valores_medicao = get_valores_medicao_cei(
        medicao_recreio,
        categorias,
    )
    logs_indexados = get_logs_indexados_recreio_cei(
        solicitacao.escola,
        recreio.data_inicio,
        recreio.data_fim,
    )
    categorias_validas = get_classificacoes_dietas_recreio(
        categorias, tipos_alimentacao
    )
    cache_classificacoes = {
        categoria.id: get_classificacoes_dietas_cei(categoria)
        for categoria in categorias_validas
    }
    faixas = FaixaEtaria.objects.filter(ativo=True)
    for categoria in categorias_validas:
        classificacoes = cache_classificacoes.get(categoria.id)
        for dia in dias_letivos:
            if lista_erros_com_periodo(lista_erros, medicao_recreio, "dietas"):
                return erros_unicos(lista_erros)
            for faixa in faixas:
                periodo_com_erro = validate_lancamento_dietas_cei(
                    dia=dia,
                    categoria=categoria,
                    classificacoes=classificacoes,
                    valores_medicao=valores_medicao,
                    mes=solicitacao.mes,
                    ano=solicitacao.ano,
                    logs_indexados=logs_indexados,
                    faixa_etaria=faixa,
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


def get_valores_medicao_cei(
    medicao: Medicao,
    categorias: list[CategoriaMedicao],
) -> set:
    """Retorna os valores da medição indexados em formato de conjunto.

    Busca os valores de medição vinculados às categorias informadas e retorna
    uma estrutura otimizada para validações de existência durante o
    processamento das dietas.

    Cada item do conjunto contém:
        - nome do campo;
        - identificador da categoria de medição;
        - dia do lançamento;
        - identificador da faixa etária.

    Args:
        medicao (Medicao): Medição utilizada na busca dos valores lançados.

        categorias (list[CategoriaMedicao]): Lista de categorias de medição
            utilizadas no filtro.

    Returns:
        set: Conjunto contendo tuplas no formato:

            ``(nome_campo, categoria_medicao_id, dia, faixa_etaria_id)``
    """
    valores_medicao = (
        medicao.valores_medicao.filter(
            categoria_medicao__in=categorias, nome_campo="frequencia"
        )
        .values_list("nome_campo", "categoria_medicao_id", "dia", "faixa_etaria")
        .distinct()
    )
    return set(valores_medicao)


def get_logs_indexados_recreio_cei(
    escola: Escola,
    inicio_recreio: datetime.date,
    fim_recreio: datetime.date,
) -> dict:
    """Retorna os logs de dietas autorizadas indexados por data, classificação e faixa etária.

    Busca os logs de dietas autorizadas da escola dentro do período do
    recreio e agrupa as quantidades por data, classificação da dieta e
    faixa etária.

    A estrutura retornada é utilizada para otimizar consultas durante as
    validações de lançamento das dietas.

    Args:
        escola (Escola): Escola utilizada na busca dos logs.

        inicio_recreio (datetime.date): Data inicial do período do recreio.

        fim_recreio (datetime.date): Data final do período do recreio.

    Returns:
        dict: Dicionário indexado por tupla contendo:

            - data do log;
            - identificador da classificação da dieta;
            - identificador da faixa etária.

            O valor armazenado representa a quantidade total registrada
            para a combinação informada.
    """
    logs = (
        escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
            data__range=[
                inicio_recreio,
                fim_recreio,
            ]
        )
        .values_list("data", "classificacao_id", "quantidade", "faixa_etaria")
        .distinct()
        .order_by(
            "data",
            "classificacao_id",
        )
    )

    logs_indexados = defaultdict(int)

    for data_log, classificacao_id, quantidade, faixa_etaria in logs:
        logs_indexados[(data_log, classificacao_id, faixa_etaria)] += quantidade

    return logs_indexados


def validate_lancamento_dietas_cei(
    dia: str,
    categoria: CategoriaMedicao,
    classificacoes: list[ClassificacaoDieta],
    valores_medicao: dict,
    mes: str,
    ano: str,
    logs_indexados: dict,
    faixa_etaria: FaixaEtaria,
) -> bool:
    """Valida os lançamentos de dietas para um dia e faixa etária específicos.

    Verifica se existem dietas autorizadas registradas nos logs para a
    categoria, dia e faixa etária informados e valida se existe lançamento
    correspondente na medição.

    A validação considera:
        - classificações vinculadas à categoria;
        - quantidade total registrada nos logs;
        - faixa etária do lançamento;
        - valores lançados na medição.

    Args:
        dia (str): Dia validado no formato ``DD``.

        categoria (CategoriaMedicao): Categoria de medição da dieta.

        classificacoes (list[ClassificacaoDieta]): Lista de classificações
            vinculadas à categoria.

        valores_medicao (dict): Estrutura indexada contendo os valores
            lançados na medição.

        mes (str): Mês de referência da validação.

        ano (str): Ano de referência da validação.

        logs_indexados (dict): Estrutura indexada contendo os logs de
            dietas autorizadas agrupados por data, classificação e faixa
            etária.

        faixa_etaria (FaixaEtaria): Faixa etária utilizada na validação.

    Returns:
        bool: ``True`` quando existe lançamento pendente.

            ``False`` quando todos os lançamentos obrigatórios estão
            preenchidos ou não existem dietas autorizadas para o dia e
            faixa etária informados.
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
                faixa_etaria.id,
            ),
            0,
        )
        for classificacao_id in classificacoes_ids
    )

    if quantidade_total == 0:
        return False

    valor_existe = ("frequencia", categoria.id, dia, faixa_etaria.id) in valores_medicao

    if not valor_existe:
        return True

    return False


def get_classificacoes_dietas_cei(
    categoria: CategoriaMedicao,
) -> list[ClassificacaoDieta]:
    """Retorna as classificações de dietas vinculadas à categoria informada.

    Para categorias do tipo ``Tipo A``, retorna todas as classificações cujo
    nome contenha ``"Tipo A"``.

    Para as demais categorias, utiliza o termo extraído do nome da categoria
    para localizar as classificações correspondentes.

    Args:
        categoria (CategoriaMedicao): Categoria de medição utilizada na
            busca das classificações.

    Returns:
        list[ClassificacaoDieta]: Lista de classificações de dietas
            associadas à categoria informada.
    """

    termo = (
        "Tipo A"
        if categoria.nome == CATEGORIA_DIETA_TIPO_A
        else categoria.nome.split(" - ")[1]
    )

    return ClassificacaoDieta.objects.filter(nome__icontains=termo)
