import pytest
from rest_framework import serializers

from src.terceirizada.api.validators import (
    MENSAGEM_CNPJ_DUPLICADO,
    normaliza_cnpj,
    valida_cnpj_unico,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def empresa(empresa_factory):
    return empresa_factory()


def test_normaliza_cnpj_remove_formatacao_e_converte_para_maiusculo():
    assert normaliza_cnpj("12.abc.345/6789-01") == "12ABC345678901"


def test_mensagem_cnpj_duplicado_corresponde_a_historia():
    assert MENSAGEM_CNPJ_DUPLICADO == (
        "Não foi possível concluir o cadastro, pois já existe uma empresa "
        "cadastrada com o CNPJ informado."
    )


def test_normaliza_cnpj_retorna_vazio_quando_valor_nao_informado():
    assert normaliza_cnpj(None) == ""
    assert normaliza_cnpj("") == ""


def test_valida_cnpj_unico_quando_nao_existe_empresa_com_cnpj():
    assert valida_cnpj_unico("12345678901234") == "12345678901234"


def test_valida_cnpj_unico_quando_existe_empresa_com_cnpj(empresa):
    with pytest.raises(serializers.ValidationError) as exc:
        valida_cnpj_unico(empresa.cnpj)

    assert exc.value.detail[0] == MENSAGEM_CNPJ_DUPLICADO


def test_valida_cnpj_unico_quando_outra_empresa_possui_o_cnpj(empresa, empresa_factory):
    outra_empresa = empresa_factory()

    with pytest.raises(serializers.ValidationError):
        valida_cnpj_unico(empresa.cnpj, empresa=outra_empresa)


def test_valida_cnpj_unico_ignora_a_propria_empresa(empresa):
    assert valida_cnpj_unico(empresa.cnpj, empresa=empresa) == empresa.cnpj


def test_valida_cnpj_unico_considera_cnpj_com_formatacao(empresa):
    cnpj_formatado = (
        f"{empresa.cnpj[:2]}.{empresa.cnpj[2:5]}.{empresa.cnpj[5:8]}/"
        f"{empresa.cnpj[8:12]}-{empresa.cnpj[12:]}"
    )

    with pytest.raises(serializers.ValidationError):
        valida_cnpj_unico(cnpj_formatado)


def test_valida_cnpj_unico_nao_diferencia_maiusculas(empresa):
    empresa.cnpj = "12abc345678901"
    empresa.save(update_fields=["cnpj"])

    with pytest.raises(serializers.ValidationError):
        valida_cnpj_unico("12ABC345678901")
