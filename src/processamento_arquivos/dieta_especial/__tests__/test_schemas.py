import pytest
from pydantic import ValidationError

from ..schemas import (
    ArquivoCargaAlimentosSchema,
    ArquivoCargaDietaEspecialSchema,
)


def test_schema_arquivo_alimento_e_substitutos():
    dicionario_dados = {"nome": "ARROZ"}
    assert ArquivoCargaAlimentosSchema(**dicionario_dados)


def test_schema_arquivo_alimento_e_substitutos_value_error():
    dicionario_dados = {"nome": None}
    with pytest.raises(ValidationError):
        ArquivoCargaAlimentosSchema(**dicionario_dados)


def test_schema_arquivo_importa_dieta_especial():
    dicionario_dados = {
        "dre": "BT",
        "tipo_gestao": "Terceirizada",
        "tipo_unidade": "DIRETA",
        "codigo_escola": "12345678",
        "nome_unidade": "Uma Unidade",
        "codigo_eol_aluno": "1234567",
        "nome_aluno": "Anderson Marques",
        "data_nascimento": "11/01/1989",
        "data_ocorrencia": "11/01/1989",
        "codigo_diagnostico": "Aluno Alérgico",
        "protocolo_dieta": "Alérgico",
        "codigo_categoria_dieta": "A",
    }
    assert ArquivoCargaDietaEspecialSchema(**dicionario_dados)


def test_schema_arquivo_importa_dieta_especial_erro_codigo_eol_aluno():
    dicionario_dados = {
        "dre": "BT",
        "tipo_gestao": "Terceirizada",
        "tipo_unidade": "DIRETA",
        "codigo_escola": "12345678",
        "nome_unidade": "Uma Unidade",
        "codigo_eol_aluno": "123456",
        "nome_aluno": "Anderson Marques",
        "data_nascimento": "11/01/1989",
        "data_ocorrencia": "11/01/1989",
        "codigo_diagnostico": "Aluno Alérgico",
        "protocolo_dieta": "Alérgico",
        "codigo_categoria_dieta": "A",
    }
    with pytest.raises(ValueError):
        ArquivoCargaDietaEspecialSchema(**dicionario_dados)
