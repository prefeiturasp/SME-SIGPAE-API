import pytest
from django.contrib import admin

from ...carga_dados.admin import PlanilhaAtualizacaoTipoGestaoEscolaAdmin
from ...models import (
    PlanilhaAtualizacaoTipoGestaoEscola,
    PlanilhaEscolaDeParaCodigoEolCodigoCoade,
)

pytestmark = pytest.mark.django_db


def test_instance_model_planilha_de_para_codigo_eol_codigo_codae(
    planilha_de_para_eol_codae,
):
    model = planilha_de_para_eol_codae
    assert isinstance(model, PlanilhaEscolaDeParaCodigoEolCodigoCoade)
    assert model.criado_em is not None
    assert model.planilha is not None
    assert model.codigos_codae_vinculados is not None


def test_meta_modelo_planilha_de_para_codigo_eol_codigo_codae(
    planilha_de_para_eol_codae,
):
    assert (
        planilha_de_para_eol_codae._meta.verbose_name
        == "Planilha De-Para: Código EOL x Código Codae"
    )
    assert (
        planilha_de_para_eol_codae._meta.verbose_name_plural
        == "Planilhas De-Para: Código EOL x Código Codae"
    )


def test_instance_model_planilha_atualizacao_tipo_gestao_escolas(
    planilha_atualizacao_tipo_gestao,
):
    model = planilha_atualizacao_tipo_gestao
    assert isinstance(model, PlanilhaAtualizacaoTipoGestaoEscola)
    assert model.criado_em is not None
    assert model.conteudo is not None
    assert model.status is not None


def test_meta_modelo_planilha_atualizacao_tipo_gestao_escolas(
    planilha_atualizacao_tipo_gestao,
):
    assert (
        planilha_atualizacao_tipo_gestao._meta.verbose_name
        == "Planilha Atualização Tipo Gestão Escola"
    )
    assert (
        planilha_atualizacao_tipo_gestao._meta.verbose_name_plural
        == "Planilha Atualização Tipo Gestão Escola"
    )


def test_admin_planilha_atualizacao_tipo_gestao_escolas():
    model_admin = PlanilhaAtualizacaoTipoGestaoEscolaAdmin(
        PlanilhaAtualizacaoTipoGestaoEscola, admin.site
    )
    # pylint: disable=W0212
    assert admin.site._registry[PlanilhaAtualizacaoTipoGestaoEscola]
    assert model_admin.list_display == ("__str__", "criado_em", "status")
    assert (
        model_admin.change_list_template
        == "admin/escola/importacao_tipos_de_gestao_das_escolas.html"
    )
    assert model_admin.actions == ("processa_planilha",)
