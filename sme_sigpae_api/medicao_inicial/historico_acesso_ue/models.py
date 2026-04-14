from django.db import models

from sme_sigpae_api.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)


class HistoricoAcessoMedicaoInicialUE(
    TemChaveExterna, TemIdentificadorExternoAmigavel, CriadoEm, CriadoPor
):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="historicos_acesso_medicao_inicial_ue",
    )
    data_inicial = models.DateField("Data inicial")
    data_final = models.DateField("Data final", null=True, blank=True)

    class Meta:
        verbose_name = "Histórico de acesso à medição inicial da UE"
        verbose_name_plural = "Históricos de acesso à medição inicial da UE"

    def __str__(self):
        return f"Histórico de acesso à medição inicial da UE - {self.escola.nome} - {self.data_inicial} a {self.data_final or 'presente'}"
