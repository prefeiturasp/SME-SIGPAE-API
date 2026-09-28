import pytest
from django.utils import timezone
from model_bakery import baker

from src.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from src.medicao_inicial.models import (
    Medicao,
    OcorrenciaMedicaoInicial,
    SolicitacaoMedicaoInicial,
)
from src.medicao_inicial.services.pendencias_acao_dre import (
    anotar_pendencia_acao_dre,
)

pytestmark = pytest.mark.django_db


def criar_solicitacao(
    escola,
    status_solicitacao=SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRIGIDA_PARA_CODAE,
    status_medicao=Medicao.workflow_class.MEDICAO_APROVADA_PELA_CODAE,
    possui_ciencia=False,
):
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        status=status_solicitacao,
        dre_ciencia_correcao_data=timezone.now() if possui_ciencia else None,
    )
    baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        status=status_medicao,
    )
    return solicitacao


def obter_pendencia(solicitacao):
    return anotar_pendencia_acao_dre(
        SolicitacaoMedicaoInicial.objects.filter(pk=solicitacao.pk)
    ).get()


def test_anota_pendencia_quando_dre_precisa_dar_ciencia(escola):
    solicitacao = criar_solicitacao(escola)

    resultado = obter_pendencia(solicitacao)

    assert resultado.pendente_acao_dre is True


@pytest.mark.parametrize(
    "status_solicitacao,status_medicao,possui_ciencia",
    [
        (
            SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE,
            Medicao.workflow_class.MEDICAO_APROVADA_PELA_CODAE,
            False,
        ),
        (
            SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRIGIDA_PARA_CODAE,
            Medicao.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE,
            False,
        ),
        (
            SolicitacaoMedicaoInicialWorkflow.MEDICAO_CORRIGIDA_PARA_CODAE,
            Medicao.workflow_class.MEDICAO_APROVADA_PELA_CODAE,
            True,
        ),
    ],
)
def test_nao_anota_pendencia_fora_das_condicoes(
    escola,
    status_solicitacao,
    status_medicao,
    possui_ciencia,
):
    solicitacao = criar_solicitacao(
        escola,
        status_solicitacao=status_solicitacao,
        status_medicao=status_medicao,
        possui_ciencia=possui_ciencia,
    )

    resultado = obter_pendencia(solicitacao)

    assert resultado.pendente_acao_dre is False


def test_exige_aprovacao_da_ocorrencia_pela_codae(escola):
    solicitacao = criar_solicitacao(escola)
    ocorrencia = baker.make(
        "OcorrenciaMedicaoInicial",
        solicitacao_medicao_inicial=solicitacao,
        status=(
            OcorrenciaMedicaoInicial.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE
        ),
    )

    assert obter_pendencia(solicitacao).pendente_acao_dre is False

    ocorrencia.status = (
        OcorrenciaMedicaoInicial.workflow_class.MEDICAO_APROVADA_PELA_CODAE
    )
    ocorrencia.save(update_fields=["status"])

    assert obter_pendencia(solicitacao).pendente_acao_dre is True
