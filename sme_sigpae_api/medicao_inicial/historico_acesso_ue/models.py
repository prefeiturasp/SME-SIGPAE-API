import calendar
import datetime

from django.db import models
from django.db.models import Q

from sme_sigpae_api.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)


class HistoricoAcessoMedicaoInicialUEQuerySet(models.QuerySet):
    def por_dre(self, dre_uuid):
        return self.filter(escola__diretoria_regional__uuid=dre_uuid)

    def ativos_no_mes_ano(self, mes: int, ano: int):
        primeiro_dia_mes = datetime.date(ano, mes, 1)
        ultimo_dia_mes = datetime.date(ano, mes, calendar.monthrange(ano, mes)[1])

        return self.filter(
            Q(
                data_final__isnull=False,
                data_inicial__lte=ultimo_dia_mes,
                data_final__gte=primeiro_dia_mes,
            )
            | Q(
                data_final__isnull=True,
                data_inicial__lte=ultimo_dia_mes,
            )
        )


class HistoricoAcessoMedicaoInicialUE(
    TemChaveExterna, TemIdentificadorExternoAmigavel, CriadoEm, CriadoPor
):
    objects = HistoricoAcessoMedicaoInicialUEQuerySet.as_manager()

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
