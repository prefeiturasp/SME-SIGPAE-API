import pytest

pytestmark = pytest.mark.django_db


def test_label_tipos_alimentacao_retona_dois_tipos_alimentacao(label_tipos_alimentacao):
    modelo, tipo_vegetariano, tipo_vegano = label_tipos_alimentacao
    modelo.tipos_alimentacao.add(tipo_vegetariano, tipo_vegano)
    assert "Vegetariano" in modelo.label
    assert "Vegano" in modelo.label


def test_label_property_retona_um_tipo_alimentacao(label_tipos_alimentacao):
    modelo, tipo_vegetariano, _ = label_tipos_alimentacao
    modelo.tipos_alimentacao.add(tipo_vegetariano)
    assert modelo.label == "Vegetariano"


def test_label_property_retona_nenhum_tipo(label_tipos_alimentacao):
    modelo, _, _ = label_tipos_alimentacao
    assert modelo.label == ""
