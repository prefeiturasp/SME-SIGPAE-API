import calendar
import datetime

from django.db import models
from django.db.models import Q

from src.dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)
from src.dados_comuns.constants import (
    MODEL_ESCOLA,
    MODEL_LOTE,
    StringsVerboseNameModels,
)


class HistoricoAcessoMedicaoInicialUEQuerySet(models.QuerySet):
    def por_dre(self, dre_uuid):
        return self.filter(escola__diretoria_regional__uuid=dre_uuid)

    def ativos_no_mes_ano(self, mes: int, ano: int):
        ultimo_dia_mes = datetime.date(ano, mes, calendar.monthrange(ano, mes)[1])

        return self.filter(
            Q(
                data_final__isnull=False,
                data_inicial__lte=ultimo_dia_mes,
                data_final__gt=ultimo_dia_mes,
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
        MODEL_ESCOLA,
        on_delete=models.CASCADE,
        related_name="historicos_acesso_medicao_inicial_ue",
    )
    lote = models.ForeignKey(
        MODEL_LOTE,
        on_delete=models.CASCADE,
        related_name="historicos_acesso_medicao_inicial_ue",
    )
    data_inicial = models.DateField(StringsVerboseNameModels.DATA_INICIAL.value)
    data_final = models.DateField(
        StringsVerboseNameModels.DATA_FINAL.value, null=True, blank=True
    )

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.HISTORICO_DE_ACESSO_A_MEDICAO_INICIAL_DA_UE.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.HISTORICOS_DE_ACESSO_A_MEDICAO_INICIAL_DA_UE.value
        )

    def __str__(self):
        return f"Histórico de acesso à medição inicial da UE - {self.escola.nome} - {self.lote.nome} - {self.data_inicial} a {self.data_final or 'presente'}"
