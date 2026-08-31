"""Modelos do submódulo de ajuste de saldo do laudo."""

from django.db import models

from src.pre_recebimento.documento_recebimento.models import DocumentoDeRecebimento

from ...dados_comuns.behaviors import (
    ModeloBase,
)


class AjusteSaldo(ModeloBase):
    """Ajuste (desconto) de saldo de um laudo de documento de recebimento.

    Registra a ``quantidade_descontada`` de um documento de recebimento,
    reduzindo o saldo disponível do laudo. O saldo disponível é calculado
    pela função ``calcular_saldo_laudo`` (quantidade do laudo menos o total
    recebido em fichas assinadas menos os ajustes já registrados).
    """

    documento_recebimento = models.ForeignKey(
        DocumentoDeRecebimento,
        on_delete=models.CASCADE,
        related_name="ajustes_saldo",
    )
    quantidade_descontada = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
