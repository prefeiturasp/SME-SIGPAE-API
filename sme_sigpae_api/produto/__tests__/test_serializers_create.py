import pytest
from model_bakery import baker
from sme_sigpae_api.produto.api.serializers.serializers_create import *

pytestmark = pytest.mark.django_db

def test_produto_edital_create(produto_edital_rascunho):
    class FakeObject(object):
        user = baker.make("perfil.Usuario")

    serializer = CadastroProdutosEditalCreateSerializer(data=produto_edital_rascunho, context={"request": FakeObject})
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save() 

    assert instance.nome == produto_edital_rascunho['nome']
    assert instance.ativo is True
    assert instance.tipo_produto == produto_edital_rascunho['tipo_produto']


def test_produto_edital_update(produto_logistica, produto_edital_rascunho):
    serializer = CadastroProdutosEditalCreateSerializer(produto_logistica, data=produto_edital_rascunho)
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save() 

    assert instance.nome == produto_edital_rascunho['nome']
    assert instance.ativo is True
    assert instance.tipo_produto == produto_edital_rascunho['tipo_produto']


def test_produto_erro_nome_duplicado_create(produto_logistica):
    serializer = CadastroProdutosEditalCreateSerializer(
        data={
            "nome": "PRODUTO TESTE",
            "tipo_produto": "LOGISTICA",
            "ativo": "Ativo",
        },
        context={"request": type("FakeRequest", (), { "user": produto_logistica.criado_por })()},
    )
    assert serializer.is_valid(), serializer.errors 
    with pytest.raises(serializers.ValidationError) as excinfo:
        serializer.save()
    assert "Item já cadastrado" in str(excinfo.value)