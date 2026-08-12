from unittest.mock import patch

from freezegun import freeze_time

from src.dados_comuns.models import SolicitacaoAberta, VersaoSistema
from src.dados_comuns.tasks import (
    atualiza_versao_sistema,
    deleta_logs_duplicados_e_cria_logs_caso_nao_existam,
    deleta_solicitacoes_abertas,
    envia_email_em_massa_task,
    envia_email_unico_task,
)
from src.dados_comuns.utils import envia_email_em_massa
from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from src.escola.models import LogAlunosMatriculadosPeriodoEscola


def test_envia_email_unico_task(reclamacao_produto_codae_recusou, dados_html):
    _, reclamacao_produto = reclamacao_produto_codae_recusou

    assunto = "[SIGPAE] Reclamação Analisada"
    email = reclamacao_produto.criado_por.email
    corpo = ""

    resultado = envia_email_unico_task(
        assunto=assunto,
        email=email,
        corpo=corpo,
        html=dados_html,
    )
    assert bool(resultado) is True


def test_envia_email_unico_task_erro(dados_html):
    assunto = "[SIGPAE] Reclamação Analisada"
    email = {}
    corpo = ""

    resultado = envia_email_unico_task(
        assunto=assunto,
        email=email,
        corpo=corpo,
        html=dados_html,
    )
    assert bool(resultado) is False


def test_envia_email_em_massa_task(reclamacao_produto_codae_recusou, dados_html):
    _, reclamacao_produto = reclamacao_produto_codae_recusou

    assunto = "[SIGPAE] Reclamação Analisada"
    emails = [reclamacao_produto.criado_por.email]
    corpo = ""

    resultado = envia_email_em_massa_task(
        assunto=assunto,
        emails=emails,
        corpo=corpo,
        html=dados_html,
    )
    assert bool(resultado) is True


def test_envia_email_em_massa_task_erro(dados_html):
    assunto = "[SIGPAE] Reclamação Analisada"
    emails = []
    corpo = ""

    resultado = envia_email_em_massa_task(
        assunto=assunto,
        emails=emails,
        corpo=corpo,
        html=dados_html,
    )
    assert bool(resultado) is False


@freeze_time("2025-02-10 16:29:00")
def test_deleta_solicitacoes_abertas(solicitacoes_abertas):
    assert SolicitacaoAberta.objects.count() == 3
    deleta_solicitacoes_abertas()
    assert SolicitacaoAberta.objects.count() == 1
    assert SolicitacaoAberta.objects.last() == solicitacoes_abertas


def test_deleta_logs_duplicados_e_cria_logs_caso_nao_existam(
    logs_alunos_matriculados_periodo_escola,
    logs_quantidade_dietas_autorizadas_escola_comum,
    logs_quantidade_dietas_autorizadas_escola_cei,
    logs_quantidade_dietas_autorizadas_escola_cemei,
):
    deleta_logs_duplicados_e_cria_logs_caso_nao_existam()

    logs = LogAlunosMatriculadosPeriodoEscola.objects.all()
    assert logs.count() == 4

    logs_dietas_comuns = LogQuantidadeDietasAutorizadas.objects.all()
    assert logs_dietas_comuns.count() == 3
    logs_dietas_cei = [
        log
        for log in LogQuantidadeDietasAutorizadasCEI.objects.all()
        if log.escola.tipo_unidade.iniciais == "CEI DIRET"
    ]
    assert len(logs_dietas_cei) == 4
    logs_dietas_cemei = [
        log
        for log in LogQuantidadeDietasAutorizadasCEI.objects.all()
        if log.escola.tipo_unidade.iniciais == "CEMEI"
    ]
    assert len(logs_dietas_cemei) == 5


@patch("src.dados_comuns.tasks.obter_versao_api")
def test_atualiza_versao_sistema_sucesso(mock_obter_versao):
    mock_obter_versao.return_value = "3.2.1"
    resultado = atualiza_versao_sistema()
    assert resultado == "3.2.1"
    assert VersaoSistema.objects.get().versao == "3.2.1"


@patch("src.dados_comuns.tasks.obter_versao_api")
def test_atualiza_versao_sistema_falha_github(mock_obter_versao):
    VersaoSistema.objects.get().versao = "2.71.5"
    VersaoSistema.objects.get().save()
    mock_obter_versao.return_value = None
    resultado = atualiza_versao_sistema()
    assert resultado is None
    assert VersaoSistema.objects.get().versao == "2.71.5"
