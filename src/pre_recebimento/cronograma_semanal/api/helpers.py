"""Helpers da API do submódulo de cronograma semanal."""

import calendar
import datetime

from django.db.models import Q

FORMATOS_DE_MES_ACEITOS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%Y")


def _parse_ano_mes(valor):
    """Extrai (ano, mês) do valor informado. ``None`` se inválido.

    O filtro é por mês, então só o mês e o ano do valor importam: o dia,
    quando presente, é descartado. São aceitos ``AAAA-MM-DD`` (formato
    enviado pelo front), ``DD/MM/AAAA`` e ``MM/AAAA``.
    """
    if not valor:
        return None

    for formato in FORMATOS_DE_MES_ACEITOS:
        try:
            data = datetime.datetime.strptime(str(valor).strip(), formato)
        except (ValueError, TypeError):
            continue
        return data.year, data.month

    return None


def primeiro_dia_do_mes(valor):
    """Primeiro dia do mês informado (``None`` se inválido)."""
    ano_mes = _parse_ano_mes(valor)
    if ano_mes is None:
        return None
    ano, mes = ano_mes
    return datetime.date(ano, mes, 1)


def ultimo_dia_do_mes(valor):
    """Último dia do mês informado (``None`` se inválido)."""
    ano_mes = _parse_ano_mes(valor)
    if ano_mes is None:
        return None
    ano, mes = ano_mes
    return datetime.date(ano, mes, calendar.monthrange(ano, mes)[1])


def periodo_de_entrega(query_params):
    """Extrai o período de entrega (``mes_inicial``/``mes_final``) dos
    query params, expandido para o primeiro e o último dia dos meses.

    Retorna ``(None, None)`` quando nenhum mês válido é informado.
    """
    return (
        primeiro_dia_do_mes(query_params.get("mes_inicial")),
        ultimo_dia_do_mes(query_params.get("mes_final")),
    )


def q_programacao_no_periodo(data_inicial, data_final):
    """``Q`` das programações com ao menos uma das datas dentro do período.

    Uma programação entra no recorte quando ``data_inicio`` **ou**
    ``data_fim`` cai dentro dos meses selecionados. Um período aberto de um
    dos lados considera apenas o limite informado.
    """
    inicio_no_periodo = Q()
    fim_no_periodo = Q()

    if data_inicial:
        inicio_no_periodo &= Q(data_inicio__gte=data_inicial)
        fim_no_periodo &= Q(data_fim__gte=data_inicial)
    if data_final:
        inicio_no_periodo &= Q(data_inicio__lte=data_final)
        fim_no_periodo &= Q(data_fim__lte=data_final)

    return inicio_no_periodo | fim_no_periodo
