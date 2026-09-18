import pytest
from rest_framework import status

from src.escola.models import Lote, TipoUnidadeEscolar
from src.perfil.models import Usuario

pytestmark = pytest.mark.django_db


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
