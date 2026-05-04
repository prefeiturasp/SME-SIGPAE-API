from django.db import models

from ..dados_comuns.behaviors import (  # noqa I101
    CriadoEm,
    CriadoPor,
    Logs,
    TemChaveExterna,
    TemData,
)
from .utils import (
    alteracoes_de_cardapio_por_escola_periodo_escolar_e_data,
    total_kits_lanche_por_escola_e_data,
    total_merendas_secas_por_escola_periodo_escolar_e_data,
)


class LancamentoDiario(
    CriadoEm, CriadoPor, TemData, Logs, TemChaveExterna, models.Model
):
    escola_periodo_escolar = models.ForeignKey(
        "escola.EscolaPeriodoEscolar", on_delete=models.DO_NOTHING
    )
    tipo_dieta = models.ForeignKey(
        "dieta_especial.ClassificacaoDieta", on_delete=models.DO_NOTHING, null=True
    )
    frequencia = models.IntegerField(null=True)
    merenda_seca = models.IntegerField(null=True)
    lanche_4h = models.IntegerField(null=True)
    lanche_5h = models.IntegerField(null=True)
    ref_enteral = models.IntegerField(null=True)
    observacoes = models.TextField(blank=True)
    eh_dia_de_sobremesa_doce = models.BooleanField(default=False)

    @property
    def kits_lanches(self):
        return total_kits_lanche_por_escola_e_data(
            self.escola_periodo_escolar.escola, self.data
        )

    @property
    def merenda_seca_solicitada(self):
        return total_merendas_secas_por_escola_periodo_escolar_e_data(
            self.escola_periodo_escolar, self.data
        )

    @property
    def troca(self):
        return alteracoes_de_cardapio_por_escola_periodo_escolar_e_data(
            self.escola_periodo_escolar, self.data
        )

    def __str__(self):
        return str(self.uuid)


class Refeicao(models.Model):
    ref_oferta = models.IntegerField(null=True)
    ref_repet = models.IntegerField(null=True)
    sob_oferta = models.IntegerField(null=True)
    sob_repet = models.IntegerField(null=True)
    lancamento = models.ForeignKey(
        LancamentoDiario, on_delete=models.CASCADE, related_name="refeicoes"
    )

    def __str__(self):
        return f"{self.id} - Pertencente ao lançamento ${self.lancamento.uuid}"
