import datetime

import pytest
from model_bakery import baker
from rest_framework import status

from src.dados_comuns.constants import PEDIDOS_CODAE, PEDIDOS_DRE, SEM_FILTRO
from src.escola.models import Lote, TipoUnidadeEscolar

pytestmark = pytest.mark.django_db


def _setup_kit_lanche(kit_lanche_factory, escola, contrato_factory, edital_factory):
    edital = edital_factory.create(numero="78/SME/2016")
    contrato_factory.create(
        edital=edital, terceirizada=escola.lote.terceirizada, lotes=Lote.objects.all()
    )
    return kit_lanche_factory.create(
        edital=edital, tipos_unidades=TipoUnidadeEscolar.objects.all()
    )


def _cria_pedidos(
    kit_lanche,
    escola,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
    solicitacao_kit_lanche_cei_avulsa_factory,
    status_pedido,
    data,
):
    solicitacao_kit_lanche = solicitacao_kit_lanche_factory.create(
        kits=[kit_lanche], data=data
    )
    solicitacao_kit_lanche_avulsa_factory.create(
        solicitacao_kit_lanche=solicitacao_kit_lanche,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        escola=escola,
        status=status_pedido,
    )
    solicitacao_kit_lanche_cei = solicitacao_kit_lanche_factory.create(
        kits=[kit_lanche], data=data
    )
    solicitacao_kit_lanche_cei_avulsa_factory.create(
        solicitacao_kit_lanche=solicitacao_kit_lanche_cei,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        escola=escola,
        status=status_pedido,
    )
    baker.make(
        "SolicitacaoKitLancheCEMEI",
        escola=escola,
        data=data,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        rastro_terceirizada=escola.lote.terceirizada,
        status=status_pedido,
        local="Parque",
    )


def test_solicitacoes_diretoria_regional_unificado(
    client_autenticado_da_dre,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
    solicitacao_kit_lanche_cei_avulsa_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    kit_lanche = _setup_kit_lanche(
        kit_lanche_factory, escola, contrato_factory, edital_factory
    )
    _cria_pedidos(
        kit_lanche,
        escola,
        solicitacao_kit_lanche_factory,
        solicitacao_kit_lanche_avulsa_factory,
        solicitacao_kit_lanche_cei_avulsa_factory,
        status_pedido="DRE_A_VALIDAR",
        data=data,
    )

    response = client_autenticado_da_dre.get(
        f"/solicitacao-kit-lanche/{PEDIDOS_DRE}/{SEM_FILTRO}/?prazo=REGULAR"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert dados["count"] == 3
    assert len(dados["results"]) == 3
    assert dados["escolas_solicitantes"] == 1
    assert dados["totais"]["PRIORITARIO"] == 0
    assert dados["totais"]["LIMITE"] == 0
    assert dados["totais"]["REGULAR"] == 3


def test_solicitacoes_diretoria_regional_unificado_filtra_prazo(
    client_autenticado_da_dre,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
    solicitacao_kit_lanche_cei_avulsa_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    kit_lanche = _setup_kit_lanche(
        kit_lanche_factory, escola, contrato_factory, edital_factory
    )
    _cria_pedidos(
        kit_lanche,
        escola,
        solicitacao_kit_lanche_factory,
        solicitacao_kit_lanche_avulsa_factory,
        solicitacao_kit_lanche_cei_avulsa_factory,
        status_pedido="DRE_A_VALIDAR",
        data=data,
    )

    response = client_autenticado_da_dre.get(
        f"/solicitacao-kit-lanche/{PEDIDOS_DRE}/{SEM_FILTRO}/?prazo=PRIORITARIO"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0
    assert response.json()["escolas_solicitantes"] == 0


def test_solicitacoes_diretoria_regional_unificado_busca(
    client_autenticado_da_dre,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
    solicitacao_kit_lanche_cei_avulsa_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    kit_lanche = _setup_kit_lanche(
        kit_lanche_factory, escola, contrato_factory, edital_factory
    )
    _cria_pedidos(
        kit_lanche,
        escola,
        solicitacao_kit_lanche_factory,
        solicitacao_kit_lanche_avulsa_factory,
        solicitacao_kit_lanche_cei_avulsa_factory,
        status_pedido="DRE_A_VALIDAR",
        data=data,
    )

    response = client_autenticado_da_dre.get(
        f"/solicitacao-kit-lanche/{PEDIDOS_DRE}/{SEM_FILTRO}/"
        f"?prazo=REGULAR&busca={escola.codigo_eol}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 3

    response = client_autenticado_da_dre.get(
        f"/solicitacao-kit-lanche/{PEDIDOS_DRE}/{SEM_FILTRO}/"
        f"?prazo=REGULAR&busca=zzzzzz"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


def test_solicitacoes_codae_unificado(
    client_autenticado_da_codae,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
    solicitacao_kit_lanche_cei_avulsa_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    kit_lanche = _setup_kit_lanche(
        kit_lanche_factory, escola, contrato_factory, edital_factory
    )
    _cria_pedidos(
        kit_lanche,
        escola,
        solicitacao_kit_lanche_factory,
        solicitacao_kit_lanche_avulsa_factory,
        solicitacao_kit_lanche_cei_avulsa_factory,
        status_pedido="DRE_VALIDADO",
        data=data,
    )

    response = client_autenticado_da_codae.get(
        f"/solicitacao-kit-lanche/{PEDIDOS_CODAE}/{SEM_FILTRO}/?prazo=REGULAR"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert dados["count"] == 3
    assert len(dados["results"]) == 3
    assert dados["escolas_solicitantes"] == 1
    assert dados["totais"]["REGULAR"] == 3


def test_solicitacoes_diretoria_regional_unificado_paginacao(
    client_autenticado_da_dre,
    kit_lanche_factory,
    escola,
    contrato_factory,
    edital_factory,
    solicitacao_kit_lanche_factory,
    solicitacao_kit_lanche_avulsa_factory,
):
    kit_lanche = _setup_kit_lanche(
        kit_lanche_factory, escola, contrato_factory, edital_factory
    )
    data = datetime.date.today() + datetime.timedelta(days=30)
    for _ in range(15):
        solicitacao_kit_lanche = solicitacao_kit_lanche_factory.create(
            kits=[kit_lanche], data=data
        )
        solicitacao_kit_lanche_avulsa_factory.create(
            solicitacao_kit_lanche=solicitacao_kit_lanche,
            rastro_lote=escola.lote,
            rastro_dre=escola.diretoria_regional,
            rastro_terceirizada=escola.lote.terceirizada,
            escola=escola,
            status="DRE_A_VALIDAR",
        )

    response = client_autenticado_da_dre.get(
        f"/solicitacao-kit-lanche/{PEDIDOS_DRE}/{SEM_FILTRO}/?prazo=REGULAR"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert dados["count"] == 15
    assert len(dados["results"]) == 10

    response = client_autenticado_da_dre.get(
        f"/solicitacao-kit-lanche/{PEDIDOS_DRE}/{SEM_FILTRO}/?prazo=REGULAR&page=2"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert len(dados["results"]) == 5
