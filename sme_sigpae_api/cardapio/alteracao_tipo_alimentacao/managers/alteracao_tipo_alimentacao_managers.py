"""Managers customizados para o modelo AlteracaoCardapio.

Cada manager aplica um filtro diferente sobre o queryset padrão, segmentando
as alterações de cardápio por janela temporal ou status do fluxo de trabalho.
"""

import datetime

from django.db import models

from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


class AlteracoesCardapioDestaSemanaManager(models.Manager):
    """Manager que retorna alterações de cardápio com início nos próximos 7 dias."""

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo da semana atual.

        Returns:
            QuerySet: Alterações cuja ``data_inicial`` está entre hoje e hoje + 7 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(AlteracoesCardapioDestaSemanaManager, self)
            .get_queryset()
            .filter(data_inicial__range=(data_limite_inicial, data_limite_final))
        )


class AlteracoesCardapioDesteMesManager(models.Manager):
    """Manager que retorna alterações de cardápio com início nos próximos 31 dias."""

    def get_queryset(self):
        """Retorna o queryset filtrado pelo intervalo do mês atual.

        Returns:
            QuerySet: Alterações cuja ``data_inicial`` está entre hoje e hoje + 31 dias.
        """
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(AlteracoesCardapioDesteMesManager, self)
            .get_queryset()
            .filter(data_inicial__range=(data_limite_inicial, data_limite_final))
        )


class AlteracoesCardapioVencidaManager(models.Manager):
    """Manager que retorna alterações de cardápio vencidas e ainda em status aberto.

    Considera vencidas as alterações com ``data_inicial`` anterior a hoje e que
    ainda estejam nos status RASCUNHO, DRE_A_VALIDAR ou DRE_PEDIU_ESCOLA_REVISAR.
    """

    def get_queryset(self):
        """Retorna o queryset das alterações vencidas.

        Returns:
            QuerySet: Alterações com ``data_inicial`` passada e status pendente.
        """
        hoje = datetime.date.today()
        return (
            super(AlteracoesCardapioVencidaManager, self)
            .get_queryset()
            .filter(data_inicial__lt=hoje)
            .filter(
                status__in=[
                    PedidoAPartirDaEscolaWorkflow.RASCUNHO,
                    PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
                    PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
                ]
            )
        )


class AlteracoesCardapioDoMesCorrenteManager(models.Manager):
    """Manager que retorna alterações de cardápio do mês corrente em status ativo.

    Filtra pelo primeiro e último dia do mês atual, incluindo apenas alterações
    cujo status indica que ainda estão em andamento no fluxo de trabalho.
    """

    def get_queryset(self):
        """Retorna o queryset das alterações do mês corrente.

        Returns:
            QuerySet: Alterações com ``data_inicial`` dentro do mês atual e em
            status ativo (DRE_A_VALIDAR, DRE_VALIDADO, CODAE_AUTORIZADO, etc.).
        """
        hoje = datetime.datetime.today().date()
        primeiro_dia_do_mes = hoje.replace(month=hoje.month, day=1)
        proximo_mes = hoje.replace(day=28) + datetime.timedelta(days=4)
        ultimo_dia_do_mes = proximo_mes - datetime.timedelta(days=proximo_mes.day)
        return (
            super(AlteracoesCardapioDoMesCorrenteManager, self)
            .get_queryset()
            .filter(data_inicial__range=(primeiro_dia_do_mes, ultimo_dia_do_mes))
            .filter(
                status__in=[
                    PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
                    PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
                    PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
                    PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
                    PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO,
                    PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO,
                    PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
                ]
            )
        )
