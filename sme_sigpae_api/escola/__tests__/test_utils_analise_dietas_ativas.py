import json
import tempfile
import pytest
from sme_sigpae_api.escola.utils_analise_dietas_ativas import gera_dict_codigos_escolas, get_codigo_eol_aluno, get_codigo_eol_escola, get_escolas_json, dict_codigos_escolas, retorna_codigo_eol_escolas_nao_identificadas


def test_get_escolas_json():
    escolas_data = {
        "escolas": [
            {"id": 1, "nome": "Escola A"},
            {"id": 2, "nome": "Escola B"}
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=True) as temp_file:
        json.dump(escolas_data, temp_file)
        temp_file.seek(0) 
        result = get_escolas_json(temp_file.name)
        assert result == escolas_data

def test_gera_dict_codigos_escolas():
    items_codigos_escolas = [
        {"CÓDIGO UNIDADE": 123, "CODIGO EOL": 456},
        {"CÓDIGO UNIDADE": 789, "CODIGO EOL": 101112},
        {"CÓDIGO UNIDADE": 345, "CODIGO EOL": 6789},
    ]
    dict_codigos_escolas.clear()
    
    gera_dict_codigos_escolas(items_codigos_escolas)
    assert dict_codigos_escolas ==  {
        "123": "456",
        "789": "101112",
        "345": "6789",
    }
    
def test_get_codigo_eol_escola():
    assert get_codigo_eol_escola("123") == "000123" 
    assert get_codigo_eol_escola(" 45 ") == "000045"  
    assert get_codigo_eol_escola("123456") == "123456"  
    assert get_codigo_eol_escola("1234567") == "1234567" 
    assert get_codigo_eol_escola("") == "000000" 

def test_get_codigo_eol_aluno():
    assert get_codigo_eol_aluno(1234) == "0001234" 
    assert get_codigo_eol_aluno(" 789 ") == "0000789"  
    assert get_codigo_eol_aluno("1234567") == "1234567" 
    assert get_codigo_eol_aluno("12345678") == "12345678"
    assert get_codigo_eol_aluno("") == "0000000"
    
    
def test_retorna_codigo_eol_escolas_nao_identificadas_exception():
    items_codigos_escolas = [
        {"CodEscola": "123", "CODIGO EOL": 456},
        {"CodEscola": "789", "CODIGO EOL": 101112},
        {"CodEscola": "345", "CODIGO EOL": 6789},
    ]
    
    with pytest.raises(Exception):
        retorna_codigo_eol_escolas_nao_identificadas(items_codigos_escolas)
