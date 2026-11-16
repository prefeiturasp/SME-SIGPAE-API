import pytest
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from rangefilter.filters import DateRangeFilter

from src.dados_comuns.constants import StringsSearchHelpText
from src.medicao_inicial.admin import DiaSobremesaDoceAdmin, MedicaoFinalAdmin
from src.medicao_inicial.models import DiaSobremesaDoce, MedicaoFinal

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
    assert (
        admin_instance.search_help_text
        == StringsSearchHelpText.PESQUISE_POR_INICIAIS_OU_NOME_DO_TIPO_DE_UNIDADE_NUMERO_DO_EDITAL_TIPO_DE_SOBREMESA.value
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


@pytest.fixture
def medicao_final_admin():
    return MedicaoFinalAdmin(model=MedicaoFinal, admin_site=AdminSite())


def test_medicao_final_admin_registrado():
    assert isinstance(admin.site._registry[MedicaoFinal], MedicaoFinalAdmin)


def test_medicao_final_admin_list_display(medicao_final_admin):
    assert medicao_final_admin.list_display == (
        "relatorio_financeiro",
        "rf_responsavel_conferencia",
        "nome_responsavel_conferencia",
        "numero_processo_pagamento",
        "gerado_por",
        "criado_em",
    )


def test_medicao_final_admin_search_fields(medicao_final_admin):
    assert medicao_final_admin.search_fields == (
        "rf_responsavel_conferencia",
        "nome_responsavel_conferencia",
        "numero_processo_pagamento",
        "relatorio_financeiro__lote__nome",
    )
    assert (
        medicao_final_admin.search_help_text
        == StringsSearchHelpText.PESQUISE_POR_RF_OU_NOME_DO_RESPONSAVEL_PROCESSO_DE_PAGAMENTO_OU_NOME_DO_LOTE.value
    )


def test_medicao_final_admin_list_filter(medicao_final_admin):
    assert medicao_final_admin.list_filter == (
        ("criado_em", DateRangeFilter),
        "relatorio_financeiro__mes",
        "relatorio_financeiro__ano",
        "relatorio_financeiro__lote",
    )


def test_medicao_final_admin_campos_somente_leitura(medicao_final_admin):
    assert medicao_final_admin.readonly_fields == ("uuid", "criado_em", "alterado_em")
    assert medicao_final_admin.raw_id_fields == ("relatorio_financeiro", "gerado_por")
