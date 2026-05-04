from rest_framework_xml.parsers import XMLParser


def check_xml_list(element):
    child_tags_elements = [child.tag for child in element]
    child_tags_set = set(child_tags_elements)
    bigger_than_one = len(element) > 1
    less_than_or_equal_to_one = len(child_tags_set) <= 1
    return bigger_than_one and less_than_or_equal_to_one


def returns_data_from_children(self, children, is_list):
    if not is_list:
        data = {}
        for child in children:
            data[child.tag] = self._xml_convert(child)
    else:
        data = []
        for child in children:
            data.append(self._xml_convert(child))
    return data


def check_and_returns_data_from_element(self, element):
    children = list(element)
    is_list = check_xml_list(element)
    return returns_data_from_children(self, children, is_list)


class ListXMLParser(XMLParser):
    def _xml_convert(self, element):
        children = list(element)
        if len(children) == 0:
            if "Str" in element.tag:
                return element.text
            return self._type_convert(element.text)
        else:
            data = check_and_returns_data_from_element(self, element)
        return data
