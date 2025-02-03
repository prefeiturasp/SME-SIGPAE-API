import pytest
from freezegun.api import freeze_time
from rest_framework import status

from sme_sigpae_api.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.inclusao_alimentacao.fixtures.factories.base_factory import (
    GrupoInclusaoAlimentacaoNormalFactory,
    InclusaoAlimentacaoNormalFactory,
    QuantidadePorPeriodoFactory,
)
from sme_sigpae_api.inclusao_alimentacao.models import GrupoInclusaoAlimentacaoNormal

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("client_autenticado_escola_paineis_consolidados", "escola")
@freeze_time("2025-01-13")
class TestEndpointsPainelGerencialAlimentacaoEscola:
    def setup_solicitacoes(
        self,
        escola,
        usuario,
        status,
        status_evento,
    ):
        grupo_inclusao_alimentacao_normal = (
            GrupoInclusaoAlimentacaoNormalFactory.create(
                escola=escola,
                rastro_escola=escola,
                rastro_lote=escola.lote,
                rastro_dre=escola.diretoria_regional,
                status=status,
            )
        )
        InclusaoAlimentacaoNormalFactory.create(
            data="2025-01-14", grupo_inclusao=grupo_inclusao_alimentacao_normal
        )
        QuantidadePorPeriodoFactory.create(
            grupo_inclusao_normal=grupo_inclusao_alimentacao_normal
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=grupo_inclusao_alimentacao_normal.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def test_pendentes_autorizacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self.setup_solicitacoes(
            escola,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_A_VALIDAR,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        )

        response = client.get("/escola-solicitacoes/pendentes-autorizacao/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1

    def test_autorizados(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self.setup_solicitacoes(
            escola,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        )

        response = client.get("/escola-solicitacoes/autorizados/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 2

    def test_negados(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self.setup_solicitacoes(
            escola,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_NEGOU_PEDIDO,
            status_evento=LogSolicitacoesUsuario.CODAE_NEGOU,
        )

        response = client.get("/escola-solicitacoes/negados/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1

    def test_cancelados(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self.setup_solicitacoes(
            escola,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.ESCOLA_CANCELOU,
            status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
        )

        response = client.get("/escola-solicitacoes/cancelados/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
