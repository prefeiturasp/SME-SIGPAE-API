from django.db import models

from src.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    TemAlteradoEm,
    TemChaveExterna,
    TemData,
)
from src.escola.models import Escola, Lote, PeriodoEscolar, TipoUnidadeEscolar


class DiaLetivoSIGPAE(CriadoEm, CriadoPor, TemAlteradoEm, TemChaveExterna, TemData):
    lotes = models.ManyToManyField(Lote, related_name="dias_letivos_sigpae")
    tipos_unidade_escolar = models.ManyToManyField(
        TipoUnidadeEscolar, related_name="dias_letivos_sigpae"
    )
    escolas = models.ManyToManyField(Escola, related_name="dias_letivos_sigpae")
    periodos_escolares = models.ManyToManyField(
        PeriodoEscolar, related_name="dias_letivos_sigpae"
    )

    def __str__(self):
        return f"Dia {self.data} letivo no SIGPAE"

    class Meta:
        verbose_name = "Dia letivo no SIGPAE"
        verbose_name_plural = "Dias letivos no SIGPAE"
