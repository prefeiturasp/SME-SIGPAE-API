"""Utilitários de inclusão contínua e medição de Programas e Projetos.

Funções auxiliares para identificar períodos ativos no mês e remover a
medição de Programas e Projetos quando a inclusão contínua é encerrada e
não há outra quantidade ativa na instituição.
"""

import datetime

from django.db.models import Q

from src.dados_comuns.constants import GRUPO_PROGRAMAS_E_PROJETOS
from src.dados_comuns.utils import get_ultimo_dia_mes
from src.inclusao_alimentacao.models import QuantidadePorPeriodo


def quantidade_periodo_possui_dia_ativo_no_mes(
    quantidade_periodo, primeiro_dia_mes, ultimo_dia_mes
):
    """Indica se a quantidade por período ainda tem dia vigente no mês.

    A vigência considera o intervalo da inclusão contínua, o
    ``encerrado_a_partir_de`` (a própria data continua ativa) e os dias da
    semana da quantidade. Lista vazia de dias da semana equivale a todos os
    dias.

    Args:
        quantidade_periodo (QuantidadePorPeriodo): Quantidade por período da
            inclusão contínua.
        primeiro_dia_mes (datetime.date): Primeiro dia do mês avaliado.
        ultimo_dia_mes (datetime.date): Último dia do mês avaliado.

    Returns:
        bool: ``True`` se existir ao menos um dia ativo no mês.
    """
    inclusao = quantidade_periodo.inclusao_alimentacao_continua
    data_inicio = max(inclusao.data_inicial, primeiro_dia_mes)
    data_fim = min(inclusao.data_final, ultimo_dia_mes)
    if quantidade_periodo.encerrado_a_partir_de:
        data_fim = min(data_fim, quantidade_periodo.encerrado_a_partir_de)
    if data_inicio > data_fim:
        return False

    dias_semana = quantidade_periodo.dias_semana
    if not dias_semana:
        return True

    data = data_inicio
    while data <= data_fim:
        if data.weekday() in dias_semana:
            return True
        data += datetime.timedelta(days=1)
    return False


def medicao_programas_e_projetos_do_mes(escola, ano, mes):
    """Busca a medição de Programas e Projetos da escola no mês/ano.

    Há no máximo uma solicitação sem recreio nas férias por escola/mês/ano
    e no máximo uma medição do grupo Programas e Projetos nessa solicitação.
    Aceita mês com ou sem zero à esquerda.

    Args:
        escola (Escola): Escola da solicitação de medição inicial.
        ano (int): Ano da solicitação.
        mes (int): Mês da solicitação.

    Returns:
        Medicao: Medição do grupo Programas e Projetos, ou ``None`` se não
        existir.
    """
    from src.medicao_inicial.models import Medicao

    return Medicao.objects.filter(
        solicitacao_medicao_inicial__escola=escola,
        solicitacao_medicao_inicial__ano=str(ano),
        solicitacao_medicao_inicial__mes__in={f"{mes:02d}", str(mes)},
        solicitacao_medicao_inicial__recreio_nas_ferias__isnull=True,
        grupo__nome=GRUPO_PROGRAMAS_E_PROJETOS,
    ).first()


def escola_possui_outra_quantidade_ativa_no_mes(
    escola, primeiro_dia_mes, ultimo_dia_mes, uuids_excluir
):
    """Indica se a escola tem outra quantidade de inclusão contínua ativa no mês.

    Percorre as inclusões autorizadas da instituição, no mesmo critério de
    ``periodos_inclusao_continua_ativas``, excluindo as quantidades em
    ``uuids_excluir`` (as recém-encerradas). Respeita vigência e
    ``dias_semana``. Quantidades canceladas e motivo ETEC são ignoradas.

    Args:
        escola (Escola): Instituição da inclusão.
        primeiro_dia_mes (datetime.date): Primeiro dia do mês avaliado.
        ultimo_dia_mes (datetime.date): Último dia do mês avaliado.
        uuids_excluir: UUIDs das quantidades recém-encerradas.

    Returns:
        bool: ``True`` se existir outra quantidade com dia ativo no mês.
    """
    quantidades = (
        QuantidadePorPeriodo.objects.filter(
            inclusao_alimentacao_continua__status="CODAE_AUTORIZADO",
            inclusao_alimentacao_continua__rastro_escola=escola,
            inclusao_alimentacao_continua__data_inicial__lte=ultimo_dia_mes,
            cancelado=False,
        )
        .exclude(inclusao_alimentacao_continua__motivo__nome="ETEC")
        .exclude(uuid__in=uuids_excluir)
        .filter(
            Q(
                encerrado_a_partir_de__isnull=True,
                inclusao_alimentacao_continua__data_final__gte=primeiro_dia_mes,
            )
            | Q(encerrado_a_partir_de__gte=primeiro_dia_mes)
        )
        .select_related("inclusao_alimentacao_continua")
    )
    for quantidade_periodo in quantidades:
        if quantidade_periodo_possui_dia_ativo_no_mes(
            quantidade_periodo, primeiro_dia_mes, ultimo_dia_mes
        ):
            return True
    return False


def exclui_valores_inativos_mes_encerramento(medicao, inclusao, encerrado_a_partir_de):
    """Remove a medição de Programas e Projetos se ela ficar sem uso no mês.

    Se existir outra quantidade ativa na unidade no mês, a medição é mantida.
    Caso contrário, a medição é excluída.

    Args:
        medicao (Medicao): Medição de Programas e Projetos do mês do
            encerramento. Se ``None``, a função não faz nada.
        inclusao (InclusaoAlimentacaoContinua): Inclusão contínua encerrada.
        encerrado_a_partir_de (datetime.date): Data a partir da qual a
            inclusão foi encerrada.
    """
    if not medicao:
        return
    primeiro_dia_mes = datetime.date(
        encerrado_a_partir_de.year, encerrado_a_partir_de.month, 1
    )
    ultimo_dia_mes = get_ultimo_dia_mes(primeiro_dia_mes)
    uuids_encerrados = inclusao.quantidades_periodo.filter(
        encerrado_a_partir_de=encerrado_a_partir_de
    ).values_list("uuid", flat=True)
    if escola_possui_outra_quantidade_ativa_no_mes(
        inclusao.escola, primeiro_dia_mes, ultimo_dia_mes, uuids_encerrados
    ):
        return
    medicao.delete()


def remove_medicao_programas_e_projetos_se_inclusao_inativa(
    inclusao, encerrado_a_partir_de
):
    """Remove a medição de Programas e Projetos se ela ficar sem uso no mês.

    Atua só no mês de ``encerrado_a_partir_de``. Outra quantidade ativa na
    instituição faz com que a medição seja mantida. Sem isso, a medição é
    excluída.

    Não faz nada quando a escola ou a data de encerramento estão ausentes.

    Args:
        inclusao (InclusaoAlimentacaoContinua): Inclusão contínua encerrada.
        encerrado_a_partir_de (datetime.date): Data a partir da qual a
            inclusão foi encerrada.
    """
    escola = inclusao.escola
    if not escola or not encerrado_a_partir_de:
        return

    medicao = medicao_programas_e_projetos_do_mes(
        escola, encerrado_a_partir_de.year, encerrado_a_partir_de.month
    )
    exclui_valores_inativos_mes_encerramento(
        medicao, inclusao, encerrado_a_partir_de
    )
