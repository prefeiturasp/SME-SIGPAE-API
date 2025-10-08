# tests/test_ficha_tecnica_serializer.py
import pytest
from model_bakery import baker
from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializer_create import FichaTecnicaCreateSerializer
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto

pytestmark = pytest.mark.django_db


def test_valido_nao_perecivel_com_produto_liquido(payload_base):
    payload_base["produto_eh_liquido"] = True
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert serializer.is_valid(), serializer.errors


def test_invalido_nao_perecivel_sem_produto_liquido(payload_base):
    payload_base.pop("produto_eh_liquido", None)
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    is_valid = serializer.is_valid()
    assert not is_valid
    errors = str(serializer.errors)
    assert (
        "Fichas Técnicas de Produtos NÃO PERECÍVEIS exigem que sejam forncecidos valores para os campos agroecologico, organico, e produto_eh_liquido"
        in errors
    ), errors


def test_valido_perecivel_com_campos_obrigatorios(payload_base):
    payload_base.update({
        "categoria": FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        "agroecologico": True,
        "prazo_validade_descongelamento": "2 dias",
        "temperatura_congelamento": -18,
        "temperatura_veiculo": 4,
        "condicoes_de_transporte": "refrigerado",
        "variacao_percentual": 5.0,
    })
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert serializer.is_valid(),  serializer.errors


def test_invalido_perecivel_sem_campos_obrigatorios(payload_base):
    payload_base["categoria"] = FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS
    for campo in [
        "prazo_validade_descongelamento",
        "temperatura_congelamento",
        "temperatura_veiculo",
        "condicoes_de_transporte",
        "variacao_percentual",
    ]:
        payload_base.pop(campo, None)

    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    is_valid = serializer.is_valid()
    assert not is_valid
    errors = str(serializer.errors)
    assert (
        "Fichas Técnicas de Produtos PERECÍVEIS exigem que sejam forncecidos valores para os campos agroecologico, organico, prazo_validade_descongelamento, temperatura_congelamento, temperatura_veiculo, condicoes_de_transporte e variacao_percentual."
        in errors
    ), errors
    
    
def test_produto_eh_liquido_true_valido(payload_base):
    payload_base["produto_eh_liquido"] = True
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert serializer.is_valid(), serializer.errors


def test_produto_eh_liquido_false_valido(payload_base):
    payload_base["produto_eh_liquido"] = False
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert serializer.is_valid(), serializer.errors
    
@pytest.mark.parametrize("valor_invalido", [None, "sim", "não", "verdadeiro", "falso", "null", []])
def test_produto_eh_liquido_invalido(payload_base, valor_invalido):
    payload_base["produto_eh_liquido"] = valor_invalido
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    is_valid = serializer.is_valid()
    assert not is_valid
    errors = str(serializer.errors)
    assert (
       "Este campo não pode ser nulo."
    ), errors


def test_produto_eh_liquido_opcional_para_perecivel(payload_base):
    payload_base.update({
        "categoria": FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
        "prazo_validade_descongelamento": "2 dias",
        "temperatura_congelamento": -18,
        "temperatura_veiculo": 4,
        "condicoes_de_transporte": "refrigerado",
        "variacao_percentual": 5.0,
    })
    payload_base.pop("produto_eh_liquido", None)
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert serializer.is_valid(), serializer.errors
    
    
def test_produto_eh_liquido_obrigatorio_para_nao_perecivel(payload_base):
    payload_base["categoria"] = FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS
    payload_base.pop("produto_eh_liquido", None)
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert not serializer.is_valid()
    assert (
        "Fichas Técnicas de Produtos NÃO PERECÍVEIS exigem que sejam forncecidos valores"
        in str(serializer.errors)
    )