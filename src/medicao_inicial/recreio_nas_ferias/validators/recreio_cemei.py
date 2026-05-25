from src.cardapio.base.models import TipoAlimentacao
from src.medicao_inicial.models import (
    CategoriaMedicao,
    SolicitacaoMedicaoInicial,
)
from src.medicao_inicial.recreio_nas_ferias.models import (
    RecreioNasFeriasUnidadeParticipante,
)
from src.medicao_inicial.recreio_nas_ferias.utils import gerar_dias_letivos_recreio
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_cei_cci_cips import (
    buscar_valores_lancamento_alimentacoes_faixa_etaria,
    cria_valores_medicao_dietas_autorizadas_do_recreio_cei,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_common import (
    agrupar_tipos_alimentacao_por_categoria,
    get_classificacoes_dietas_recreio,
    valida_campo_participantes,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    cria_valores_medicao_dietas_autorizadas_do_recreio,
    get_linhas_da_tabela_dieta_recreio,
    get_logs_indexados_recreio,
    get_valores_medicao_set,
    validar_lancamentos_alimentacoes_recreio,
    validate_lancamento_dietas,
)
from src.medicao_inicial.validators import (
    erros_unicos,
    get_classificacoes_dietas,
    lista_erros_com_periodo,
)

GRUPO_CEI = "Recreio nas Férias - de 0 a 3 anos e 11 meses"
GRUPO_EMEI = "Recreio nas Férias - 4 a 14 anos"
GRUPO_COLABORADORES = "Colaboradores"


def cria_valores_medicao_participantes_cemei(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de participantes do Recreio nas Férias de unidades CEMEI.

    Cria registros de ``ValorMedicao`` para cada dia do período do recreio,
    considerando os grupos participantes disponíveis na unidade escolar.

    Os valores são criados apenas quando ainda não existem para o dia,
    categoria e grupo informados.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    recreio = instance.recreio_nas_ferias

    participantes = {
        participante.cei_ou_emei: participante
        for participante in recreio.unidades_participantes.filter(
            unidade_educacional=instance.escola
        )
    }
    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    informacoes_participantes = {}
    grupos = [
        (
            participantes_emei,
            GRUPO_EMEI,
        ),
        (
            participantes_cei,
            GRUPO_CEI,
        ),
    ]

    for participante, descricao in grupos:
        if participante and participante.num_inscritos > 0:
            informacoes_participantes[descricao] = participante.num_inscritos

    if existe_colaborador_cemei(participantes_cei, participantes_emei):
        total = sum(
            p.num_colaboradores
            for p in [participantes_cei, participantes_emei]
            if p is not None
        )
        informacoes_participantes[GRUPO_COLABORADORES] = total

    valida_campo_participantes(instance, informacoes_participantes)


def cria_valores_medicao_participantes_dietas_autorizadas_cemei(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    """Cria os valores de medição de dietas autorizadas do recreio CEMEI.

    Cria registros de ``ValorMedicao`` para dietas autorizadas durante o
    período do Recreio nas Férias, considerando separadamente os cenários
    EMEI e CEI da CEMEI.

    Para EMEI, os valores são gerados a partir dos logs de dietas autorizadas
    indexados por data e classificação, criando registros para cada
    combinação de categoria e dia ainda inexistente.

    Para CEI, os valores são gerados a partir dos logs de dietas autorizadas
    indexados por data, faixa etária e classificação, criando registros para
    cada combinação de categoria, dia e faixa etária ainda inexistente.

    Somente categorias que possuam logs compatíveis no período do recreio
    são consideradas para criação dos valores.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """

    escola = instance.escola
    recreio = instance.recreio_nas_ferias
    inicio_recreio = recreio.data_inicio
    fim_recreio = recreio.data_fim

    logs_do_recreio_emei = escola.logs_dietas_autorizadas_recreio_ferias.filter(
        data__range=[inicio_recreio, fim_recreio],
    )
    cria_valores_medicao_dietas_autorizadas_do_recreio(
        instance, logs_do_recreio_emei, GRUPO_EMEI
    )

    logs_do_recreio_cei = escola.logs_dietas_autorizadas_recreio_ferias_cei.filter(
        data__range=[inicio_recreio, fim_recreio],
        faixa_etaria__isnull=False,
    )

    cria_valores_medicao_dietas_autorizadas_do_recreio_cei(
        instance, logs_do_recreio_cei, GRUPO_CEI
    )


def existe_colaborador_cemei(
    participantes_cei: RecreioNasFeriasUnidadeParticipante,
    participantes_emei: RecreioNasFeriasUnidadeParticipante,
) -> bool:
    """ "Verifica se existem colaboradores ativos no CEMEI.

    Retorna ``True`` quando a soma dos colaboradores participantes dos
    recreios CEI (0 a 3 anos e 11 meses) e EMEI (4 a 14 anos) da unidade
    CEMEI for maior que zero e houver pelo menos um tipo de alimentação
    associado à categoria ``"Colaboradores"`` em qualquer um dos recreios.
    Caso contrário, retorna ``False``.

    Args:
        participantes_cei (RecreioNasFeriasUnidadeParticipante):  Instância participante dos inscritos no Recreio nas Férias – CEI (0 a 3 anos e 11 meses)
            da unidade CEMEI.
        participantes_emei (RecreioNasFeriasUnidadeParticipante): Instância participante dos inscritos no Recreio nas Férias – EMEI (4 a 14 anos)
            da unidade CEMEI

    Returns:
        bool:  ``True`` se houver colaboradores com alimentação configurada dos recreios CEI ou EMEI da unidade CEMEI; caso contrário, ``False``.
    """
    participantes = [
        p for p in [participantes_cei, participantes_emei] if p is not None
    ]

    total_colaboradores = sum(p.num_colaboradores for p in participantes)

    if total_colaboradores <= 0:
        return False

    tipos_alimentacao = None

    for participante in participantes:
        tipos = participante.tipos_alimentacao.filter(
            categoria__nome=GRUPO_COLABORADORES
        )

        tipos_alimentacao = (
            tipos if tipos_alimentacao is None else tipos_alimentacao | tipos
        )

    tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)

    return bool(
        tipos_alimentacao_map.get(
            GRUPO_COLABORADORES,
            [],
        )
    )


def validate_lancamento_alimentacoes_medicao_recreio_cemei(
    solicitacao: SolicitacaoMedicaoInicial, lista_erros: list
) -> list:
    """Valida os lançamentos das alimentações da medição do Recreio nas Férias para CEMEI.

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
    dias_letivos = [
        f"{dia:02d}"
        for dia in gerar_dias_letivos_recreio(recreio.data_inicio, recreio.data_fim)
    ]
    categoria_alimentacao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    participantes = dict()
    tipos_alimentacao = TipoAlimentacao.objects.none()
    informacoes_alimentacao = {}

    for participante in recreio.unidades_participantes.filter(
        unidade_educacional=solicitacao.escola
    ):
        alimentacoes = participante.tipos_alimentacao.filter(
            categoria__nome__in=["Infantil", "Inscritos", "Colaboradores"]
        )
        tipos_alimentacao = tipos_alimentacao | alimentacoes
        participantes[participante.cei_ou_emei] = participante

    tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)
    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    if existe_colaborador_cemei(participantes_cei, participantes_emei):
        informacoes_alimentacao[GRUPO_COLABORADORES] = tipos_alimentacao_map.get(
            "Colaboradores", []
        )
    if participantes_emei is not None and participantes_emei.num_inscritos > 0:
        informacoes_alimentacao[GRUPO_EMEI] = tipos_alimentacao_map.get("Infantil", [])

    if informacoes_alimentacao:
        informacoes = {
            "solicitacao": solicitacao,
            "grupos_recreio": informacoes_alimentacao,
            "dias_letivos": dias_letivos,
            "categoria_alimentacao": categoria_alimentacao,
        }
        lista_erros = validar_lancamentos_alimentacoes_recreio(informacoes, lista_erros)

    if participantes_cei is not None and participantes_cei.num_inscritos > 0:
        lista_erros = buscar_valores_lancamento_alimentacoes_faixa_etaria(
            solicitacao,
            GRUPO_CEI,
            dias_letivos,
            categoria_alimentacao,
            lista_erros,
        )

    return lista_erros


def validate_lancamento_dietas_medicao_recreio_cemei(
    solicitacao: SolicitacaoMedicaoInicial, lista_erros: list
) -> list:
    """Valida os lançamentos de dietas da medição referente ao período de recreio nas férias
    para unidades CEMEI, considerando apenas as alimentações da categoria Infantil (EMEI).

    A função obtém os dias letivos do recreio, recupera as alimentações disponíveis para
    a unidade participante e delega a validação das dietas para as medições do grupo EMEI.

    Args:
        solicitacao (SolicitacaoMedicaoInicial):  Solicitação de medição contendo os dados do
            recreio, escola e medições associadas.
        lista_erros (list): Lista acumulada de erros encontrados durante o processo de validação.

    Returns:
        list: Lista de erros atualizada após a validação dos lançamentos de dietas.
    """
    recreio = solicitacao.recreio_nas_ferias
    categorias = CategoriaMedicao.objects.filter(nome__icontains="dieta")
    dias_letivos = [
        f"{dia:02d}"
        for dia in gerar_dias_letivos_recreio(
            recreio.data_inicio,
            recreio.data_fim,
        )
    ]
    alimentacoes = buscar_alimentacoes_recreio_cemei(solicitacao)
    alimentacoes_emei = alimentacoes.get("Infantil", [])

    lista_erros = valida_dietas_emei_da_cemei(
        solicitacao, categorias, alimentacoes_emei, dias_letivos, lista_erros
    )

    return lista_erros


def buscar_alimentacoes_recreio_cemei(
    solicitacao: SolicitacaoMedicaoInicial,
) -> dict[str, list]:
    """Obtém e agrupa os tipos de alimentação configurados para o recreio nas férias
    da unidade CEMEI, considerando apenas as categorias Infantil, Inscritos e
    Colaboradores.

    A função percorre as unidades participantes do recreio vinculadas à escola da
    solicitação e retorna os tipos de alimentação agrupados por categoria.

    Args:
        solicitacao (SolicitacaoMedicaoInicial): Solicitação de medição contendo a escola
            e as informações do recreio.

    Returns:
        dict[str, list]:  Dicionário com os tipos de alimentação agrupados por categoria.
    """
    tipos_alimentacao = TipoAlimentacao.objects.none()
    for participante in solicitacao.recreio_nas_ferias.unidades_participantes.filter(
        unidade_educacional=solicitacao.escola
    ):
        alimentacoes = participante.tipos_alimentacao.filter(
            categoria__nome__in=["Infantil", "Inscritos", "Colaboradores"]
        )
        tipos_alimentacao = tipos_alimentacao | alimentacoes

    return agrupar_tipos_alimentacao_por_categoria(tipos_alimentacao)


def valida_dietas_emei_da_cemei(
    solicitacao: SolicitacaoMedicaoInicial,
    categorias: list[CategoriaMedicao],
    alimentacoes: list[str],
    dias_letivos: list[str],
    lista_erros: list,
) -> list:
    """Valida os lançamentos de dietas da medição do grupo EMEI da CEMEI para o recreio nas férias.

    A validação verifica, para cada categoria de dieta e para cada dia letivo do período,
    se existem lançamentos pendentes nas dietas esperadas conforme as alimentações
    disponíveis. Caso sejam encontrados dias sem lançamento, um erro é adicionado à lista.

    Args:
        solicitacao (SolicitacaoMedicaoInicial):  Solicitação de medição contendo as medições, escola e
            período do recreio.
        categorias (list[CategoriaMedicao]): Lista de categorias de medição relacionadas às dietas.
        alimentacoes (list[str]): Lista de alimentações disponíveis para validação.
        dias_letivos (list[str]): Lista dos dias letivos do período do recreio formatados para validação.
        lista_erros (list):  Lista acumulada de erros encontrados durante o processo.

    Returns:
        list: Lista de erros atualizada contendo eventuais pendências de lançamentos.
    """
    medicao_recreio_emei = solicitacao.medicoes.filter(grupo__nome=GRUPO_EMEI).first()
    valores_medicao = get_valores_medicao_set(
        medicao_recreio_emei,
        categorias,
    )
    logs_indexados = get_logs_indexados_recreio(
        solicitacao.escola,
        solicitacao.recreio_nas_ferias.data_inicio,
        solicitacao.recreio_nas_ferias.data_fim,
    )
    categorias_validas = get_classificacoes_dietas_recreio(categorias, alimentacoes)
    cache_classificacoes = {
        categoria.id: get_classificacoes_dietas(categoria)
        for categoria in categorias_validas
    }
    for categoria in categorias_validas:
        classificacoes = cache_classificacoes.get(categoria.id)
        nomes_campos = get_linhas_da_tabela_dieta_recreio(alimentacoes, categoria)
        for dia in dias_letivos:

            if lista_erros_com_periodo(lista_erros, medicao_recreio_emei, "dietas"):
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
                        "periodo_escolar": medicao_recreio_emei.grupo.nome,
                        "erro": "Restam dias a serem lançados nas dietas.",
                    }
                )
                return erros_unicos(
                    lista_erros,
                )

    return lista_erros
