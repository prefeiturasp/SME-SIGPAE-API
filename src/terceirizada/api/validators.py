import re

from rest_framework import serializers

from src.terceirizada.models import Terceirizada

MENSAGEM_CNPJ_DUPLICADO = (
    "Não foi possível concluir o cadastro, pois já existe uma empresa "
    "cadastrada com o CNPJ informado."
)


def normaliza_cnpj(cnpj):
    if not cnpj:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(cnpj)).upper()


def valida_cnpj_unico(cnpj, empresa=None):
    empresas_com_cnpj = Terceirizada.objects.filter(cnpj__iexact=normaliza_cnpj(cnpj))

    if empresa is not None:
        empresas_com_cnpj = empresas_com_cnpj.exclude(uuid=empresa.uuid)

    if empresas_com_cnpj.exists():
        raise serializers.ValidationError(MENSAGEM_CNPJ_DUPLICADO)

    return cnpj
