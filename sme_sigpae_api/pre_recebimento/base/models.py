
from django.db import models
from sme_sigpae_api.dados_comuns.behaviors import TemChaveExterna, Nomeavel, CriadoEm


class UnidadeMedida(TemChaveExterna, Nomeavel, CriadoEm):
    abreviacao = models.CharField("Abreviação", max_length=25)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"
        unique_together = ("nome",)

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        self.abreviacao = self.abreviacao.lower()
        super().save(*args, **kwargs)