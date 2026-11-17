import pytest
from model_bakery import baker

from src.core.diretoria_regional.api.filters import DiretoriaRegionalFilter
from src.core.models import Escola, TipoUnidadeEscolar
from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR

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


def test_diretoria_regional_filter(diretoria_regional):
    filtro_dre = DiretoriaRegionalFilter(
        data={"dre": diretoria_regional.uuid},
        queryset=Escola.objects.all().prefetch_related("diretoria_regional"),
    )
    assert filtro_dre.qs.count() == 3
    for escola in filtro_dre.qs:
        assert escola.diretoria_regional.nome == diretoria_regional.nome
        assert str(escola.diretoria_regional.uuid) == diretoria_regional.uuid
