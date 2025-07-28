import datetime

import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
)
from sme_sigpae_api.dados_comuns import constants


@pytest.fixture
def alteracao_cardapio_cei(escola, template_mensagem_alteracao_cardapio):
    return baker.make(
        AlteracaoCardapioCEI,
        escola=escola,
        observacao="teste",
        data=datetime.date(2019, 12, 31),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )


@pytest.fixture
def client_autenticado_vinculo_escola_cei_cardapio(
    client, django_user_model, escola_cei, template_mensagem_alteracao_cardapio
):
    email = "test@test.com"
    rf = "8888888"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=rf, password=password, email=email, registro_funcional="8888888"
    )
    assert escola_cei.tipo_gestao.nome == "TERC TOTAL"
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    baker.make(
        GrupoSuspensaoAlimentacao,
        criado_por=user,
        escola=escola_cei,
        rastro_escola=escola_cei,
    )
    client.login(username=rf, password=password)
    return client
