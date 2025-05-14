import datetime

from django.db import models

from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


class AlteracoesCardapioDestaSemanaManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(AlteracoesCardapioDestaSemanaManager, self)
            .get_queryset()
            .filter(data_inicial__range=(data_limite_inicial, data_limite_final))
        )


class AlteracoesCardapioDesteMesManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(AlteracoesCardapioDesteMesManager, self)
            .get_queryset()
            .filter(data_inicial__range=(data_limite_inicial, data_limite_final))
        )


class AlteracoesCardapioVencidaManager(models.Manager):
    def get_queryset(self):
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
    def get_queryset(self):
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
