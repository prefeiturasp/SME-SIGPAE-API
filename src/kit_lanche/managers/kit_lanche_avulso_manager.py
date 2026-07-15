import datetime

from django.db import models

from ...dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


class SolicitacoesKitLancheAvulsaDestaSemanaManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=7)
        return (
            super(SolicitacoesKitLancheAvulsaDestaSemanaManager, self)
            .get_queryset()
            .filter(
                solicitacao_kit_lanche__data__range=(
                    data_limite_inicial,
                    data_limite_final,
                )
            )
        )


class SolicitacoesKitLancheAvulsaDesteMesManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        data_limite_inicial = hoje
        data_limite_final = hoje + datetime.timedelta(days=31)
        return (
            super(SolicitacoesKitLancheAvulsaDesteMesManager, self)
            .get_queryset()
            .filter(
                solicitacao_kit_lanche__data__range=(
                    data_limite_inicial,
                    data_limite_final,
                )
            )
        )


class SolicitacoesKitLancheAvulsaVencidaDiasManager(models.Manager):
    def get_queryset(self):
        hoje = datetime.date.today()
        return (
            super(SolicitacoesKitLancheAvulsaVencidaDiasManager, self)
            .get_queryset()
            .filter(solicitacao_kit_lanche__data__lt=hoje)
            .filter(
                status__in=[
                    PedidoAPartirDaEscolaWorkflow.RASCUNHO,
                    PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
                    PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
                    PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
                ]
            )
        )
