import datetime
from unittest.mock import Mock, patch

import pytest
from django.contrib.admin.sites import AdminSite
from model_bakery import baker

from src.escola.dias_letivos.admin import (
    DIAS_SEMANA,
    DiaLetivoSIGPAEAdmin,
    DiaSemanaFilter,
)
from src.escola.dias_letivos.models import DiaLetivoSIGPAE

pytestmark = pytest.mark.django_db


def test_dia_semana_filter_lookups():
    filter_instance = DiaSemanaFilter(Mock(), {}, DiaLetivoSIGPAE, DiaLetivoSIGPAEAdmin)
    assert filter_instance.lookups(Mock(), Mock()) == DIAS_SEMANA


def test_dia_semana_filter_queryset_with_value():
    baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 21))

    filter_instance = DiaSemanaFilter(
        Mock(),
        {"dia_semana": ["2"]},
        DiaLetivoSIGPAE,
        DiaLetivoSIGPAEAdmin,
    )
    queryset = filter_instance.queryset(Mock(), DiaLetivoSIGPAE.objects.all())
    assert queryset.count() == 1

    filter_instance_sunday = DiaSemanaFilter(
        Mock(),
        {"dia_semana": ["1"]},
        DiaLetivoSIGPAE,
        DiaLetivoSIGPAEAdmin,
    )
    queryset_sunday = filter_instance_sunday.queryset(
        Mock(), DiaLetivoSIGPAE.objects.all()
    )
    assert queryset_sunday.count() == 1


def test_dia_semana_filter_queryset_without_value():
    baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 21))

    filter_instance = DiaSemanaFilter(Mock(), {}, DiaLetivoSIGPAE, DiaLetivoSIGPAEAdmin)
    queryset = filter_instance.queryset(Mock(), DiaLetivoSIGPAE.objects.all())
    assert queryset.count() == 2


def test_dia_semana_filter_title_and_parameter_name():
    filter_instance = DiaSemanaFilter(Mock(), {}, DiaLetivoSIGPAE, DiaLetivoSIGPAEAdmin)
    assert filter_instance.title == "Dia da semana"
    assert filter_instance.parameter_name == "dia_semana"


def test_dia_letivo_admin_list_display():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    assert admin_instance.list_display == (
        "data",
        "get_dia_semana",
        "get_periodos_escolares",
        "get_lotes",
        "get_tipos_unidade",
        "get_escolas",
    )


def test_dia_letivo_admin_search_fields():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    assert admin_instance.search_fields == ("escolas__nome", "escolas__codigo_eol")


def test_dia_letivo_admin_search_help_text():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    assert (
        admin_instance.search_help_text
        == "Pesquise por: nome da escola ou código eol da escola"
    )


def test_dia_letivo_admin_filters():
    from rangefilter.filters import DateRangeFilter

    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    filters = admin_instance.list_filter
    assert filters[0] == ("data", DateRangeFilter)
    assert filters[1] == "periodos_escolares"
    assert filters[2] == "lotes"
    assert filters[3] == DiaSemanaFilter


def test_dia_letivo_admin_ordering():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    assert admin_instance.ordering == ("-data",)


def test_dia_letivo_admin_readonly_fields():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    assert admin_instance.readonly_fields == (
        "uuid",
        "criado_em",
        "criado_por",
        "alterado_em",
    )


def test_get_dia_semana():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    dia = baker.prepare(DiaLetivoSIGPAE)

    dia.data = datetime.date(2026, 6, 22)
    assert admin_instance.get_dia_semana(dia) == "Segunda"

    dia.data = datetime.date(2026, 6, 23)
    assert admin_instance.get_dia_semana(dia) == "Terça"

    dia.data = datetime.date(2026, 6, 24)
    assert admin_instance.get_dia_semana(dia) == "Quarta"

    dia.data = datetime.date(2026, 6, 25)
    assert admin_instance.get_dia_semana(dia) == "Quinta"

    dia.data = datetime.date(2026, 6, 26)
    assert admin_instance.get_dia_semana(dia) == "Sexta"

    dia.data = datetime.date(2026, 6, 27)
    assert admin_instance.get_dia_semana(dia) == "Sábado"

    dia.data = datetime.date(2026, 6, 28)
    assert admin_instance.get_dia_semana(dia) == "Domingo"


def test_get_dia_semana_display_decorator():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    assert admin_instance.get_dia_semana.short_description == "Dia da semana"


def test_get_periodos_escolares():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    periodo1 = baker.make("escola.PeriodoEscolar", nome="Manhã")
    periodo2 = baker.make("escola.PeriodoEscolar", nome="Tarde")

    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    dia.periodos_escolares.set([periodo1, periodo2])

    assert set(admin_instance.get_periodos_escolares(dia).split(", ")) == {
        "Manhã",
        "Tarde",
    }
    assert (
        admin_instance.get_periodos_escolares.short_description == "Períodos escolares"
    )


def test_get_periodos_escolares_empty():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    assert admin_instance.get_periodos_escolares(dia) == ""


def test_get_lotes():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    lote1 = baker.make("escola.Lote", nome="Lote A")
    lote2 = baker.make("escola.Lote", nome="Lote B")

    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    dia.lotes.set([lote1, lote2])

    assert set(admin_instance.get_lotes(dia).split(", ")) == {"Lote A", "Lote B"}
    assert admin_instance.get_lotes.short_description == "Lotes"


def test_get_lotes_empty():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    assert admin_instance.get_lotes(dia) == ""


def test_get_tipos_unidade():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    tipo1 = baker.make("escola.TipoUnidadeEscolar", iniciais="EMEF")
    tipo2 = baker.make("escola.TipoUnidadeEscolar", iniciais="CEI")

    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    dia.tipos_unidade_escolar.set([tipo1, tipo2])

    assert set(admin_instance.get_tipos_unidade(dia).split(", ")) == {"EMEF", "CEI"}
    assert admin_instance.get_tipos_unidade.short_description == "Tipos de unidade"


def test_get_tipos_unidade_empty():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    assert admin_instance.get_tipos_unidade(dia) == ""


def test_get_escolas():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    escola1 = baker.make("escola.Escola", nome="EMEF A")
    escola2 = baker.make("escola.Escola", nome="EMEF B")

    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    dia.escolas.set([escola1, escola2])

    assert set(admin_instance.get_escolas(dia).split(", ")) == {"EMEF A", "EMEF B"}
    assert admin_instance.get_escolas.short_description == "Escolas"


def test_get_escolas_empty():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())
    dia = baker.make(DiaLetivoSIGPAE, data=datetime.date(2026, 6, 22))
    assert admin_instance.get_escolas(dia) == ""


def test_get_queryset_prefetch_related():
    admin_instance = DiaLetivoSIGPAEAdmin(model=DiaLetivoSIGPAE, admin_site=AdminSite())

    mock_queryset = Mock()
    with patch(
        "django.contrib.admin.ModelAdmin.get_queryset", return_value=mock_queryset
    ):
        result = admin_instance.get_queryset(Mock())

    mock_queryset.prefetch_related.assert_called_once_with(
        "periodos_escolares", "lotes", "tipos_unidade_escolar", "escolas"
    )
    assert result == mock_queryset.prefetch_related.return_value
