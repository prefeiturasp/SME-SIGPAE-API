from django import forms
from django.core.exceptions import ValidationError

from .models import MoldeConsolidado


def validate_tipo_solicitacao(value):
    tipos_permitidos = [
        MoldeConsolidado.TP_SOL_ALT_CARDAPIO,
        MoldeConsolidado.TP_SOL_INV_CARDAPIO,
        MoldeConsolidado.TP_SOL_INC_ALIMENTA,
        MoldeConsolidado.TP_SOL_INC_ALIMENTA_CONTINUA,
        MoldeConsolidado.TP_SOL_KIT_LANCHE_AVULSA,
        MoldeConsolidado.TP_SOL_SUSP_ALIMENTACAO,
        MoldeConsolidado.TP_SOL_KIT_LANCHE_UNIFICADA,
        MoldeConsolidado.TP_SOL_TODOS,
    ]
    if value not in tipos_permitidos:
        raise ValidationError(
            f"tipo de solicitação {value} não permitida, deve ser um dos: {tipos_permitidos}"
        )


def validate_status(value):
    value = value.replace("/", "")
    status_solicitacao = [
        MoldeConsolidado.STATUS_AUTORIZADOS,
        MoldeConsolidado.STATUS_NEGADOS,
        MoldeConsolidado.STATUS_CANCELADOS,
        MoldeConsolidado.STATUS_PENDENTES,
        MoldeConsolidado.STATUS_TODOS,
    ]
    if value not in status_solicitacao:
        raise ValidationError(
            f"status de solicitação {value} não permitida, deve ser um dos: {status_solicitacao}"
        )


class FiltroValidator(forms.Form):
    tipo_solicitacao = forms.CharField(validators=[validate_tipo_solicitacao])
    status_solicitacao = forms.CharField(validators=[validate_status])
    data_inicial = forms.DateField()
    data_final = forms.DateField()
