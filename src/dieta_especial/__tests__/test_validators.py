import pytest
from rest_framework.exceptions import ValidationError

from src.dieta_especial.protocolo_padrao.api.validators import (
    edital_ja_existe_protocolo,
)

from ...dados_comuns.validators import deve_ter_extensao_valida

pytestmark = pytest.mark.django_db


def test_extensoes_validas(nomes_arquivos_validos):
    nome = deve_ter_extensao_valida(nomes_arquivos_validos)
    assert type(nome) is str


def test_extensoes_invalidas(nomes_arquivos_invalidos):
    with pytest.raises(ValidationError, match="Extensão inválida"):
        deve_ter_extensao_valida(nomes_arquivos_invalidos)


@pytest.mark.parametrize(
    "editais,quantidade_editais,msg_esperada",
    [
        ([{"numero": "E1"}], 0, "Já existe um protocolo padrão com esse nome."),
        (
            [{"numero": "E1"}, {"numero": "E2"}],
            2,
            "Já existe um protocolo padrão com esse nome para os editais: E1, E2.",
        ),
    ],
)
def test_edital_ja_existe_protocolo(editais, quantidade_editais, msg_esperada):
    with pytest.raises(ValidationError, match=msg_esperada):
        edital_ja_existe_protocolo(editais, quantidade_editais)
