import datetime

import pytest
from model_mommy import mommy

from sme_sigpae_api.cardapio.models import (
    GrupoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from sme_sigpae_api.dados_comuns.models import TemplateMensagem
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.escola.models import Aluno
from sme_sigpae_api.perfil.models.usuario import Usuario


def criar_suspensoes(grupo_suspensao, datas_cancelamentos):
    """
    Cria objetos SuspensaoAlimentacao para o grupo_suspensao.
    :param grupo_suspensao: GrupoSuspensaoAlimentacao associado.
    :param datas_cancelamentos: Lista de tuplas (data, cancelado, justificativa).
    """
    for data, cancelado, justificativa in datas_cancelamentos:
        mommy.make(
            SuspensaoAlimentacao,
            data=data,
            grupo_suspensao=grupo_suspensao,
            cancelado=cancelado,
            cancelado_justificativa=justificativa,
        )


@pytest.fixture
def escola():
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    diretoria_regional = mommy.make(
        "DiretoriaRegional", nome="DIRETORIA REGIONAL IPIRANGA"
    )
    escola = mommy.make(
        "Escola",
        lote=lote,
        nome="EMEF JOAO MENDES",
        codigo_eol="000546",
        diretoria_regional=diretoria_regional,
    )
    return escola


@pytest.fixture
def template_mensagem_dieta_especial():
    return mommy.make(
        TemplateMensagem,
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        assunto="TESTE DIETA ESPECIAL",
        template_html="@id @criado_em @status @link",
    )


@pytest.fixture
def grupo_suspensao_alimentacao(escola):
    grupo_suspensao = mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
        escola=escola,
        rastro_escola=escola,
    )
    criar_suspensoes(
        grupo_suspensao,
        [
            (datetime.date(2025, 1, 20), False, ""),
            (datetime.date(2025, 1, 21), False, ""),
            (datetime.date(2025, 1, 22), False, ""),
            (datetime.date(2025, 1, 23), False, ""),
            (datetime.date(2025, 1, 24), False, ""),
        ],
    )

    return grupo_suspensao


@pytest.fixture
def grupo_suspensao_alimentacao_cancelamento_parcial(escola):
    grupo_suspensao = mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
        escola=escola,
        rastro_escola=escola,
    )
    criar_suspensoes(
        grupo_suspensao,
        [
            (datetime.date(2025, 1, 20), True, "Cancelado por motivos maiores"),
            (datetime.date(2025, 1, 21), False, ""),
            (
                datetime.date(2025, 1, 22),
                True,
                "Ajustes internos necessários para o funcionamento da unidade.",
            ),
            (datetime.date(2025, 1, 23), False, ""),
            (datetime.date(2025, 1, 24), False, ""),
        ],
    )

    return grupo_suspensao


@pytest.fixture
def grupo_suspensao_alimentacao_cancelamento_total(escola):
    grupo_suspensao = mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
        escola=escola,
        rastro_escola=escola,
    )
    criar_suspensoes(
        grupo_suspensao,
        [
            (datetime.date(2025, 1, 20), True, "Cancelado por falta de recursos"),
            (datetime.date(2025, 1, 21), True, "Cancelamento preventivo"),
            (datetime.date(2025, 1, 22), True, "Interrupção necessária"),
            (datetime.date(2025, 1, 23), True, "Manutenção na unidade"),
            (datetime.date(2025, 1, 24), True, "Suspensão devido a reformas"),
        ],
    )

    return grupo_suspensao


@pytest.fixture
def solicitacao_dieta_especial_a_autorizar(
    client, escola, template_mensagem_dieta_especial
):
    email = "escola@admin.com"
    password = DJANGO_ADMIN_PASSWORD
    rf = "1545933"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil_professor = mommy.make("perfil.Perfil", nome="ADMINISTRADOR_UE", ativo=False)
    mommy.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_professor,
        data_inicial=datetime.date.today(),
        ativo=True,
    )  # ativo

    aluno = mommy.make(
        Aluno,
        nome="Roberto Alves da Silva",
        codigo_eol="123456",
        data_nascimento="2000-01-01",
    )
    solic = mommy.make(
        SolicitacaoDietaEspecial,
        escola_destino=escola,
        rastro_escola=escola,
        rastro_terceirizada=escola.lote.terceirizada,
        aluno=aluno,
        ativo=True,
        criado_por=user,
    )
    solic.inicia_fluxo(user=user)

    return solic


@pytest.fixture
def solicitacao_dieta_especial_autorizada(
    client, escola, solicitacao_dieta_especial_a_autorizar
):
    email = "terceirizada@admin.com"
    password = DJANGO_ADMIN_PASSWORD
    rf = "4545454"
    user = Usuario.objects.create_user(
        username=email, password=password, email=email, registro_funcional=rf
    )
    client.login(username=email, password=password)

    perfil = mommy.make("perfil.Perfil", nome="TERCEIRIZADA", ativo=False)
    mommy.make(
        "perfil.Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )

    solicitacao_dieta_especial_a_autorizar.codae_autoriza(user=user)

    return solicitacao_dieta_especial_a_autorizar
