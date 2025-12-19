import pytest
from freezegun import freeze_time
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


@freeze_time("2025-01-01")
@pytest.mark.usefixtures("client_autenticado_escola_paineis_consolidados", "escola")
class TestEndpointUltimoDiaComSolicitacaoAutorizadaNoMes:
    def _setup_solicitacoes(
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
        InclusaoAlimentacaoNormalFactory.create(
            data="2025-01-20", grupo_inclusao=grupo_inclusao_alimentacao_normal
        )
        QuantidadePorPeriodoFactory.create(
            grupo_inclusao_normal=grupo_inclusao_alimentacao_normal,
            inclusao_alimentacao_continua=None,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=grupo_inclusao_alimentacao_normal.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def test_ultima_data_com_solicitacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self._setup_solicitacoes(
            escola,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        )

        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": "2025-01-20"}

    def test_ultima_data_sem_solicitacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": None}
