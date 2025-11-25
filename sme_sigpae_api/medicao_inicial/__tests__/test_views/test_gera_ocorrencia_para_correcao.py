import json

import pytest
from rest_framework import status

from sme_sigpae_api.medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    OcorrenciaMedicaoInicialFactory,
    SolicitacaoMedicaoInicialFactory,
)
from sme_sigpae_api.medicao_inicial.models import OcorrenciaMedicaoInicial

pytestmark = pytest.mark.django_db
viewset_url = "/medicao-inicial/ocorrencia/"


@pytest.mark.usefixtures(
    "client_autenticado_diretoria_regional", "client_autenticado_codae_medicao"
)
class TestGeraOcorrenciaParaCorrecao:

    def setup_solicitacao(self):
        self.solicitacao = SolicitacaoMedicaoInicialFactory.create()

    def setup_ocorrencia(self, solicitacao: SolicitacaoMedicaoInicialFactory):
        self.ocorrencia = OcorrenciaMedicaoInicialFactory.create(
            solicitacao_medicao_inicial=solicitacao
        )

    def test_gera_ocorrencia_para_correcao_sucesso_dre(
        self, client_autenticado_diretoria_regional
    ):
        self.setup_solicitacao()

        data = {
            "solicitacao_medicao_uuid": str(self.solicitacao.uuid),
            "justificativa": "Necessário corrigir.",
        }

        response = client_autenticado_diretoria_regional.post(
            f"{viewset_url}gera-ocorrencia-para-correcao/",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["solicitacao_medicao_inicial"] == self.solicitacao.id

        assert OcorrenciaMedicaoInicial.objects.filter(
            solicitacao_medicao_inicial=self.solicitacao
        ).exists()

    def test_gera_ocorrencia_para_correcao_sucesso_codae(
        self, client_autenticado_codae_medicao
    ):
        self.setup_solicitacao()

        data = {
            "solicitacao_medicao_uuid": str(self.solicitacao.uuid),
            "justificativa": "Corrigir alimentação.",
        }

        response = client_autenticado_codae_medicao.post(
            f"{viewset_url}gera-ocorrencia-para-correcao/",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_200_OK

        assert (
            OcorrenciaMedicaoInicial.objects.filter(
                solicitacao_medicao_inicial=self.solicitacao
            ).count()
            == 1
        )

    def test_gera_ocorrencia_para_correcao_erro_solicitacao_inexistente(
        self, client_autenticado_diretoria_regional
    ):
        data = {
            "solicitacao_medicao_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            "justificativa": "Teste",
        }

        response = client_autenticado_diretoria_regional.post(
            f"{viewset_url}gera-ocorrencia-para-correcao/",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"solicitacao_medicao_uuid": "Medição não encontrada"}

    def test_gera_ocorrencia_para_correcao_erro_ja_possui_ocorrencia(
        self, client_autenticado_diretoria_regional
    ):
        self.setup_solicitacao()
        self.setup_ocorrencia(self.solicitacao)

        data = {
            "solicitacao_medicao_uuid": str(self.solicitacao.uuid),
            "justificativa": "Corrigir",
        }

        response = client_autenticado_diretoria_regional.post(
            f"{viewset_url}gera-ocorrencia-para-correcao/",
            data=json.dumps(data),
            content_type="application/json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"medicao": "Já possui ocorrência associada"}
