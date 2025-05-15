import datetime

import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
)
from sme_sigpae_api.dados_comuns import constants


@pytest.fixture
def alteracao_cemei(escola_cemei, tipo_alimentacao, faixas_etarias_ativas):
    periodo_escolar = mommy.make("escola.PeriodoEscolar", nome="MANHA")
    alteracao_cemei = mommy.make(
        AlteracaoCardapioCEMEI,
        escola=escola_cemei,
        alunos_cei_e_ou_emei=AlteracaoCardapioCEMEI.CEI,
        rastro_escola=escola_cemei,
        rastro_lote=escola_cemei.lote,
        rastro_dre=escola_cemei.diretoria_regional,
        alterar_dia="2023-08-01",
    )
    subs1 = mommy.make(
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
        alteracao_cardapio=alteracao_cemei,
        periodo_escolar=periodo_escolar,
    )
    subs1.tipos_alimentacao_de.set([tipo_alimentacao])
    subs1.tipos_alimentacao_para.set([tipo_alimentacao])
    subs1.save()
    mommy.make(
        FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
        substituicao_alimentacao=subs1,
        matriculados_quando_criado=10,
        faixa_etaria=faixas_etarias_ativas[0],
        quantidade=10,
    )
    return alteracao_cemei


@pytest.fixture
def alteracao_cemei_dre_a_validar(alteracao_cemei):
    alteracao_cemei.status = alteracao_cemei.workflow_class.DRE_A_VALIDAR
    alteracao_cemei.save()
    return alteracao_cemei


@pytest.fixture
def alteracao_cemei_dre_validado(alteracao_cemei):
    alteracao_cemei.status = alteracao_cemei.workflow_class.DRE_VALIDADO
    alteracao_cemei.save()
    return alteracao_cemei


@pytest.fixture
def client_autenticado_vinculo_escola_cemei(
    client, django_user_model, escola_cemei, template_mensagem_alteracao_cardapio
):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cemei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )

    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_dre_escola_cemei(
    client, django_user_model, escola_cemei, template_mensagem_alteracao_cardapio
):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_cogestor = mommy.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cemei.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )

    client.login(username=email, password=password)
    return client
