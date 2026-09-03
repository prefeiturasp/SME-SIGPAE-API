"""Utilitários de inclusão contínua e medição de Programas e Projetos.

Funções auxiliares para identificar períodos ativos no mês e remover
valores de Programas e Projetos no mês em que a inclusão contínua é
encerrada antecipadamente.
"""

import datetime

from src.dados_comuns.constants import GRUPO_PROGRAMAS_E_PROJETOS
from src.dados_comuns.utils import get_ultimo_dia_mes


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


def inclusao_possui_quantidade_ativa_no_mes(
    inclusao, primeiro_dia_mes, ultimo_dia_mes
):
    """Indica se a inclusão contínua ainda tem quantidade ativa no mês.

    Quantidades canceladas são ignoradas.

    Args:
        inclusao (InclusaoAlimentacaoContinua): Inclusão contínua avaliada.
        primeiro_dia_mes (datetime.date): Primeiro dia do mês avaliado.
        ultimo_dia_mes (datetime.date): Último dia do mês avaliado.

    Returns:
        bool: ``True`` se alguma quantidade não cancelada ainda tiver dia
        ativo no mês.
    """
    for quantidade_periodo in inclusao.quantidades_periodo.filter(cancelado=False):
        if quantidade_periodo_possui_dia_ativo_no_mes(
            quantidade_periodo, primeiro_dia_mes, ultimo_dia_mes
        ):
            return True
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


def exclui_valores_medicao_a_partir_do_dia(medicao, dia):
    """Exclui valores da medição de Programas e Projetos a partir de um dia.

    A medição em si é mantida, assim como os valores anteriores ao dia
    informado. A exclusão dos valores é feita em uma única consulta.

    Args:
        medicao (Medicao): Medição de Programas e Projetos. Se ``None``, a
            função não faz nada.
        dia (int): Primeiro dia cujos valores devem ser excluídos
            (inclusivo).
    """
    if not medicao:
        return
    medicao.valores_medicao.filter(dia__gte=f"{dia:02d}").delete()


def exclui_valores_inativos_mes_encerramento(medicao, inclusao, encerrado_a_partir_de):
    """Remove valores inativos no mês do encerramento antecipado.

    A data ``encerrado_a_partir_de`` permanece vigente. Só exclui valores
    dos dias seguintes, e apenas se nenhuma quantidade da inclusão continuar
    ativa nesse restante do mês. Se o encerramento cair no último dia do
    mês, nada é removido.

    Args:
        medicao (Medicao): Medição de Programas e Projetos do mês do
            encerramento. Se ``None``, a função não faz nada.
        inclusao (InclusaoAlimentacaoContinua): Inclusão contínua encerrada.
        encerrado_a_partir_de (datetime.date): Data a partir da qual a
            inclusão foi encerrada.
    """
    if not medicao:
        return
    primeiro_dia_inativo = encerrado_a_partir_de + datetime.timedelta(days=1)
    ultimo_dia_mes = get_ultimo_dia_mes(
        datetime.date(encerrado_a_partir_de.year, encerrado_a_partir_de.month, 1)
    )
    if primeiro_dia_inativo > ultimo_dia_mes:
        return
    if inclusao_possui_quantidade_ativa_no_mes(
        inclusao, primeiro_dia_inativo, ultimo_dia_mes
    ):
        return
    exclui_valores_medicao_a_partir_do_dia(medicao, primeiro_dia_inativo.day)


def remove_medicao_programas_e_projetos_se_inclusao_inativa(
    inclusao, encerrado_a_partir_de
):
    """Remove valores inativos de Programas e Projetos no mês do encerramento.

    Atua só no mês de ``encerrado_a_partir_de``: mantém a medição e os
    valores ainda vigentes e exclui os posteriores à data. Meses anteriores
    e posteriores não são alterados.

    Não faz nada quando a escola ou a data de encerramento estão ausentes,
    nem quando outra quantidade da inclusão permanece ativa no restante do
    mês.

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
