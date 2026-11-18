import pytest
from django.http import QueryDict
from model_bakery import baker

from src.core.escola.api.filters import EscolaParaFiltrosFilter
from src.core.models import Escola, TipoUnidadeEscolar
from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR, PayloadVariaveis

pytestmark = pytest.mark.django_db


@pytest.fixture
def escolas_para_filtros(tipo_gestao):
    dre = baker.make("DiretoriaRegional", nome="DRE FILTROS")
    tipo_emef = baker.make(
        TipoUnidadeEscolar, iniciais=TIPOS_UNIDADE_ESCOLAR.EMEF.value
    )
    tipo_cei = baker.make(TipoUnidadeEscolar, iniciais=TIPOS_UNIDADE_ESCOLAR.CEI.value)
    lote_a = baker.make("Lote", nome="LOTE A")
    lote_b = baker.make("Lote", nome="LOTE B")

    escola_emef_lote_a = baker.make(
        Escola,
        codigo_eol="000001",
        diretoria_regional=dre,
        tipo_unidade=tipo_emef,
        lote=lote_a,
        tipo_gestao=tipo_gestao,
    )
    escola_emef_lote_b = baker.make(
        Escola,
        codigo_eol="000002",
        diretoria_regional=dre,
        tipo_unidade=tipo_emef,
        lote=lote_b,
        tipo_gestao=tipo_gestao,
    )
    escola_cei_lote_a = baker.make(
        Escola,
        codigo_eol="000003",
        diretoria_regional=dre,
        tipo_unidade=tipo_cei,
        lote=lote_a,
        tipo_gestao=tipo_gestao,
    )

    return {
        "dre": dre,
        "tipo_emef": tipo_emef,
        "tipo_cei": tipo_cei,
        "lote_a": lote_a,
        "lote_b": lote_b,
        "escola_emef_lote_a": escola_emef_lote_a,
        "escola_emef_lote_b": escola_emef_lote_b,
        "escola_cei_lote_a": escola_cei_lote_a,
    }


def test_escola_para_filtros_tipo_unidade_lista(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        [str(escolas_para_filtros["tipo_emef"].uuid)],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 2
    assert set(filtro.qs.values_list("tipo_unidade__uuid", flat=True)) == {
        escolas_para_filtros["tipo_emef"].uuid
    }


def test_escola_para_filtros_tipo_unidade_lista_multiplos(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        [
            str(escolas_para_filtros["tipo_emef"].uuid),
            str(escolas_para_filtros["tipo_cei"].uuid),
        ],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3


def test_escola_para_filtros_lote_lista(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.LOTE_UUID.value, [str(escolas_para_filtros["lote_a"].uuid)]
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 2
    assert set(filtro.qs.values_list("lote__uuid", flat=True)) == {
        escolas_para_filtros["lote_a"].uuid
    }


def test_escola_para_filtros_excluir_tipo_unidade(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.EXCLUIR_TIPO_UNIDADE_UUID.value,
        [str(escolas_para_filtros["tipo_emef"].uuid)],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escolas_para_filtros["escola_cei_lote_a"].uuid


def test_escola_para_filtros_tipo_unidade_in_existente(escolas_para_filtros):
    data = QueryDict(f"tipo_unidade__uuid__in={escolas_para_filtros['tipo_cei'].uuid}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escolas_para_filtros["escola_cei_lote_a"].uuid


def test_escola_para_filtros_lote_exact_existente(escolas_para_filtros):
    data = QueryDict(f"lote__uuid={escolas_para_filtros['lote_b'].uuid}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escolas_para_filtros["escola_emef_lote_b"].uuid


def test_escola_para_filtros_diretoria_regional_existente(escolas_para_filtros):
    data = QueryDict(f"diretoria_regional__uuid={escolas_para_filtros['dre'].uuid}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3


def test_escola_para_filtros_tipo_gestao_existente(escolas_para_filtros, tipo_gestao):
    data = QueryDict(f"tipo_gestao__nome={tipo_gestao.nome}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3


def test_escola_para_filtros_diretoria_regional_lista(escolas_para_filtros):
    outra_dre = baker.make("DiretoriaRegional", nome="OUTRA DRE")
    baker.make(
        Escola,
        codigo_eol="000004",
        diretoria_regional=outra_dre,
        tipo_unidade=escolas_para_filtros["tipo_emef"],
        lote=escolas_para_filtros["lote_a"],
        tipo_gestao=escolas_para_filtros["escola_emef_lote_a"].tipo_gestao,
    )
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(escolas_para_filtros["dre"].uuid)],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3
    assert set(filtro.qs.values_list("diretoria_regional__uuid", flat=True)) == {
        escolas_para_filtros["dre"].uuid
    }


def test_escola_para_filtros_subprefeitura_lista(escolas_para_filtros):
    subprefeitura = baker.make("Subprefeitura", nome="CENTRO")
    escola = escolas_para_filtros["escola_emef_lote_a"]
    escola.subprefeitura = subprefeitura
    escola.save()
    data = QueryDict(mutable=True)
    data.setlist(PayloadVariaveis.SUBPREFEITURA_UUID.value, [str(subprefeitura.uuid)])

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escola.uuid


def test_escola_para_filtros_combina_dre_lote_subprefeitura_e_tipo(
    escolas_para_filtros,
):
    subprefeitura = baker.make("Subprefeitura", nome="SUL")
    escola = escolas_para_filtros["escola_cei_lote_a"]
    escola.subprefeitura = subprefeitura
    escola.save()
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(escolas_para_filtros["dre"].uuid)],
    )
    data.setlist(
        PayloadVariaveis.LOTE_UUID.value, [str(escolas_para_filtros["lote_a"].uuid)]
    )
    data.setlist(PayloadVariaveis.SUBPREFEITURA_UUID.value, [str(subprefeitura.uuid)])
    data.setlist(
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        [str(escolas_para_filtros["tipo_cei"].uuid)],
    )
    data["tipo_gestao__nome"] = escolas_para_filtros[
        "escola_cei_lote_a"
    ].tipo_gestao.nome

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert list(filtro.qs.values_list("uuid", flat=True)) == [escola.uuid]
