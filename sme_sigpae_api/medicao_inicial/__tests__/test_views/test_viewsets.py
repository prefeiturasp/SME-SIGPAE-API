import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict

from sme_sigpae_api.dados_comuns.fluxo_status import SolicitacaoMedicaoInicialWorkflow
from sme_sigpae_api.medicao_inicial.api.viewsets import SolicitacaoMedicaoInicialViewSet

pytestmark = pytest.mark.django_db


def test_valida_sem_lancamentos_retorna_none(solicitacao_sem_lancamento):
    validado = SolicitacaoMedicaoInicialViewSet._valida_sem_lancamentos(
        None, solicitacao_sem_lancamento
    )
    assert validado is None


def test_valida_sem_lancamentos_retorna_exception(solicitacao_escola_emebs):

    with pytest.raises(
        ValidationError,
        match="Solicitação Medição Inicial não pode voltar para ser preenchida novamente, pois possui lançamentos.",
    ):
        SolicitacaoMedicaoInicialViewSet._valida_sem_lancamentos(
            None, solicitacao_escola_emebs
        )


def test_solicita_correcao_em_solicitacao(
    solicitacao_sem_lancamento, user_administrador_medicao
):
    usuario, _ = user_administrador_medicao
    justificativa = "Houva alimentação autorizada no período"
    SolicitacaoMedicaoInicialViewSet._solicita_correcao_em_solicitacao(
        None, solicitacao_sem_lancamento, usuario, justificativa
    )
    assert (
        solicitacao_sem_lancamento.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    medicao = solicitacao_sem_lancamento.medicoes.first()
    assert medicao.status == SolicitacaoMedicaoInicialWorkflow.MEDICAO_SEM_LANCAMENTOS


def test_solicita_correcao_em_medicoes(
    solicitacao_sem_lancamento, user_administrador_medicao
):
    usuario, _ = user_administrador_medicao
    justificativa = "Houva alimentação autorizada no período"
    SolicitacaoMedicaoInicialViewSet._solicita_correcao_em_medicoes(
        None, solicitacao_sem_lancamento, usuario, justificativa
    )
    medicao = solicitacao_sem_lancamento.medicoes.first()
    assert (
        medicao.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    assert (
        solicitacao_sem_lancamento.status
        == SolicitacaoMedicaoInicialWorkflow.MEDICAO_APROVADA_PELA_CODAE
    )


@pytest.mark.parametrize(
    "query_dict,expected",
    [
        (
            QueryDict("tipo_unidade=550e8400-e29b-41d4-a716-446655440000"),
            {"escola__tipo_unidade__uuid": "550e8400-e29b-41d4-a716-446655440000"},
        ),
        (
            QueryDict("dre=6fa459ea-ee8a-3ca4-894e-db77e160355e"),
            {
                "escola__diretoria_regional__uuid": "6fa459ea-ee8a-3ca4-894e-db77e160355e"
            },
        ),
        (QueryDict("ocorrencias=true"), {"com_ocorrencias": True}),
        (QueryDict("ocorrencias=false"), {"com_ocorrencias": False}),
        (QueryDict("mes_ano=09_2025"), {"mes": "09", "ano": "2025"}),
        (
            QueryDict(
                "lotes_selecionados[]=123e4567-e89b-12d3-a456-426614174000&lotes_selecionados[]=123e4567-e89b-12d3-a456-426614174111"
            ),
            {
                "escola__lote__uuid__in": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174111",
                ]
            },
        ),
        (
            QueryDict("escola=765432 - ESCOLA MUNICIPAL EMEF"),
            {"escola__codigo_eol": "765432"},
        ),
        (
            QueryDict(
                "tipo_unidade=550e8400-e29b-41d4-a716-446655440000"
                "&dre=6fa459ea-ee8a-3ca4-894e-db77e160355e"
                "&ocorrencias=true"
                "&mes_ano=09_2025"
                "&escola=123456 - ESCOLA TESTE CEU"
                "&lotes_selecionados[]=123e4567-e89b-12d3-a456-426614174000"
                "&lotes_selecionados[]=123e4567-e89b-12d3-a456-426614174222"
            ),
            {
                "escola__tipo_unidade__uuid": "550e8400-e29b-41d4-a716-446655440000",
                "escola__diretoria_regional__uuid": "6fa459ea-ee8a-3ca4-894e-db77e160355e",
                "com_ocorrencias": True,
                "mes": "09",
                "ano": "2025",
                "escola__lote__uuid__in": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174222",
                ],
                "escola__codigo_eol": "123456",
            },
        ),
    ],
)
def test_solicitacao_medicao_formatar_filtros(query_dict, expected):
    viewset = SolicitacaoMedicaoInicialViewSet()
    result = viewset.formatar_filtros(query_dict)
    assert result == expected
