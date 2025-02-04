from sme_sigpae_api.dados_comuns.parser_xml import (
    check_and_returns_data_from_element,
    check_xml_list,
    returns_data_from_children,
)


def test_xml_convert_retorna_dicionario(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml
    result = parser._xml_convert(xml_dicionario)
    assert result == {
        "Str": "Aluno com alergia a frutos do mar.",
        "age": 10,
        "name": "Maria Antônia",
    }


def test_xml_convert_retona_lista(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml
    result = parser._xml_convert(xml_lista)
    assert result == ["Paulo Antônio", "Maria Antônia"]


def test_check_and_returns_data_from_element_retona_dicionario(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml
    result = check_and_returns_data_from_element(parser, xml_dicionario)
    assert result == {
        "Str": "Aluno com alergia a frutos do mar.",
        "name": "Maria Antônia",
        "age": 10,
    }


def test_check_and_returns_data_from_element_retona_lista(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml
    result = check_and_returns_data_from_element(parser, xml_lista)
    assert result == ["Paulo Antônio", "Maria Antônia"]


def test_check_xml_list_retona_falso(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml
    result = check_xml_list(xml_dicionario)
    assert result is False


def test_check_xml_list_retona_verdadeiro(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml
    result = check_xml_list(xml_lista)
    assert result is True


def test_returns_data_from_children_retorna_lista(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml
    result = returns_data_from_children(parser, xml_dicionario, True)
    assert result == ["Maria Antônia", 10, "Aluno com alergia a frutos do mar."]

    result = returns_data_from_children(parser, xml_lista, True)
    assert result == ["Paulo Antônio", "Maria Antônia"]


def test_returns_data_from_children_retorna_dicionario(parser_xml):
    parser, xml_dicionario, xml_lista = parser_xml

    result = returns_data_from_children(parser, xml_dicionario, False)
    assert result == {
        "Str": "Aluno com alergia a frutos do mar.",
        "age": 10,
        "name": "Maria Antônia",
    }

    result = returns_data_from_children(parser, xml_lista, False)
    assert result == {"item": "Maria Antônia"}
