from django.db import models

from src.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    TemAlteradoEm,
    TemChaveExterna,
    TemData,
)
from src.dados_comuns.constants import StringsVerboseNameModels
from src.escola.models import Escola, Lote, PeriodoEscolar, TipoUnidadeEscolar


class DiaLetivoSIGPAE(CriadoEm, CriadoPor, TemAlteradoEm, TemChaveExterna, TemData):
    """Modelo que representa um dia letivo no sistema SIGPAE.

    Associa uma data a lotes, tipos de unidade escolar, escolas e
    períodos escolares, determinando quais instituições possuem aula
    naquele dia.
    """

    lotes = models.ManyToManyField(Lote, related_name="dias_letivos_sigpae")
    tipos_unidade_escolar = models.ManyToManyField(
        TipoUnidadeEscolar, related_name="dias_letivos_sigpae"
    )
    escolas = models.ManyToManyField(Escola, related_name="dias_letivos_sigpae")
    periodos_escolares = models.ManyToManyField(
        PeriodoEscolar, related_name="dias_letivos_sigpae"
    )

    def __str__(self) -> str:
        return f"Dia {self.data} letivo no SIGPAE"

    class Meta:
        verbose_name = StringsVerboseNameModels.DIA_LETIVO_NO_SIGPAE.value
        verbose_name_plural = StringsVerboseNameModels.DIAS_LETIVOS_NO_SIGPAE.value
