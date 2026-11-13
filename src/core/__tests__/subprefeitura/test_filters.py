from unittest.mock import Mock

import pytest
from django.http import QueryDict
from model_bakery import baker

from src.core.models import Escola, Subprefeitura, TipoUnidadeEscolar
from src.core.subprefeitura.api.filters import SubprefeituraFilter
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


def test_subprefeitura_sem_parametro_mantem_cadastro_completo():
    baker.make("Subprefeitura", nome="NORTE")
    baker.make("Subprefeitura", nome="SUL")

    filtro = SubprefeituraFilter(data=QueryDict(), queryset=Subprefeitura.objects.all())

    assert {"NORTE", "SUL"} <= set(filtro.qs.values_list("nome", flat=True))


def test_subprefeitura_filtra_uma_e_varias_dres_sem_duplicar():
    dre_a = baker.make("DiretoriaRegional", nome="DRE A")
    dre_b = baker.make("DiretoriaRegional", nome="DRE B")
    dre_c = baker.make("DiretoriaRegional", nome="DRE C")
    compartilhada = baker.make("Subprefeitura", nome="COMPARTILHADA")
    compartilhada.diretoria_regional.add(dre_a, dre_b)
    somente_c = baker.make("Subprefeitura", nome="SOMENTE C")
    somente_c.diretoria_regional.add(dre_c)

    data_uma = QueryDict(mutable=True)
    data_uma.setlist("diretoria_regional__uuid", [str(dre_a.uuid)])
    filtro_uma = SubprefeituraFilter(
        data=data_uma, queryset=Subprefeitura.objects.all()
    )
    assert list(filtro_uma.qs.values_list("uuid", flat=True)) == [compartilhada.uuid]

    data_varias = QueryDict(mutable=True)
    data_varias.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(dre_a.uuid), str(dre_b.uuid)],
    )
    filtro_varias = SubprefeituraFilter(
        data=data_varias, queryset=Subprefeitura.objects.all()
    )
    assert list(filtro_varias.qs.values_list("uuid", flat=True)) == [compartilhada.uuid]


def test_subprefeitura_dre_nao_enxerga_fora_do_escopo():
    dre = baker.make("DiretoriaRegional", nome="DRE USUARIO")
    outra = baker.make("DiretoriaRegional", nome="DRE ALHEIA")
    da_dre = baker.make("Subprefeitura", nome="DA DRE")
    da_dre.diretoria_regional.add(dre)
    alheia = baker.make("Subprefeitura", nome="ALHEIA")
    alheia.diretoria_regional.add(outra)
    request = Mock()
    request.user.is_authenticated = True
    request.user.vinculo_atual.instituicao = dre
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(dre.uuid), str(outra.uuid)],
    )

    filtro = SubprefeituraFilter(
        data=data, queryset=Subprefeitura.objects.all(), request=request
    )

    assert list(filtro.qs.values_list("uuid", flat=True)) == [da_dre.uuid]
