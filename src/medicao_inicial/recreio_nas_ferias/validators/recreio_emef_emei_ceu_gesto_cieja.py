import datetime
from collections import defaultdict
from datetime import timedelta

from django.db.models import QuerySet

from src.dieta_especial.solicitacao_dieta_especial.models import ClassificacaoDieta
from src.escola.models import Escola
from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,
    Medicao,
    SolicitacaoMedicaoInicial,
    ValorMedicao,
)
from src.medicao_inicial.recreio_nas_ferias.models import RecreioNasFerias
from src.medicao_inicial.recreio_nas_ferias.utils import gerar_dias_letivos_recreio
from src.medicao_inicial.utils import get_name_campo
from src.medicao_inicial.validators import (
    erros_unicos,
    get_classificacoes_dietas,
    lista_erros_com_periodo,
)

CATEGORIA_ALIMENTACAO_NOME = "ALIMENTAÇÃO"
CATEGORIA_DIETA_TIPO_A_ENTERAL_RESTRICAO_NOME = (
    "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
)


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
    participantes = recreio.unidades_participantes.first()

    informacoes_participantes = {
        "Recreio nas Férias": participantes.num_inscritos,
        "Colaboradores": participantes.num_colaboradores,
    }
    grupos = [
        grupo
        for grupo, quantidade in informacoes_participantes.items()
        if quantidade > 0
    ]

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
    logs_por_dia = indexar_logs_dieta_autorizadas_por_data(logs_do_recreio)

    grupo = "Recreio nas Férias"
    categorias = list(CategoriaMedicao.objects.filter(nome__icontains="dieta"))
    tipos_alimentacao = get_tipos_alimentacao_recreio(recreio)
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
    participantes = recreio.unidades_participantes.first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome__in=["Inscritos", "Colaboradores"]
    )
    tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)
    informacoes_alimentacao = {
        "Recreio nas Férias": tipos_alimentacao_map.get("Inscritos", [])
    }
    if participantes.num_colaboradores > 0:
        informacoes_alimentacao["Colaboradores"] = tipos_alimentacao_map.get(
            "Colaboradores", []
        )

    grupos = list(informacoes_alimentacao.keys())

    categoria_medicao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    dias_letivos_geral = gerar_dias_letivos_recreio(
        recreio.data_inicio, recreio.data_fim
    )
    dias_letivos_geral_formatado = [f"{dia:02d}" for dia in dias_letivos_geral]

    for grupo in grupos:
        linhas_da_tabela = get_linhas_da_tabela_alimentacoes_recreio(
            informacoes_alimentacao[grupo]
        )
        lista_erros = buscar_valores_lancamento_alimentacoes_recreio(
            linhas_da_tabela,
            solicitacao,
            grupo,
            dias_letivos_geral_formatado,
            categoria_medicao,
            lista_erros,
        )
    return erros_unicos(lista_erros)


def agrupar_tipos_alimentacao_por_categoria(
    tipos_alimentacao: QuerySet,
) -> dict[str, list]:
    """Agrupa tipos de alimentação por categoria.

    Args:
        tipos_alimentacao (QuerySet):
            Queryset contendo os tipos de alimentação.

    Returns:
        dict[str, list]: Dicionário com os tipos de alimentação agrupados
            pelo nome da categoria.
    """
    agrupados = defaultdict(list)

    for tipo in tipos_alimentacao.select_related(
        "categoria",
        "tipo_alimentacao",
    ):
        agrupados[tipo.categoria.nome].append(tipo.tipo_alimentacao.nome)

    return dict(agrupados)


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

    tipos_alimentacao = get_tipos_alimentacao_recreio(recreio)
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


def get_tipos_alimentacao_recreio(
    recreio: RecreioNasFerias,
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
    participantes = recreio.unidades_participantes.first()

    tipos_alimentacao = participantes.tipos_alimentacao.filter(
        categoria__nome="Inscritos",
    )

    return agrupar_tipos_alimentacao_por_categoria(
        tipos_alimentacao,
    ).get("Inscritos", [])


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
