from django.db import models

from src.pre_recebimento.documento_recebimento.models import DocumentoDeRecebimento

from ...dados_comuns.behaviors import (
    ModeloBase,
)


class AjusteSaldo(ModeloBase):
    documento_recebimento = models.ForeignKey(
        DocumentoDeRecebimento,
        on_delete=models.CASCADE,
        related_name="ajustes_saldo",
    )
    quantidade_descontada = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
