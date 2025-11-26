from model_bakery import baker
import datetime
from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario


def cria_solicitacao_com_log(escola, log_criado_em, status_solicitacao):
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=10,
        ano=2025,
        escola=escola,
        status=status_solicitacao,
    )
    baker.make(
        "LogSolicitacoesUsuario",
        uuid_original=solicitacao.uuid,
        status_evento=LogSolicitacoesUsuario.MEDICAO_APROVADA_PELA_DRE,
        solicitacao_tipo=LogSolicitacoesUsuario.MEDICAO_INICIAL,
        criado_em=log_criado_em,
    )


def test_dashboard_resultados_ordenados(
    client_autenticado_diretoria_regional,
    diretoria_regional, 
    tipo_unidade_escolar,
    tipo_unidade_escolar_ceu_emei,
    tipo_unidade_escolar_cei,
):
    """
    Valida que 'dados' no dashboard vem ordenado pela 'Última atualização'.
    """

    escolas = []
    for i, tipo in enumerate([
        tipo_unidade_escolar,
        tipo_unidade_escolar_ceu_emei,
        tipo_unidade_escolar_cei,
    ], start=1):
        escola = baker.make(
            "Escola",
            nome=f"{tipo.iniciais} TESTE",
            diretoria_regional=diretoria_regional,
            tipo_unidade=tipo,
            codigo_eol=f"20000{i}",
        )
        escolas.append(escola)

    cria_solicitacao_com_log(
        escolas[0],
        log_criado_em=datetime.datetime(2025, 10, 9, 14, 9, 11, tzinfo=datetime.timezone.utc),
        status_solicitacao=SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_DRE,
    )
    cria_solicitacao_com_log(
        escolas[1],
        log_criado_em=datetime.datetime(2025, 10, 20, 11, 30, 23, tzinfo=datetime.timezone.utc),
        status_solicitacao=SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRECAO_SOLICITADA,
    )
    cria_solicitacao_com_log(
        escolas[2],
        log_criado_em=datetime.datetime(2025, 10, 23, 10, 15, 33, tzinfo=datetime.timezone.utc),
        status_solicitacao=SolicitacaoMedicaoInicialWorkflow.MEDICAO_ENVIADA_PELA_UE,
    )

    url = (
        "/medicao-inicial/solicitacao-medicao-inicial/dashboard-resultados/?status=TODOS_OS_LANCAMENTOS"
        f"&diretoria_regional={diretoria_regional.uuid}&limit=200&mes=10&ano=2025"
    )
    resp = client_autenticado_diretoria_regional.get(url)
    assert resp.status_code == 200, resp.content

    dados = resp.json()["results"]["dados"]
    assert len(dados) == 3, f"Esperado 3 solicitações, vieram {len(dados)}"

    for item in dados:
        assert item["mes"] == "10"
        assert item["ano"] == "2025"

    assert dados[0]["escola"] == escolas[0].nome
    assert dados[1]["escola"] == escolas[1].nome
    assert dados[2]["escola"] == escolas[2].nome
