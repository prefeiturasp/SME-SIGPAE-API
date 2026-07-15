import datetime

from django.db import models

from ...dados_comuns.fluxo_status import PedidoAPartirDaDiretoriaRegionalWorkflow


class SolicitacaoUnificadaDestaSemanaManager(models.Manager):
    def get_queryset(self):
        data_limite_inicial = datetime.date.today()
        data_limite_final = datetime.date.today() + datetime.timedelta(days=7)
        return (
            super(SolicitacaoUnificadaDestaSemanaManager, self)
            .get_queryset()
            .filter(
                solicitacao_kit_lanche__data__range=(
                    data_limite_inicial,
                    data_limite_final,
                )
            )
        )


class SolicitacaoUnificadaDesteMesManager(models.Manager):
    def get_queryset(self):
        data_limite_inicial = datetime.date.today()
        data_limite_final = datetime.date.today() + datetime.timedelta(days=31)
        return (
            super(SolicitacaoUnificadaDesteMesManager, self)
            .get_queryset()
            .filter(
                solicitacao_kit_lanche__data__range=(
                    data_limite_inicial,
                    data_limite_final,
                )
            )
        )


class SolicitacaoUnificadaVencidaManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        return (
            super(SolicitacaoUnificadaVencidaManager, self)
            .get_queryset()
            .filter(solicitacao_kit_lanche__data__lt=hoje)
            .filter(
                status__in=[
                    PedidoAPartirDaDiretoriaRegionalWorkflow.RASCUNHO,
                    PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_PEDIU_DRE_REVISAR,
                    PedidoAPartirDaDiretoriaRegionalWorkflow.CODAE_A_AUTORIZAR,
                ]
            )
        )
