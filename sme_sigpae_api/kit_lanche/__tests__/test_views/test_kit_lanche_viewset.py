import uuid

import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import (
    PEDIDOS_CODAE,
    PEDIDOS_DRE,
    SEM_FILTRO,
)
from sme_sigpae_api.escola.models import Lote, TipoUnidadeEscolar

pytestmark = pytest.mark.django_db


def test_list(
    client_autenticado_da_escola,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
):
    edital = edital_factory.create(numero="78/SME/2016")
    edital_2 = edital_factory.create(numero="31/SME/2022")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche_factory.create(
        edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )
    kit_lanche_factory.create(
        edital=edital_2, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )

    response = client_autenticado_da_escola.get("/kit-lanches/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_list_escola_cemei(
    client_autenticado_da_escola,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    tipo_unidade_escolar_factory,
):
    escola.tipo_unidade.iniciais = "CEMEI"
    escola.tipo_unidade.save()
    tipo_unidade_cei_diret = tipo_unidade_escolar_factory.create(iniciais="CEI DIRET")

    edital = edital_factory.create(numero="78/SME/2016")
    edital_2 = edital_factory.create(numero="31/SME/2022")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche_factory.create(
        edital=edital,
        tipos_unidades=TipoUnidadeEscolar.objects.filter(id=tipo_unidade_cei_diret.id),
    )
    kit_lanche_factory.create(
        edital=edital_2, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )

    response = client_autenticado_da_escola.get("/kit-lanches/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


def test_valida_nome_kit_lanche(
    client_autenticado_da_escola,
    kit_lanche_factory,
    contrato_factory,
    edital_factory,
    escola,
):
    edital = edital_factory.create(numero="78/SME/2016")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche_factory.create(
        nome="KIT_1", edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )

    url = (
        f"/kit-lanches/nome-existe/"
        f"?nome=KIT_1"
        f"&edital={str(edital.uuid)}"
        f"&tipos_unidades[]={str(escola.tipo_unidade.uuid)}"
        f"&uuid={str(uuid.uuid4())}"
    )

    response = client_autenticado_da_escola.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "detail": "Esse nome de kit lanche já existe para o edital e tipos de unidades selecionados"
    }


def test_valida_nome_kit_lanche_404_mesmo_uuid(
    client_autenticado_da_escola,
    kit_lanche_factory,
    contrato_factory,
    edital_factory,
    escola,
):
    edital = edital_factory.create(numero="78/SME/2016")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche = kit_lanche_factory.create(
        nome="KIT_1", edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )

    url = (
        f"/kit-lanches/nome-existe/"
        f"?nome=KIT_1"
        f"&edital={str(edital.uuid)}"
        f"&tipos_unidades[]={str(escola.tipo_unidade.uuid)}"
        f"&uuid={kit_lanche.uuid}"
    )

    response = client_autenticado_da_escola.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Nome válido"}


def test_valida_nome_kit_lanche_404_kit_lanche_does_not_exist(
    client_autenticado_da_escola,
    kit_lanche_factory,
    contrato_factory,
    edital_factory,
    escola,
):
    edital = edital_factory.create(numero="78/SME/2016")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    kit_lanche = kit_lanche_factory.create(
        nome="KIT_1", edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )

    url = (
        f"/kit-lanches/nome-existe/"
        f"?nome=KIT_2"
        f"&edital={str(edital.uuid)}"
        f"&tipos_unidades[]={str(escola.tipo_unidade.uuid)}"
        f"&uuid={kit_lanche.uuid}"
    )

    response = client_autenticado_da_escola.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Nome válido"}


def test_url_solicitacao_kit_lanche_cemei_codae(client_autenticado_da_codae):
    response = client_autenticado_da_codae.get(
        f"/solicitacao-kit-lanche-cemei/{PEDIDOS_CODAE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_url_solicitacao_kit_lanche_cemei_dre(client_autenticado_da_dre):
    response = client_autenticado_da_dre.get(
        f"/solicitacao-kit-lanche-cemei/{PEDIDOS_DRE}/{SEM_FILTRO}/"
    )
    data = response.json()
    assert "previous" not in data
    assert "next" not in data
    assert "count" not in data
    assert "results" in data
    assert isinstance(data["results"], list)
