from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.http import QueryDict

from src.dados_comuns.constants import FORMATO_DATA_BRASILEIRO
from src.escola.models import Escola
from src.medicao_inicial.models import Medicao, ValorMedicao

ORDEM_PERIODOS = {
    "MANHA": 1,
    "TARDE": 2,
    "INTEGRAL": 3,
    "NOITE": 4,
    "INTERMEDIARIO": 5,
    "VESPERTINO": 6,
}

ORDEM_ALIMENTACOES = {
    "LANCHE": 1,
    "REFEIÇÃO": 2,
    "SOBREMESA": 3,
    "LANCHE 4H": 4,
}


def _obtem_medicoes(mes: str, ano: str, filtros: dict) -> QuerySet:
    """
    Obtém um QuerySet de medições filtradas por mês, ano e filtros adicionais.
    Recupera medições aprovadas pela CODAE para o período especificado, excluindo unidades
    de educação infantil e aplicando filtros adicionais quando fornecidos.

    Args:
        mes (str): mês de referência para a filtragem (formato: 'MM')
        ano (str): ano de referência para a filtragem (formato: 'AAAA')
        filtros (dict): Dicionário contendo filtros adicionais para aplicar na consulta.

    Returns:
        QuerySet: Conjunto de resultados contendo objetos Medicao
    """
    return (
        Medicao.objects.select_related("periodo_escolar", "grupo")
        .filter(
            solicitacao_medicao_inicial__mes=mes,
            solicitacao_medicao_inicial__ano=ano,
            solicitacao_medicao_inicial__status="MEDICAO_APROVADA_PELA_CODAE",
            **filtros,
        )
        .exclude(
            solicitacao_medicao_inicial__escola__tipo_unidade__iniciais__in=[
                "CEI",
                "CEI DIRET",
                "CEI INDIR",
                "CEI CEU",
                "CCI",
                "CCI/CIPS",
                "CEU CEI",
                "CEU CEMEI",
                "CEMEI",
            ]
        )
    )


def _obtem_valores_medicao(
    medicao: Medicao,
    tipos_alimentacao: list[str],
    dia_inicial: str | None,
    dia_final: str | None,
) -> QuerySet:
    """
    Obtém os valores de medição filtrados por critérios específicos.
    Recupera um QuerySet de valores de medição associados a uma medição principal,
    aplicando filtros por período e tipos de alimentação quando fornecidos, e
    excluindo automaticamente registros de dieta especial.

    Args:
        medicao (Medicao): Instância do modelo Medicao para a qual se buscam os valores
        tipos_alimentacao (list[str]): Lista de UUIDs de tipos de alimentação para filtrar. Se vazia, não aplica filtro por tipo.
        dia_inicial (str | None): Dia inicial do período no formato 'DD' (opcional)
        dia_final (str | None): Dia final do período no formato 'DD' (opcional)

    Returns:
        QuerySet:  QuerySet de valores de medição.
    """
    queryset = ValorMedicao.objects.select_related("tipo_alimentacao").filter(
        medicao=medicao
    )

    if dia_inicial and dia_final:
        queryset = queryset.filter(dia__gte=dia_inicial, dia__lte=dia_final)

    if tipos_alimentacao:
        queryset = queryset.filter(
            tipo_alimentacao__uuid__in=tipos_alimentacao
        ) | queryset.filter(nome_campo="frequencia")

    return queryset.exclude(categoria_medicao__nome__icontains="DIETA")


def _soma_total_servido_do_tipo_de_alimentacao(
    resultados: dict, medicao_nome: str, valor_medicao: ValorMedicao
) -> dict:
    """
    Acumula os valores totais servidos por tipo de alimentação em uma estrutura de resultados.
    Esta função atualiza um dicionário de resultados com os valores de medição,
    somando as quantidades servidas para cada tipo de alimentação encontrado

    Args:
        resultados (dict):  dicionário acumulador
        medicao_nome (str): nome da medição no dicionário de resultados
        valor_medicao (ValorMedicao): objeto ValorMedicao contendo os dados a serem somados.

    Returns:
        dict: o dicionário de resultados atualizado com os novos valores acumulados.
    """
    tipo_alimentacao = valor_medicao.tipo_alimentacao

    if tipo_alimentacao is not None:
        tipo_alimentacao_nome = tipo_alimentacao.nome.upper()
        if resultados[medicao_nome].get(tipo_alimentacao_nome) is None:
            resultados[medicao_nome][tipo_alimentacao_nome] = {
                "total_servido": 0,
                "total_frequencia": 0,
                "total_adesao": 0,
            }

        resultados[medicao_nome][tipo_alimentacao_nome]["total_servido"] += int(
            valor_medicao.valor
        )

    return resultados


def _atualiza_total_frequencia_e_adesao_para_cada_tipo_de_alimentacao(
    resultados: dict, medicao_nome: str, total_frequencia: int
) -> dict:
    """
    Atualiza os totais de frequência e adesão para todos os tipos de alimentação de uma medição.
    Para cada tipo de alimentação registrado nos resultados, esta função:
    1. Atualiza o valor total de frequência com o valor fornecido
    2. Calcula a taxa de adesão (total servido / frequência)
    3. Trata casos de divisão por zero (frequência = 0)

    Args:
        resultados (dict): dicionário contendo os resultados acumulados
        medicao_nome (str): nome da medição a ser atualizada nos resultados
        total_frequencia (int): Valor total de frequência a ser atribuído a todos os tipos de
        alimentação desta medição.

    Returns:
        dict: O mesmo dicionário de resultados com os valores de frequência e adesão atualizados
        para todos os tipos de alimentação da medição especificada.
    """
    for tipo_alimentacao in resultados[medicao_nome].keys():
        tipo_alimentacao_totais = resultados[medicao_nome][tipo_alimentacao]
        tipo_alimentacao_totais["total_frequencia"] = total_frequencia
        try:
            tipo_alimentacao_totais["total_adesao"] = round(
                tipo_alimentacao_totais["total_servido"] / total_frequencia,
                4,
            )
        except ZeroDivisionError:
            tipo_alimentacao_totais["total_adesao"] = 0

    return resultados


def _soma_totais_por_medicao(
    resultados: dict,
    total_frequencia_por_medicao: dict,
    medicao: Medicao,
    tipos_alimentacao: list[str],
    dia_inicial: str | None,
    dia_final: str | None,
) -> dict:
    """
    Calcula e acumula totais de frequência e valores servidos por tipo de alimentação para uma medição.
    Processa os valores de uma medição específica, atualizando:
    - O total de frequência para a medição
    - Os valores servidos por tipo de alimentação
    - As taxas de adesão calculadas

    Args:
        resultados (dict): Dicionário acumulador
        total_frequencia_por_medicao (dict): Dicionário acumulador de frequências por medição
        medicao (Medicao): Objeto Medicao contendo os dados da medição a ser processada
        tipos_alimentacao (list[str]): Lista de UUIDs de tipos de alimentação para filtrar
        dia_inicial (str | None): Dia inicial do período no formato 'DD' (opcional)
        dia_final (str | None): Dia final do período no formato 'DD' (opcional)

    Returns:
        dict: Dicionário de resultados atualizado com os valores processados para a medição.
    """
    medicao_nome = medicao.nome_periodo_grupo.upper()

    if resultados.get(medicao_nome) is None:
        resultados[medicao_nome] = {}
        total_frequencia_por_medicao[medicao_nome] = 0

    valores_medicao = _obtem_valores_medicao(
        medicao, tipos_alimentacao, dia_inicial, dia_final
    )
    for valor_medicao in valores_medicao:
        if valor_medicao.nome_campo == "frequencia":
            total_frequencia_por_medicao[medicao_nome] += int(valor_medicao.valor)
        else:
            resultados = _soma_total_servido_do_tipo_de_alimentacao(
                resultados, medicao_nome, valor_medicao
            )

    if not resultados[medicao_nome]:
        del resultados[medicao_nome]
    else:
        resultados = _atualiza_total_frequencia_e_adesao_para_cada_tipo_de_alimentacao(
            resultados, medicao_nome, total_frequencia_por_medicao[medicao_nome]
        )

    return resultados


def _aplica_filtro_lista(
    query_params: QueryDict, filtros: dict, parametro: str, chave_filtro: str
) -> dict:
    """
    Aplica um filtro de lista de parâmetros ao dicionário de filtros, quando houver valores.

    Args:
        query_params (QueryDict): objeto QueryDict contendo os parâmetros da requisição HTTP.
        filtros (dict): dicionário de filtros a ser atualizado.
        parametro (str): nome do parâmetro a ser lido do query_params.
        chave_filtro (str): chave do filtro a ser adicionada ao dicionário.

    Returns:
        dict: dicionário de filtros atualizado.
    """
    valores = query_params.getlist(parametro)
    if valores:
        filtros[chave_filtro] = valores
    return filtros


def _cria_filtros(query_params: QueryDict) -> dict:
    """
    Cria um dicionário de filtros para consulta de medições a partir de parâmetros de URL.
    Converte os parâmetros recebidos na requisição em filtros compatíveis com o ORM do Django,
    mapeando os nomes dos parâmetros para os campos correspondentes nos modelos.

    Args:
        query_params (QueryDict): objeto QueryDict contendo os parâmetros da requisição HTTP.

    Returns:
        dict: dicionário contendo os filtros formatados para uso em querysets Django
    """
    filtros = {}

    dre = query_params.get("diretoria_regional")
    if dre:
        filtros["solicitacao_medicao_inicial__escola__diretoria_regional__uuid"] = dre

    filtros = _aplica_filtro_lista(
        query_params,
        filtros,
        "lotes[]",
        "solicitacao_medicao_inicial__escola__lote__uuid__in",
    )
    filtros = _aplica_filtro_lista(
        query_params,
        filtros,
        "tipos_unidades[]",
        "solicitacao_medicao_inicial__escola__tipo_unidade__uuid__in",
    )
    filtros = _aplica_filtro_lista(
        query_params,
        filtros,
        "escola__uuid[]",
        "solicitacao_medicao_inicial__escola__uuid__in",
    )

    escola = query_params.get("escola")
    if escola:
        escola = escola.split("-")[0].strip()
        filtros["solicitacao_medicao_inicial__escola__codigo_eol"] = escola

    filtros = _aplica_filtro_lista(
        query_params, filtros, "periodos_escolares[]", "periodo_escolar__uuid__in"
    )

    return filtros


def _parametros_consulta(
    query_params: QueryDict,
) -> tuple[str, str, str | None, str | None, list[str]]:
    """
    Extrai e normaliza os parâmetros comuns de consulta do relatório de adesão.

    Args:
        query_params (QueryDict): objeto QueryDict contendo os parâmetros da requisição HTTP.

    Returns:
        tuple: contendo (mes, ano, dia_inicial, dia_final, tipos_alimentacao)
    """
    mes_ano = query_params.get("mes_ano")
    mes, ano = mes_ano.split("_")
    periodo_lancamento_de = query_params.get("periodo_lancamento_de")
    periodo_lancamento_ate = query_params.get("periodo_lancamento_ate")

    dia_inicial = None
    dia_final = None
    if periodo_lancamento_de and periodo_lancamento_ate:
        dia_inicial = periodo_lancamento_de.split("/")[0]
        dia_final = periodo_lancamento_ate.split("/")[0]

    tipos_alimentacao = query_params.getlist("tipos_alimentacao[]")

    return mes, ano, dia_inicial, dia_final, tipos_alimentacao


def _ordena_resultados(resultados: dict) -> dict:
    """
    Ordena de forma determinística os períodos e as alimentações do resultado.

    A ordem dos períodos é: Manhã, Tarde, Integral, Noite, Intermediário, Vespertino.
    A ordem das alimentações é: Lanche, Refeição, Sobremesa, Lanche 4h.
    Períodos ou alimentações desconhecidos são mantidos por último, na ordem em que aparecem.

    Args:
        resultados (dict): dicionário com os resultados consolidados.

    Returns:
        dict: dicionário com os períodos e alimentações ordenados.
    """

    def _chave_periodo(medicao_nome: str) -> int:
        periodo = medicao_nome.split(" - ")[-1].strip()
        return ORDEM_PERIODOS.get(periodo, len(ORDEM_PERIODOS) + 1)

    def _chave_alimentacao(alimentacao_nome: str) -> int:
        return ORDEM_ALIMENTACOES.get(alimentacao_nome, len(ORDEM_ALIMENTACOES) + 1)

    return {
        medicao_nome: dict(
            sorted(
                alimentacoes.items(),
                key=lambda item: _chave_alimentacao(item[0]),
            )
        )
        for medicao_nome, alimentacoes in sorted(
            resultados.items(), key=lambda item: _chave_periodo(item[0])
        )
    }


def _calcula_resultados(
    mes: str,
    ano: str,
    filtros: dict,
    tipos_alimentacao: list[str],
    dia_inicial: str | None,
    dia_final: str | None,
) -> dict:
    """
    Calcula e consolida os resultados de medições a partir de um conjunto de filtros.

    Args:
        mes (str): mês de referência no formato 'MM'
        ano (str): ano de referência no formato 'AAAA'
        filtros (dict): filtros a serem aplicados na consulta de medições
        tipos_alimentacao (list[str]): lista de UUIDs de tipos de alimentação
        dia_inicial (str | None): dia inicial do período de lançamento
        dia_final (str | None): dia final do período de lançamento

    Returns:
        dict: dicionário consolidado com os resultados
    """
    resultados = {}
    total_frequencia_por_medicao = {}

    medicoes = _obtem_medicoes(mes, ano, filtros)
    for medicao in medicoes:
        resultados = _soma_totais_por_medicao(
            resultados,
            total_frequencia_por_medicao,
            medicao,
            tipos_alimentacao,
            dia_inicial,
            dia_final,
        )

    return _ordena_resultados(resultados)


def obtem_resultados(query_params: QueryDict) -> dict:
    """
    Obtém e consolida resultados de medições de alimentação escolar com base em parâmetros de filtro.
    Processa os parâmetros de consulta, aplica os filtros correspondentes e calcula os totais de:
    - Frequência por medição
    - Quantidades servidas por tipo de alimentação
    - Taxas de adesão (servido/frequência)

    Args:
        query_params (QueryDict): QueryDict contendo os parâmetros da requisição

    Returns:
        dict: dicionário consolidado com os resultados
    """
    mes, ano, dia_inicial, dia_final, tipos_alimentacao = _parametros_consulta(
        query_params
    )

    filtros = _cria_filtros(query_params)
    return _calcula_resultados(
        mes, ano, filtros, tipos_alimentacao, dia_inicial, dia_final
    )


def obtem_escolas_ordenadas(escolas_uuid: list[str]) -> list[Escola]:
    """
    Retorna as escolas filtradas pelos UUIDs, ordenadas alfabeticamente pelo nome.

    Args:
        escolas_uuid (list[str]): lista de UUIDs de escolas.

    Returns:
        list[Escola]: escolas encontradas, ordenadas por nome.
    """
    return list(
        Escola.objects.filter(uuid__in=escolas_uuid)
        .only("uuid", "nome", "codigo_eol")
        .order_by("nome")
    )


def obtem_resultados_para_escola(escola: Escola, query_params: QueryDict) -> dict:
    """
    Calcula os resultados consolidados de medições para uma única escola.

    Args:
        escola (Escola): escola para a qual os resultados serão calculados.
        query_params (QueryDict): parâmetros da requisição.

    Returns:
        dict: dicionário com a identificação da escola e seus resultados.
    """
    mes, ano, dia_inicial, dia_final, tipos_alimentacao = _parametros_consulta(
        query_params
    )

    filtros = _cria_filtros(query_params)
    filtros["solicitacao_medicao_inicial__escola__uuid"] = escola.uuid
    resultados = _calcula_resultados(
        mes, ano, filtros, tipos_alimentacao, dia_inicial, dia_final
    )

    return {
        "escola": {
            "nome": escola.nome,
            "codigo_eol": escola.codigo_eol,
        },
        "resultados": resultados,
    }


def obtem_resultados_por_escola(query_params: QueryDict) -> list[dict]:
    """
    Obtém e consolida resultados de medições de alimentação escolar agrupados por escola.

    Para cada escola informada no filtro ``escola__uuid[]``, calcula os resultados
    agregados da medição e os retorna junto com a identificação da escola
    (nome e código EOL), permitindo que o resultado seja paginado com uma escola
    por página.

    Args:
        query_params (QueryDict): QueryDict contendo os parâmetros da requisição

    Returns:
        list[dict]: lista de dicionários no formato
        ``{"escola": {"nome": str, "codigo_eol": str}, "resultados": dict}``
    """
    escolas_uuid = query_params.getlist("escola__uuid[]")
    return [
        obtem_resultados_para_escola(escola, query_params)
        for escola in obtem_escolas_ordenadas(escolas_uuid)
    ]


def _valida_ano_mes(mes_ano: str) -> tuple[int, int]:
    """
    Valida e extrai mês e ano de uma string no formato 'MM_AAAA'

    Args:
        mes_ano (str): string contendo mês e ano no formato 'MM_AAAA'.

    Raises:
        ValidationError: Se o parâmetro estiver vazio ou no formato incorreto.

    Returns:
        tuple: tupla contendo (mes_referencia, ano_referencia) como inteiros
    """
    if not mes_ano:
        raise ValidationError("É necessário informar o mês/ano de referência")
    try:
        mes_referencia, ano_referencia = map(int, mes_ano.split("_"))
    except ValueError:
        raise ValidationError("mes_ano deve estar no formato MM_AAAA")

    return mes_referencia, ano_referencia


def valida_parametros_periodo_lancamento(query_params: QueryDict) -> None:
    """
    Valida parâmetros de período de lançamento em uma consulta.
    Realiza validações completas dos parâmetros relacionados a períodos de lançamento,
    incluindo consistência entre datas e mês/ano de referência.

    Args:
        query_params (QueryDict): Dicionário de parâmetros da requisição HTTP.

    Raises:
        ValidationError: Se qualquer validação falhar, com mensagem específica:
            - Parâmetros de período ausentes/inconsistentes
            - Datas em formato inválido
            - Datas fora do mês/ano de referência
            - Data inicial posterior à data final
    """

    mes_ano = query_params.get("mes_ano")
    periodo_lancamento_de = query_params.get("periodo_lancamento_de")
    periodo_lancamento_ate = query_params.get("periodo_lancamento_ate")

    mes_referencia, ano_referencia = _valida_ano_mes(mes_ano)

    if (periodo_lancamento_de and not periodo_lancamento_ate) or (
        periodo_lancamento_ate and not periodo_lancamento_de
    ):
        raise ValidationError(
            "Ambos 'periodo_lancamento_de' e 'periodo_lancamento_ate' devem ser informados juntos"
        )

    if periodo_lancamento_de and periodo_lancamento_ate:

        data_de = _parse_data(periodo_lancamento_de, "periodo_lancamento_de")
        data_ate = _parse_data(periodo_lancamento_ate, "periodo_lancamento_ate")

        if data_de > data_ate:
            raise ValidationError(
                "'periodo_lancamento_de' deve ser anterior a 'periodo_lancamento_ate'"
            )

        _validar_mes_ano_data(
            data_de, mes_referencia, ano_referencia, "periodo_lancamento_de"
        )
        _validar_mes_ano_data(
            data_ate, mes_referencia, ano_referencia, "periodo_lancamento_ate"
        )


def _parse_data(valor: str, campo: str) -> datetime:
    """
    Converte string de data no formato 'dd/mm/yyyy' para objeto date

    Args:
        valor (str): string contendo a data.
        campo (str): nome do campo para mensagens de erro.

    Raises:
        ValidationError: se o formato da data for inválido.

    Returns:
        datetime:  objeto date convertido.
    """
    try:
        return datetime.strptime(valor, FORMATO_DATA_BRASILEIRO).date()
    except ValueError:
        raise ValidationError(
            f"Formato de data inválido para '{campo}'. Use o formato dd/mm/yyyy"
        )


def _validar_mes_ano_data(data: datetime, mes: int, ano: int, campo: str) -> None:
    """
    Valida se uma data pertence ao mês e ano especificados.

    Args:
        data (datetime): data a ser validada
        mes (int): mês de referência esperado.
        ano (int): ano de referência esperado.
        campo (str): nome do campo para mensagens de erro.

    Raises:
        ValidationError: se o mês/ano da data não corresponder ao esperado.
    """
    if (data.month, data.year) != (mes, ano):
        raise ValidationError(
            f"O mês/ano de '{campo}' ({data.month:02}/{data.year}) não coincide com 'mes_ano' ({mes:02}_{ano})."
        )
