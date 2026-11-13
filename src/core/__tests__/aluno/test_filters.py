from unittest.mock import Mock

import pytest
from model_bakery import baker

from src.core.aluno.api.filters import AlunoFilter
from src.core.models import Aluno, Escola, TipoUnidadeEscolar
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


def test_aluno_filter_codigo_eol(aluno):
    filtro_codigo_eol = AlunoFilter(
        data={"codigo_eol": aluno.codigo_eol}, queryset=Aluno.objects.all()
    )
    assert filtro_codigo_eol.qs.count() == 1
    assert filtro_codigo_eol.qs[0].nome == aluno.nome
    assert filtro_codigo_eol.qs[0].codigo_eol == aluno.codigo_eol

    filtro = AlunoFilter(data={"codigo_eol": aluno.nome}, queryset=Aluno.objects.all())
    assert filtro.qs.count() == 0


def test_aluno_filter_dre(aluno):
    diretoria_regional = aluno.escola.diretoria_regional

    filtro_dre = AlunoFilter(
        data={"dre": diretoria_regional.uuid}, queryset=Aluno.objects.all()
    )
    assert filtro_dre.qs.count() == 1
    assert filtro_dre.qs[0].nome == aluno.nome
    assert (
        str(filtro_dre.qs[0].escola.diretoria_regional.uuid) == diretoria_regional.uuid
    )

    filtro = AlunoFilter(
        data={"dre": diretoria_regional.nome}, queryset=Aluno.objects.all()
    )
    assert filtro.qs.count() == 0


def test_aluno_filter_dieta_especial(dieta_codae_autorizou, dieta_cancelada):
    assert dieta_codae_autorizou.aluno == dieta_cancelada.aluno
    aluno = dieta_cancelada.aluno

    filtro_nao_tem_dieta_especial = AlunoFilter(
        data={"nao_tem_dieta_especial": True}, queryset=Aluno.objects.all()
    )
    assert filtro_nao_tem_dieta_especial.qs.count() == 0

    filtro_nao_tem_dieta_especial = AlunoFilter(
        data={"nao_tem_dieta_especial": False}, queryset=Aluno.objects.all()
    )
    assert filtro_nao_tem_dieta_especial.qs.count() == 2
    aluno_dieta = filtro_nao_tem_dieta_especial.qs.distinct()[0]
    assert aluno_dieta.dietas_especiais.count() == 2
    for dieta in aluno_dieta.dietas_especiais.all():
        assert dieta.aluno.nome == aluno.nome


def test_aluno_filter_periodo_escola(aluno):
    periodo_escolar = aluno.periodo_escolar

    filtro_periodo_escola = AlunoFilter(
        data={"periodo_escolar_nome": "TARDE"}, queryset=Aluno.objects.all()
    )
    assert filtro_periodo_escola.qs.count() == 0

    filtro_periodo_escola = AlunoFilter(
        data={"periodo_escolar_nome": periodo_escolar.nome},
        queryset=Aluno.objects.all(),
    )
    assert filtro_periodo_escola.qs.count() == 1
    assert filtro_periodo_escola.qs[0].nome == aluno.nome


def test_aluno_filter_escola_egressos_false(aluno):
    escola = aluno.escola

    mock_request = Mock()
    mock_request.query_params = {"inclui_alunos_egressos": "false"}
    filtro_escola = AlunoFilter(
        data={"escola": escola.uuid}, queryset=Aluno.objects.all(), request=mock_request
    )
    assert filtro_escola.qs.count() == 1
    assert filtro_escola.qs[0].nome == aluno.nome
    assert filtro_escola.qs[0].escola == escola


def test_aluno_filter_escola_egressos_true(aluno):
    escola = aluno.escola
    mock_request = Mock()
    mock_request.query_params = {
        "inclui_alunos_egressos": "true",
        "mes": "5",
        "ano": "2023",
    }
    filtro_escola = AlunoFilter(
        data={"escola": escola.uuid}, queryset=Aluno.objects.all(), request=mock_request
    )
    assert filtro_escola.qs.count() == 0
