import datetime

from sme_sigpae_api.dados_comuns.utils import filtrar_dias_letivos


def gerar_dias_letivos_recreio(
    inicio_recreio: datetime.date, fim_recreio: datetime.date
) -> list[int]:
    """
    Gera a lista de dias letivos (números do dia no mês) dentro do período
    de recreio informado.

    O período é percorrido dia a dia e, ao final, os dias são filtrados
    pela regra de dias letivos do mês/ano correspondente.

    Args:
        inicio_recreio (datetime.date):  Data inicial do período de recreio (inclusive).
        fim_recreio (datetime.date):  Data final do período de recreio (inclusive).

    Returns:
        list[int]: Lista de dias do mês que são considerados letivos dentro do período informado.
    """
    if inicio_recreio.month != fim_recreio.month:
        raise ValueError("O início e o fim do recreio devem estar no mesmo mês.")
    dias_periodo = []
    data_atual = inicio_recreio
    while data_atual <= fim_recreio:
        dias_periodo.append(data_atual.day)
        data_atual += datetime.timedelta(days=1)
    mes = inicio_recreio.month
    ano = inicio_recreio.year
    return filtrar_dias_letivos(dias_periodo, mes, ano)


def gerar_calendario_recreio(
    inicio_recreio: datetime.date,
    fim_recreio: datetime.date,
    dias_letivos_filtrados: list[int],
) -> list[dict]:
    """
    Gera um calendário detalhado do período de recreio, indicando
    para cada data se é dia letivo ou não.

    Args:
        inicio_recreio (datetime.date):  Data inicial do período de recreio (inclusive).
        fim_recreio (datetime.date): Data final do período de recreio (inclusive).
        dias_letivos_filtrados (list[int]): Lista de dias do mês que são considerados letivos.

    Returns:
        list[dict]: Lista de dicionários com as chaves:
            - "dia": dia do mês com dois dígitos.
            - "data": data no formato DD/MM/AAAA.
            - "dia_letivo": True se o dia for letivo, False caso contrário.
    """
    dias_letivos_set = set(dias_letivos_filtrados)
    calendario = []
    data_atual = inicio_recreio
    while data_atual <= fim_recreio:
        dia_numero = data_atual.day
        dia_letivo = dia_numero in dias_letivos_set
        calendario.append(
            {
                "dia": f"{dia_numero:02d}",
                "data": data_atual.strftime("%d/%m/%Y"),
                "dia_letivo": dia_letivo,
            }
        )
        data_atual += datetime.timedelta(days=1)
    return calendario
