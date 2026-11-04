import datetime

from src.dados_comuns.utils import get_ultimo_dia_mes

from .models import EscolaAbertaUnidadeParticipante


def _possui_dia_no_mes(cadastro, primeiro_dia_mes, ultimo_dia_mes):
    data_inicial = max(cadastro.data_inicial, primeiro_dia_mes)
    data_final = min(cadastro.data_final, ultimo_dia_mes)
    dias_semana = {int(dia) for dia in cadastro.dias_semana}

    dia = data_inicial
    while dia <= data_final:
        if dia.weekday() in dias_semana:
            return True
        dia += datetime.timedelta(days=1)

    return False


def obter_unidade_escola_aberta_por_mes_ano(escola_uuid, mes, ano):
    primeiro_dia_mes = datetime.date(ano, mes, 1)
    ultimo_dia_mes = get_ultimo_dia_mes(primeiro_dia_mes)

    unidades = (
        EscolaAbertaUnidadeParticipante.objects.filter(
            unidade_educacional__uuid=escola_uuid,
            escola_aberta__data_inicial__lte=ultimo_dia_mes,
            escola_aberta__data_final__gte=primeiro_dia_mes,
        )
        .select_related("escola_aberta")
        .prefetch_related("tipos_alimentacao")
        .order_by("-escola_aberta__alterado_em", "-escola_aberta__criado_em")
    )

    for unidade in unidades:
        if _possui_dia_no_mes(unidade.escola_aberta, primeiro_dia_mes, ultimo_dia_mes):
            return unidade

    return None
