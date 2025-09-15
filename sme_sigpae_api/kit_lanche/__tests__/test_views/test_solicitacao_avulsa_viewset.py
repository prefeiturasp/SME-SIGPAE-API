import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import (
    PEDIDOS_CODAE,
    PEDIDOS_DRE,
    SEM_FILTRO,
)
from sme_sigpae_api.escola.models import Lote, TipoUnidadeEscolar
from sme_sigpae_api.perfil.models import Usuario

pytestmark = pytest.mark.django_db


def test_solicitacoes_diretoria_regional(
    client_autenticado_da_dre,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
):
    edital = edital_factory.create(numero="78/SME/2016")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche = kit_lanche_factory.create(
        edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )
    solicitacao_kit_lanche = solicitacao_kit_lanche_factory.create(kits=[kit_lanche])
    solicitacao_kit_lanche_avulsa_factory.create(
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        escola=escola,
        status="DRE_A_VALIDAR",
    )

    response = client_autenticado_da_dre.get(
        f"/solicitacoes-kit-lanche-avulsa/{PEDIDOS_DRE}/{SEM_FILTRO}/?lote={escola.lote.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert len(data["results"]) == 1


def test_solicitacoes_codae(
    client_autenticado_da_codae,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
):
    edital = edital_factory.create(numero="78/SME/2016")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche = kit_lanche_factory.create(
        edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )
    solicitacao_kit_lanche = solicitacao_kit_lanche_factory.create(kits=[kit_lanche])
    solicitacao_kit_lanche_avulsa_factory.create(
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        escola=escola,
        status="DRE_VALIDADO",
    )

    response = client_autenticado_da_codae.get(
        f"/solicitacoes-kit-lanche-avulsa/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
        f"?lote={escola.lote.uuid}&diretoria_regional={escola.diretoria_regional.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert len(data["results"]) == 1


def test_minhas_solicitacoes(
    client_autenticado_da_escola,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
):
    user = Usuario.objects.get(id=client_autenticado_da_escola.session["_auth_user_id"])
    edital = edital_factory.create(numero="78/SME/2016")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche = kit_lanche_factory.create(
        edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )
    solicitacao_kit_lanche = solicitacao_kit_lanche_factory.create(kits=[kit_lanche])
    solicitacao_kit_lanche_avulsa_factory.create(
        criado_por=user,
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        escola=escola,
    )

    response = client_autenticado_da_escola.get(
        f"/solicitacoes-kit-lanche-avulsa/minhas-solicitacoes/"
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_url_solicitacoes_kit_lanche_cei_avulsa_codae(client_autenticado_da_codae):
    response = client_autenticado_da_codae.get(
        f"/solicitacoes-kit-lanche-cei-avulsa/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_solicitacoes_kit_lanche_cei_avulsa_dre(client_autenticado_da_dre):
    response = client_autenticado_da_dre.get(
        f"/solicitacoes-kit-lanche-cei-avulsa/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)
