import pytest
from model_bakery import baker

from ..api.serializers import (
    CategoriaPerguntaFrequenteSerializer,
    PerguntaFrequenteCreateSerializer,
    PerguntaFrequenteSerializer,
)
from ..constants import MODULO_GESTAO_ALIMENTACAO
from ..models import CategoriaPerguntaFrequente, PerguntaFrequente


@pytest.mark.django_db
@pytest.mark.parametrize(
    "nome_informado",
    [
        "ALIMENTAÇÃO E NUTRIÇÃO",
        "alimentacao e nutricao",
        "Alimentação e Nutrição",
        "  alimentação e nutrição  ",
        "AlImEnTaÇãO e NuTrIçÃo",
        "AlImEnTaÇãO e NuTrIcaO ",
    ],
)
def test_nao_permite_cadastrar_categoria_com_nome_equivalente(
    nome_informado,
):
    baker.make(
        CategoriaPerguntaFrequente,
        nome="Alimentação e Nutrição",
    )

    serializer = CategoriaPerguntaFrequenteSerializer(data={"nome": nome_informado})

    assert serializer.is_valid() is False
    assert serializer.errors["nome"][0] == (
        "Não é possível cadastrar a categoria, pois já existe uma categoria "
        "com esse nome. Altere o nome informado e tente novamente."
    )


def test_permite_cadastrar_categoria_com_nome_novo():
    serializer = CategoriaPerguntaFrequenteSerializer(
        data={"nome": "Gestão de Produtos"}
    )

    assert serializer.is_valid() is True

    categoria = serializer.save()

    assert categoria.nome == "Gestão de Produtos"
    assert CategoriaPerguntaFrequente.objects.filter(nome="Gestão de Produtos").exists()


def test_nao_permite_cadastrar_categoria_com_nome_vazio():
    serializer = CategoriaPerguntaFrequenteSerializer(data={"nome": ""})

    assert serializer.is_valid() is False
    assert "nome" in serializer.errors
    assert serializer.errors["nome"][0].code == "blank"


def test_nao_permite_cadastrar_categoria_com_nome_maior_que_100_caracteres():
    serializer = CategoriaPerguntaFrequenteSerializer(data={"nome": "A" * 101})

    assert serializer.is_valid() is False
    assert "nome" in serializer.errors
    assert serializer.errors["nome"][0].code == "max_length"


def test_permite_atualizar_categoria_mantendo_o_proprio_nome():
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Alimentação Escolar",
    )

    serializer = CategoriaPerguntaFrequenteSerializer(
        instance=categoria,
        data={"nome": "Alimentação Escolar"},
    )

    assert serializer.is_valid() is True

    categoria_atualizada = serializer.save()

    assert categoria_atualizada.nome == "Alimentação Escolar"


def test_nao_permite_atualizar_categoria_com_nome_de_outra_categoria():
    baker.make(
        CategoriaPerguntaFrequente,
        nome="Alimentação Escolar",
    )
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Gestão de Produtos",
    )

    serializer = CategoriaPerguntaFrequenteSerializer(
        instance=categoria,
        data={"nome": "  ALIMENTACAO ESCOLAR  "},
    )

    assert serializer.is_valid() is False
    assert serializer.errors["nome"][0] == (
        "Não é possível cadastrar a categoria, pois já existe uma categoria "
        "com esse nome. Altere o nome informado e tente novamente."
    )


@pytest.mark.django_db
def test_nao_permite_associar_duvida_frequente_a_perfil_inativo():
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        uuid="16f009aa-bc83-45b4-919e-f9fe22bb8876",
    )
    perfil = baker.make(
        "Perfil",
        uuid="738efd93-630b-41db-84bc-29056b74228c",
        ativo=False,
    )
    serializer = PerguntaFrequenteCreateSerializer(
        data={
            "categoria": str(categoria.uuid),
            "perfis": [str(perfil.uuid)],
            "todos_os_perfis": False,
            "pergunta": "Como acessar o sistema?",
            "resposta": "Utilize suas credenciais.",
        }
    )

    assert serializer.is_valid() is False
    assert serializer.errors["perfis"][0].code == "does_not_exist"


@pytest.mark.django_db
def test_serializa_categoria_perfis_e_opcao_todos_da_duvida_frequente():
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome=MODULO_GESTAO_ALIMENTACAO,
        uuid="d84f29c4-6e6e-4d86-b9db-060f4e47458f",
    )
    perfil = baker.make(
        "Perfil",
        nome="DIRETOR_UE",
        uuid="1d1db7f9-d1fb-478a-b482-d547fca1f27c",
        ativo=True,
    )
    pergunta = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        todos_os_perfis=False,
        uuid="ed405293-ff13-48f7-b317-2f803cf614a8",
    )
    pergunta.perfis.add(perfil)

    dados = PerguntaFrequenteSerializer(pergunta).data

    assert dados["categoria"]["uuid"] == str(categoria.uuid)
    assert dados["perfis"][0]["uuid"] == str(perfil.uuid)
    assert dados["perfis"][0]["ativo"] is True
    assert dados["todos_os_perfis"] is False
