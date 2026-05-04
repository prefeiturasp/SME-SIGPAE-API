from django.db import models

from src.dados_comuns.behaviors import (
    Logs,
    ModeloBase,
    TemIdentificadorExternoAmigavel,
)
from src.dados_comuns.fluxo_status import FluxoCronogramaSemanal
from src.pre_recebimento.cronograma_entrega.models import Cronograma


class CronogramaSemanal(
    ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoCronogramaSemanal
):
    """
    Cronograma Semanal FLV derivado de Cronograma Mensal Ponto a Ponto.
    O status é gerenciado pelo FluxoCronogramaSemanal (inicia como RASCUNHO).
    """

    numero = models.CharField(
        "Número do Cronograma Semanal",
        blank=True,
        null=True,
        max_length=250,
        unique=True,
    )
    cronograma_mensal = models.ForeignKey(
        Cronograma,
        on_delete=models.PROTECT,
        related_name="cronogramas_semanais",
        verbose_name="Cronograma Mensal",
    )
    observacoes = models.TextField("Observações", blank=True)

    def __str__(self):
        return (
            f"Cronograma Semanal {self.numero or self.uuid} - "
            f"Status: {self.get_status_display()}"
        )

    class Meta:
        verbose_name = "Cronograma Semanal"
        verbose_name_plural = "Cronogramas Semanais"


class ProgramacaoEntregaSemanal(ModeloBase):
    """
    Programação de entrega semanal.
    Cada cronograma semanal pode ter múltiplas programações de entrega.
    """

    cronograma_semanal = models.ForeignKey(
        CronogramaSemanal,
        on_delete=models.CASCADE,
        related_name="programacoes",
        verbose_name="Cronograma Semanal",
    )
    mes_programado = models.CharField(
        "Mês Programado",
        max_length=7,
        help_text="Formato MM/YYYY",
    )
    data_inicio = models.DateField("Data Início")
    data_fim = models.DateField("Data Fim")
    quantidade = models.FloatField("Quantidade da Entrega")

    def __str__(self):
        return (
            f"Programação {self.mes_programado} - {self.data_inicio} a {self.data_fim}"
        )

    class Meta:
        verbose_name = "Programação de Entrega Semanal"
        verbose_name_plural = "Programações de Entrega Semanal"
        ordering = ["mes_programado", "data_inicio"]
