import pytest
from django.contrib.admin.sites import AdminSite
from rangefilter.filters import DateRangeFilter

from src.medicao_inicial.admin import DiaSobremesaDoceAdmin
from src.medicao_inicial.models import DiaSobremesaDoce

pytestmark = pytest.mark.django_db


def test_dia_sobremesa_doce_admin_list_display():
    admin_instance = DiaSobremesaDoceAdmin(
        model=DiaSobremesaDoce, admin_site=AdminSite()
    )
    assert admin_instance.list_display == (
        "data",
        "tipo_unidade",
        "edital",
        "tipo",
        "criado_em",
        "criado_por",
    )


def test_dia_sobremesa_doce_admin_search_fields():
    admin_instance = DiaSobremesaDoceAdmin(
        model=DiaSobremesaDoce, admin_site=AdminSite()
    )
    assert admin_instance.search_fields == (
        "tipo_unidade__iniciais",
        "tipo_unidade__nome",
        "edital__numero",
        "tipo__nome",
    )


def test_dia_sobremesa_doce_admin_search_help_text():
    admin_instance = DiaSobremesaDoceAdmin(
        model=DiaSobremesaDoce, admin_site=AdminSite()
    )
    assert admin_instance.search_help_text == (
        "Pesquise por: iniciais ou nome do tipo de unidade, "
        "número do edital, tipo de sobremesa"
    )


def test_dia_sobremesa_doce_admin_list_filter():
    admin_instance = DiaSobremesaDoceAdmin(
        model=DiaSobremesaDoce, admin_site=AdminSite()
    )
    assert admin_instance.list_filter == (
        ("data", DateRangeFilter),
        "tipo_unidade",
        "edital__numero",
        "tipo",
    )
