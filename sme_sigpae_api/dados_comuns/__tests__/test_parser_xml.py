from sme_sigpae_api.dados_comuns.parser_xml import ListXMLParser, check_and_returns_data_from_element, check_xml_list, returns_data_from_children
import xml.etree.ElementTree as ET

def test_xml_convert():
    parser = ListXMLParser()
    xml_data ="""<root>
        <name>Maria Antônia</name>
        <age>10</age>
    </root>"""
    element = ET.fromstring(xml_data)
    result = parser._xml_convert(element)
    assert result =={"name": "Maria Antônia", "age": 10}

    xml_data = """<root>
        <item>Paulo Antônio</item>
        <item>Maria Antônia</item>
    </root>"""
    element = ET.fromstring(xml_data)
    result = parser._xml_convert(element)
    assert result ==  ["Paulo Antônio", "Maria Antônia"]

def test_check_and_returns_data_from_element():
    parser = ListXMLParser()
    xml_data ="""<root>
        <name>Maria Antônia</name>
        <age>10</age>
    </root>"""
    element = ET.fromstring(xml_data)
    result = check_and_returns_data_from_element(parser, element)
    assert result =={"name": "Maria Antônia", "age": 10}
    
    
    xml_data = """<root>
        <item>Paulo Antônio</item>
        <item>Maria Antônia</item>
    </root>"""
    element = ET.fromstring(xml_data)
    result = check_and_returns_data_from_element(parser, element)
    assert result ==  ["Paulo Antônio", "Maria Antônia"]
    
def test_check_xml_list():
    parser = ListXMLParser()
    xml_data ="""<root>
        <name>Maria Antônia</name>
        <age>10</age>
    </root>"""
    element = ET.fromstring(xml_data)
    result = check_xml_list(element)
    assert result is False
    
    
    xml_data = """<root>
        <item>Paulo Antônio</item>
        <item>Maria Antônia</item>
    </root>"""
    element = ET.fromstring(xml_data)
    result = check_xml_list(element)
    assert result is True
    
def test_returns_data_from_children():
    parser = ListXMLParser()
    xml_data ="""<root>
        <name>Maria Antônia</name>
        <age>10</age>
    </root>"""
    element = ET.fromstring(xml_data)
    result = returns_data_from_children(parser, element, True)
    assert result == ['Maria Antônia', 10]
    
    result = returns_data_from_children(parser, element, False)
    assert result == {'age': 10, 'name': 'Maria Antônia'}
    
    xml_data = """<root>
        <item>Maria Antônia</item>
    </root>"""
    element = ET.fromstring(xml_data)
    result = returns_data_from_children(parser, element, True)
    assert result == ['Maria Antônia']
    
    result = returns_data_from_children(parser, element, False)
    assert result ==  {'item': 'Maria Antônia'}