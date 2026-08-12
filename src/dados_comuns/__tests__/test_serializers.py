import pytest
from model_bakery import baker

from ..api.serializers import CategoriaPerguntaFrequenteSerializer
from ..models import CategoriaPerguntaFrequente


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

    serializer = CategoriaPerguntaFrequenteSerializer(
        data={"nome": nome_informado}
    )

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
    assert CategoriaPerguntaFrequente.objects.filter(
        nome="Gestão de Produtos"
    ).exists()


def test_nao_permite_cadastrar_categoria_com_nome_vazio():
    serializer = CategoriaPerguntaFrequenteSerializer(
        data={"nome": ""}
    )

    assert serializer.is_valid() is False
    assert "nome" in serializer.errors
    assert serializer.errors["nome"][0].code == "blank"


def test_nao_permite_cadastrar_categoria_com_nome_maior_que_100_caracteres():
    serializer = CategoriaPerguntaFrequenteSerializer(
        data={"nome": "A" * 101}
    )

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