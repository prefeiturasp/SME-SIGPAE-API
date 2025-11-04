import datetime

import pytest
from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APIClient

from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_TREINAMENTO_PASSWORD
from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.escola.models import (
    DiretoriaRegional,
    Escola,
    TipoGestao,
    TipoUnidadeEscolar,
)
from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial

pytestmark = pytest.mark.django_db


def extrai_bloco(results, status_alvo):
    for bloco in results:
        if bloco.get("status") == status_alvo:
            return bloco
    return None


@pytest.fixture
def dre():
    return DiretoriaRegional.objects.create(nome="DRE TESTE")


@pytest.fixture
def api_client_usuario_codae(django_user_model, dre):
    """
    Cria um usuário com perfil CODAE_GESTAO_ALIMENTACAO e o vincula à DiretoriaRegional (instituicao)
    """
    client = APIClient()
    email = "usuario_codae@teste.com"
    user = django_user_model.objects.create_user(
        username=email,
        email=email,
        password=DJANGO_ADMIN_TREINAMENTO_PASSWORD,
        registro_funcional="999999",
    )

    perfil_codae = baker.make("Perfil", nome="CODAE_GESTAO_ALIMENTACAO", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=dre,
        perfil=perfil_codae,
        data_inicial=hoje,
        ativo=True,
    )
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def tipo_gestao():
    return TipoGestao.objects.create(nome="TERC TOTAL")


def cria_tipo(iniciais: str) -> TipoUnidadeEscolar:
    return TipoUnidadeEscolar.objects.create(
        iniciais=iniciais,
        ativo=True,
        pertence_relatorio_solicitacoes_alimentacao=True,
    )


def cria_escola(
    nome: str,
    iniciais_tipo: str,
    dre: DiretoriaRegional,
    codigo_eol: str,
    tipo_gestao=None,
) -> Escola:
    tipo = cria_tipo(iniciais_tipo)
    kwargs = {
        "nome": nome,
        "tipo_unidade": tipo,
        "diretoria_regional": dre,
        "codigo_eol": codigo_eol,
        "ativo": True,
    }
    if tipo_gestao:
        kwargs["tipo_gestao"] = tipo_gestao
    return Escola.objects.create(**kwargs)


def mapeia_status_evento_do_workflow(status_workflow: str) -> int:
    """
    Converte o status string do workflow (ex.: 'MEDICAO_APROVADA_PELA_CODAE')
    para o inteiro correspondente em LogSolicitacoesUsuario.STATUS_POSSIVEIS.
    """
    mapa = {
        "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE": LogSolicitacoesUsuario.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE,
        "MEDICAO_ENVIADA_PELA_UE": LogSolicitacoesUsuario.MEDICAO_ENVIADA_PELA_UE,
        "MEDICAO_CORRECAO_SOLICITADA": LogSolicitacoesUsuario.MEDICAO_CORRECAO_SOLICITADA,
        "MEDICAO_CORRIGIDA_PELA_UE": LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PELA_UE,
        "MEDICAO_APROVADA_PELA_DRE": LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
        "MEDICAO_APROVADA_PELA_CODAE": LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_CODAE,
        "MEDICAO_CORRIGIDA_PARA_CODAE": LogSolicitacoesUsuario.MEDICAO_CORRIGIDA_PARA_CODAE,
        "MEDICAO_SEM_LANCAMENTOS": LogSolicitacoesUsuario.MEDICAO_SEM_LANCAMENTOS,
    }
    if status_workflow == "TODOS_OS_LANCAMENTOS":
        return None
    return mapa[status_workflow]


def cria_solicitacao_com_log(
    escola: Escola, usuario, status_workflow: str = None, mes=None, ano=None
):
    """
    Cria a SolicitacaoMedicaoInicial e um LogSolicitacoesUsuario compatível com a raw SQL do dashboard.
    """
    hoje = datetime.date.today()
    if status_workflow is None or status_workflow == "TODOS_OS_LANCAMENTOS":
        status_workflow = SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE
    if mes is None:
        mes = str(hoje.month).zfill(2)
    if ano is None:
        ano = str(hoje.year)

    solic = SolicitacaoMedicaoInicial.objects.create(
        escola=escola,
        mes=mes,
        ano=ano,
        status=status_workflow,
    )

    status_evento = mapeia_status_evento_do_workflow(status_workflow)
    if status_evento is None:
        status_evento = mapeia_status_evento_do_workflow(status_workflow)

    LogSolicitacoesUsuario.objects.create(
        criado_em=timezone.now(),
        status_evento=status_evento,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
        uuid_original=solic.uuid,
        usuario=usuario,
    )
    return solic


@pytest.mark.parametrize(
    "status_bloco",
    [
        "TODOS_OS_LANCAMENTOS",
        SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
    ],
)
def test_dashboard_dados_ordenados(
    api_client_usuario_codae, dre, tipo_gestao, status_bloco
):
    """
    Valida que 'dados' no dashboard vem ordenado por grupos/subtipos e por nome dentro do subtipo.
    """
    user = api_client_usuario_codae.handler._force_user

    # Grupo 4 - EMEF (duas escolas para teste alfabético)
    emef_1 = cria_escola(
        "EMEF JOAO CARLOS DA SILVA BORGES, PROF.", "EMEF", dre, "100001", tipo_gestao
    )
    emef_2 = cria_escola(
        "EMEF PERICLES EUGENIO DA SILVA RAMOS", "EMEF", dre, "100002", tipo_gestao
    )

    # Grupo 1 - CEI (inclui mais itens para validar alfabético)
    cei_diret_1 = cria_escola(
        "CEI DIRET MARIA", "CEI DIRET", dre, "200001", tipo_gestao
    )
    cei_diret_0 = cria_escola("CEI DIRET ANA", "CEI DIRET", dre, "200004", tipo_gestao)

    ceu_cei_1 = cria_escola("CEU CEI PAULO", "CEU CEI", dre, "200002", tipo_gestao)
    ceu_cei_2 = cria_escola("CEU CEI ANA", "CEU CEI", dre, "200005", tipo_gestao)

    cci_cips_1 = cria_escola("CCI/CIPS TESTE", "CCI/CIPS", dre, "200003", tipo_gestao)
    cci_cips_2 = cria_escola("CCI/CIPS ABC", "CCI/CIPS", dre, "200006", tipo_gestao)

    # Grupo 2 - CEMEI
    cemei_1 = cria_escola("CEMEI CENTRAL", "CEMEI", dre, "300001", tipo_gestao)
    ceu_cemei_1 = cria_escola("CEU CEMEI SUL", "CEU CEMEI", dre, "300002", tipo_gestao)

    # Grupo 3 - EMEI
    emei_1 = cria_escola("EMEI JARDIM", "EMEI", dre, "400001", tipo_gestao)
    ceu_emei_1 = cria_escola("CEU EMEI NORTE", "CEU EMEI", dre, "400002", tipo_gestao)

    # Grupo 4 - adicionais
    emefm_1 = cria_escola("EMEFM TESTE ALPHA", "EMEFM", dre, "500001", tipo_gestao)

    # Incluímos CEU GESTAO (duas escolas para validar alfabético) ANTES de CEU EMEF (por constants)
    ceu_gestao_1 = cria_escola(
        "CEU GESTAO LESTE", "CEU GESTAO", dre, "500004", tipo_gestao
    )
    ceu_gestao_2 = cria_escola(
        "CEU GESTAO CENTRO", "CEU GESTAO", dre, "500005", tipo_gestao
    )
    ceu_emef_1 = cria_escola(
        "CEU EMEF ROSA PARKS", "CEU EMEF", dre, "500003", tipo_gestao
    )

    # Grupo 5 - EMEBS
    emebs_1 = cria_escola("EMEBS ESPECIAL", "EMEBS", dre, "600001", tipo_gestao)

    # Grupo 6 -  CIEJA e CMCT
    cieja_1 = cria_escola("CIEJA CAMPO LIMPO", "CIEJA", dre, "700001", tipo_gestao)
    cmct_1 = cria_escola("CMCT CAMPO BELO", "CMCT", dre, "700002", tipo_gestao)

    escolas = [
        emef_1,
        emef_2,
        cei_diret_1,
        cei_diret_0,
        ceu_cei_1,
        ceu_cei_2,
        cci_cips_1,
        cci_cips_2,
        cemei_1,
        ceu_cemei_1,
        emei_1,
        ceu_emei_1,
        emefm_1,
        cieja_1,
        ceu_gestao_1,
        ceu_gestao_2,
        ceu_emef_1,
        emebs_1,
        cmct_1,
    ]
    for esc in escolas:
        cria_solicitacao_com_log(
            esc,
            usuario=user,
            status_workflow=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
        )

    # Chama o endpoint com mês/ano atual e paginação ampla
    hoje = datetime.date.today()
    url = f"/medicao-inicial/solicitacao-medicao-inicial/dashboard-resultados/?limit=200&mes={str(hoje.month).zfill(2)}&ano={hoje.year}"
    resp = api_client_usuario_codae.get(url)
    assert resp.status_code == 200, resp.content

    data = resp.json()
    assert "results" in data
    dados = data["results"]["dados"]
    # Ordem esperada seguindo os constants atuais:
    # Grupo 1 (CEI DIRET=1, CEI CEU=2, CEU CEI=3, CCI=4, CCI/CIPS=5, CEI=6)
    # - CEI DIRET: alfabético
    # - CEI CEU: (não criado neste teste)
    # - CEU CEI: alfabético
    # - CCI/CIPS: alfabético
    ordem_esperada = [
        # Grupo 1
        ("CEI DIRET", "CEI DIRET ANA"),
        ("CEI DIRET", "CEI DIRET MARIA"),
        ("CEU CEI", "CEU CEI ANA"),
        ("CEU CEI", "CEU CEI PAULO"),
        ("CCI/CIPS", "CCI/CIPS ABC"),
        ("CCI/CIPS", "CCI/CIPS TESTE"),
        # Grupo 2
        ("CEMEI", "CEMEI CENTRAL"),
        ("CEU CEMEI", "CEU CEMEI SUL"),
        # Grupo 3
        ("EMEI", "EMEI JARDIM"),
        ("CEU EMEI", "CEU EMEI NORTE"),
        # Grupo 4 (EMEF=1, CEU EMEF=2, EMEFM=3, EMEF P FOM=4, CIEJA=5, CEU GESTAO=6)
        ("EMEF", "EMEF JOAO CARLOS DA SILVA BORGES, PROF."),
        ("EMEF", "EMEF PERICLES EUGENIO DA SILVA RAMOS"),
        ("CEU EMEF", "CEU EMEF ROSA PARKS"),
        ("EMEFM", "EMEFM TESTE ALPHA"),
        ("CEU GESTAO", "CEU GESTAO CENTRO"),
        ("CEU GESTAO", "CEU GESTAO LESTE"),
        # Grupo 5
        ("EMEBS", "EMEBS ESPECIAL"),
        # Grupo 6
        ("CIEJA", "CIEJA CAMPO LIMPO"),
        ("CMCT", "CMCT CAMPO BELO"),
    ]

    for i, (tipo_esp, nome_esp) in enumerate(ordem_esperada):
        assert (
            dados[i]["tipo_unidade"] == tipo_esp
        ), f"Posição {i}: esperado tipo '{tipo_esp}', obtido '{dados[i].get('tipo_unidade')}'. Item: {dados[i]}"
        assert (
            dados[i]["escola"] == nome_esp
        ), f"Posição {i}: esperado escola '{nome_esp}', obtido '{dados[i].get('escola')}'. Item: {dados[i]}"
