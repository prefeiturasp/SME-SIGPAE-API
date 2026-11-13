from __future__ import annotations

from django.db import models

from src.dados_comuns.constants import StringsVerboseNameModels

from ...dados_comuns.behaviors import Nomeavel, TemChaveExterna
from ..diretoria_regional.models import DiretoriaRegional


class Subprefeitura(Nomeavel, TemChaveExterna):
    OPCOES_AGRUPAMENTO = (
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
    )

    codigo_eol = models.CharField(  # noqa DJ01
        StringsVerboseNameModels.CODIGO_EOL.value,
        max_length=6,
        unique=True,
        null=True,
        blank=True,
    )
    diretoria_regional = models.ManyToManyField(
        DiretoriaRegional, related_name="subprefeituras", blank=True
    )
    lote = models.ForeignKey(
        "Lote",
        related_name="subprefeituras",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    agrupamento = models.PositiveSmallIntegerField(
        choices=OPCOES_AGRUPAMENTO, default=1
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Subprefeitura"
        verbose_name_plural = "Subprefeituras"
        ordering = ("nome",)
