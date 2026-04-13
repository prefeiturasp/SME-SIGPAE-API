import pytest
from django.test import Client
from rest_framework import status

from sme_sigpae_api.pre_recebimento.cronograma_semanal.models import CronogramaSemanal

pytestmark = pytest.mark.django_db


class TestCronogramaSemanalViewSet:
    def test_post_rascunho_sucesso(
        self, client_autenticado_vinculo_dilog_cronograma, payload_cronograma_semanal_rascunho
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            payload_cronograma_semanal_rascunho,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "uuid" in response.json()

    def test_post_rascunho_sem_cronograma_mensal(
        self, client_autenticado_vinculo_dilog_cronograma
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            {"observacoes": "Teste"},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cronograma_mensal" in response.json()

    def test_post_rascunho_cronograma_nao_ponto_a_ponto(
        self, client_autenticado_vinculo_dilog_cronograma, cronograma_nao_ponto_a_ponto_assinado
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            {"cronograma_mensal": str(cronograma_nao_ponto_a_ponto_assinado.uuid)},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Ponto a Ponto" in str(response.json())

    def test_post_rascunho_cronograma_nao_assinado_codae(
        self, client_autenticado_vinculo_dilog_cronograma, cronograma_ponto_a_ponto_nao_assinado
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            {"cronograma_mensal": str(cronograma_ponto_a_ponto_nao_assinado.uuid)},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "ASSINADO_CODAE" in str(response.json())

    def test_post_rascunho_com_programacoes(
        self, client_autenticado_vinculo_dilog_cronograma, payload_cronograma_semanal_com_programacoes
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            payload_cronograma_semanal_com_programacoes,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "programacoes" in data
        assert len(data["programacoes"]) == 2

    def test_patch_atualiza_rascunho(
        self, client_autenticado_vinculo_dilog_cronograma, cronograma_semanal_rascunho
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.patch(
            f"/cronogramas-semanais/{cronograma_semanal_rascunho.uuid}/",
            {"observacoes": "Observação atualizada"},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        cronograma_semanal_rascunho.refresh_from_db()
        assert cronograma_semanal_rascunho.observacoes == "Observação atualizada"

    def test_patch_atualiza_observacoes(
        self, client_autenticado_vinculo_dilog_cronograma, cronograma_semanal_rascunho
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.patch(
            f"/cronogramas-semanais/{cronograma_semanal_rascunho.uuid}/",
            {"observacoes": "Nova observação"},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK

    def test_patch_atualiza_programacoes(
        self, client_autenticado_vinculo_dilog_cronograma, cronograma_semanal_rascunho, cronograma_ponto_a_ponto_assinado
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.patch(
            f"/cronogramas-semanais/{cronograma_semanal_rascunho.uuid}/",
            {
                "cronograma_mensal": str(cronograma_ponto_a_ponto_assinado.uuid),
                "programacoes": [
                    {
                        "mes_programado": "05/2026",
                        "data_inicio": "2026-05-01",
                        "data_fim": "2026-05-15",
                        "quantidade": 75.0,
                    }
                ],
            },
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        cronograma_semanal_rascunho.refresh_from_db()
        assert cronograma_semanal_rascunho.programacoes.count() == 1

    def test_get_cronogramas_mensal_assinados_lista(
        self, client_autenticado_vinculo_dilog_cronograma, cronograma_ponto_a_ponto_assinado
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.get("/cronogramas-semanais/cronogramas-mensal-assinados/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_cronogramas_mensal_assinados_filtra_nao_ponto_a_ponto(
        self, client_autenticado_vinculo_dilog_cronograma,
        cronograma_ponto_a_ponto_assinado, cronograma_nao_ponto_a_ponto_assinado
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.get("/cronogramas-semanais/cronogramas-mensal-assinados/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        uuids = [item["uuid"] for item in data]
        assert str(cronograma_nao_ponto_a_ponto_assinado.uuid) not in uuids

    def test_get_cronogramas_mensal_assinados_filtra_status(
        self, client_autenticado_vinculo_dilog_cronograma,
        cronograma_ponto_a_ponto_assinado, cronograma_ponto_a_ponto_nao_assinado
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.get("/cronogramas-semanais/cronogramas-mensal-assinados/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        uuids = [item["uuid"] for item in data]
        assert str(cronograma_ponto_a_ponto_nao_assinado.uuid) not in uuids

    def test_permissao_dilog_cronograma_permitido(
        self, client_autenticado_vinculo_dilog_cronograma, payload_cronograma_semanal_rascunho
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            payload_cronograma_semanal_rascunho,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_permissao_coordenador_codae_dilog_permitido(
        self, client_autenticado_coordenador_codae_dilog, payload_cronograma_semanal_rascunho
    ):
        client, _ = client_autenticado_coordenador_codae_dilog
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            payload_cronograma_semanal_rascunho,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_permissao_negada_outro_perfil(
        self, client_autenticado_dilog_abastecimento, payload_cronograma_semanal_rascunho
    ):
        response = client_autenticado_dilog_abastecimento.post(
            "/cronogramas-semanais/rascunho/",
            payload_cronograma_semanal_rascunho,
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_permissao_negada_nao_autenticado(self, payload_cronograma_semanal_rascunho):
        client = Client()
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            payload_cronograma_semanal_rascunho,
            content_type="application/json",
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_get_cronogramas_mensal_assinados_campos_retornados(
        self, client_autenticado_vinculo_dilog_cronograma, cronograma_ponto_a_ponto_assinado
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.get("/cronogramas-semanais/cronogramas-mensal-assinados/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        if len(data) > 0:
            item = data[0]
            assert "uuid" in item
            assert "numero" in item
            assert "produto_nome" in item
            assert "fornecedor_nome" in item
            assert "numero_contrato" in item

    def test_post_rascunho_uuid_invalido(
        self, client_autenticado_vinculo_dilog_cronograma
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.post(
            "/cronogramas-semanais/rascunho/",
            {"cronograma_mensal": "uuid-invalido"},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_uuid_inexistente(
        self, client_autenticado_vinculo_dilog_cronograma
    ):
        client, _ = client_autenticado_vinculo_dilog_cronograma
        response = client.patch(
            "/cronogramas-semanais/00000000-0000-0000-0000-000000000000/",
            {"observacoes": "Teste"},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
