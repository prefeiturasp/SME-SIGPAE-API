from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from src.cardapio.base.models import TipoAlimentacao
from src.dados_comuns.behaviors import CriadoEm, TemAlteradoEm, TemChaveExterna
from src.escola.models import Escola, Lote


class EscolaAberta(TemChaveExterna, CriadoEm, TemAlteradoEm):
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    data_inicial = models.DateField()
    data_final = models.DateField()
    dias_semana = ArrayField(models.CharField(max_length=1))  # "0" a "6"

    class Meta:
        ordering = ["-alterado_em"]
        verbose_name = "Escola Aberta"
        verbose_name_plural = "Escolas Abertas"

    def __str__(self):
        return f"Escola Aberta {self.uuid}"


class EscolaAbertaUnidadeParticipante(TemChaveExterna, CriadoEm, TemAlteradoEm):
    escola_aberta = models.ForeignKey(
        EscolaAberta, on_delete=models.CASCADE, related_name="unidades_participantes"
    )
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT)
    unidade_educacional = models.ForeignKey(Escola, on_delete=models.PROTECT)
    num_participantes = models.PositiveIntegerField(null=True, blank=True)
    tipos_alimentacao = models.ManyToManyField(
        TipoAlimentacao, related_name="escolas_abertas_unidades"
    )

    class Meta:
        unique_together = ["escola_aberta", "unidade_educacional"]
        verbose_name = "Escola Aberta - Unidade Participante"
        verbose_name_plural = "Escola Aberta - Unidades Participantes"

    def __str__(self):
        return f"{self.unidade_educacional} - {self.escola_aberta_id}"
