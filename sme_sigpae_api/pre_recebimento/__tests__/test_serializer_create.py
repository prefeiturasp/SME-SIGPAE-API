# tests/test_ficha_tecnica_serializer.py
import pytest
from model_bakery import baker
from rest_framework import serializers

from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.serializers.serializer_create import (
    FichaTecnicaCreateSerializer,
    FichaTecnicaFLVCreateSerializer,
    AnaliseFichaTecnicaCreateSerializer,
)
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
        "Fichas Técnicas de Produtos NÃO PERECÍVEIS exigem que sejam fornecidos valores para os campos organico, e produto_eh_liquido"
        in errors
    ), errors


def test_valido_perecivel_com_campos_obrigatorios(payload_base):
    payload_base.update(
        {
            "categoria": FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
            "prazo_validade_descongelamento": "2 dias",
            "temperatura_congelamento": -18,
            "temperatura_veiculo": 4,
            "condicoes_de_transporte": "refrigerado",
            "variacao_percentual": 5.0,
        }
    )
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert serializer.is_valid(), serializer.errors


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
        "Fichas Técnicas de Produtos PERECÍVEIS exigem que sejam fornecidos valores para os campos organico, prazo_validade_descongelamento, temperatura_congelamento, temperatura_veiculo, condicoes_de_transporte e variacao_percentual."
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


@pytest.mark.parametrize(
    "valor_invalido", [None, "sim", "não", "verdadeiro", "falso", "null", []]
)
def test_produto_eh_liquido_invalido(payload_base, valor_invalido):
    payload_base["produto_eh_liquido"] = valor_invalido
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    is_valid = serializer.is_valid()
    assert not is_valid
    errors = str(serializer.errors)
    assert "Este campo não pode ser nulo.", errors


def test_produto_eh_liquido_opcional_para_perecivel(payload_base):
    payload_base.update(
        {
            "categoria": FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
            "prazo_validade_descongelamento": "2 dias",
            "temperatura_congelamento": -18,
            "temperatura_veiculo": 4,
            "condicoes_de_transporte": "refrigerado",
            "variacao_percentual": 5.0,
        }
    )
    payload_base.pop("produto_eh_liquido", None)
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert serializer.is_valid(), serializer.errors


def test_produto_eh_liquido_obrigatorio_para_nao_perecivel(payload_base):
    payload_base["categoria"] = FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS
    payload_base.pop("produto_eh_liquido", None)
    serializer = FichaTecnicaCreateSerializer(data=payload_base)
    assert not serializer.is_valid()
    assert (
        "Fichas Técnicas de Produtos NÃO PERECÍVEIS exigem que sejam fornecidos valores"
        in str(serializer.errors)
    )


def test_ficha_flv_valida(payload_base_flv):
    payload_base_flv["categoria"] = FichaTecnicaDoProduto.CATEGORIA_FLV
    serializer = FichaTecnicaFLVCreateSerializer(data=payload_base_flv)
    assert serializer.is_valid(), serializer.errors


def make_serializer(payload, ficha_tecnica, usuario):
    return AnaliseFichaTecnicaCreateSerializer(
        data=payload,
        context={"ficha_tecnica": ficha_tecnica, "criado_por": usuario},
    )


def test_analise_normal_valida(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario):
    serializer = make_serializer(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario)
    assert serializer.is_valid(), serializer.errors


def test_analise_normal_conferido_false_com_correcoes_valido(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario):
    payload_analise_aprovada.update({
        "conservacao_conferido": False,
        "conservacao_correcoes": "Temperatura incorreta.",
        "aprovada": False,
    })
    serializer = make_serializer(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario)
    assert serializer.is_valid(), serializer.errors


def test_analise_normal_conferido_false_sem_correcoes_invalido(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario):
    payload_analise_aprovada.update({
        "conservacao_conferido": False,
        "conservacao_correcoes": "",
        "aprovada": False,
    })
    serializer = make_serializer(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario)
    assert not serializer.is_valid()
    assert "não pode ser vazio" in str(serializer.errors)


def test_analise_normal_conferido_true_com_correcoes_invalido(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario):
    payload_analise_aprovada.update({
        "modo_preparo_conferido": True,
        "modo_preparo_correcoes": "Correção indevida.",
    })
    serializer = make_serializer(payload_analise_aprovada, ficha_tecnica_nao_perecivel, usuario)
    assert not serializer.is_valid()
    assert "deve ser vazio" in str(serializer.errors)


def test_analise_normal_campos_inexistentes_para_flv_sao_obrigatorios(ficha_tecnica_nao_perecivel, usuario):
    serializer = make_serializer({}, ficha_tecnica_nao_perecivel, usuario)
    assert not serializer.is_valid()
    for campo in [
        "informacoes_nutricionais_conferido",
        "conservacao_conferido",
        "armazenamento_conferido",
        "embalagem_e_rotulagem_conferido",
        "modo_preparo_conferido",
    ]:
        assert campo in serializer.errors, f"Esperado erro em: {campo}"


def test_analise_flv_valida_sem_campos_inexistentes(payload_analise_flv_aprovada, ficha_tecnica_flv, usuario):
    serializer = make_serializer(payload_analise_flv_aprovada, ficha_tecnica_flv, usuario)
    assert serializer.is_valid(), serializer.errors


def test_analise_flv_campos_inexistentes_ignorados_mesmo_se_enviados(payload_analise_flv_aprovada, ficha_tecnica_flv, usuario):
    payload_analise_flv_aprovada.update({
        "modo_preparo_conferido": False,
        "modo_preparo_correcoes": "",
    })
    serializer = make_serializer(payload_analise_flv_aprovada, ficha_tecnica_flv, usuario)
    assert serializer.is_valid(), serializer.errors


def test_analise_flv_campos_obrigatorios_continuam_sendo_validados(payload_analise_flv_aprovada, ficha_tecnica_flv, usuario):
    payload_analise_flv_aprovada.update({
        "fabricante_envasador_conferido": False,
        "fabricante_envasador_correcoes": "",
        "aprovada": False,
    })
    serializer = make_serializer(payload_analise_flv_aprovada, ficha_tecnica_flv, usuario)
    assert not serializer.is_valid()
    assert "não pode ser vazio" in str(serializer.errors)
