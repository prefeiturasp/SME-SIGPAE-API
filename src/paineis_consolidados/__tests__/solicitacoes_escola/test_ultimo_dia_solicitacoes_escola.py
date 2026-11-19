import pytest
from freezegun import freeze_time
from rest_framework import status

from src.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.inclusao_alimentacao.fixtures.factories.base_factory import (
    GrupoInclusaoAlimentacaoNormalFactory,
    InclusaoAlimentacaoContinuaFactory,
    InclusaoAlimentacaoNormalFactory,
    QuantidadePorPeriodoFactory,
)
from src.inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
)

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

    def _setup_inclusao_continua(
        self,
        escola,
        usuario,
        data_inicial="2025-01-25",
        data_final="2025-01-30",
    ):
        inclusao_continua = InclusaoAlimentacaoContinuaFactory.create(
            escola=escola,
            rastro_escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.diretoria_regional,
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
            data_inicial=data_inicial,
            data_final=data_final,
        )
        QuantidadePorPeriodoFactory.create(
            grupo_inclusao_normal=None,
            inclusao_alimentacao_continua=inclusao_continua,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=inclusao_continua.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
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

    def test_considera_inclusao_continua_no_calculo_da_ultima_data_por_padrao(
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
        self._setup_inclusao_continua(escola, usuario)

        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": "2025-01-30"}

    def test_usa_fim_da_inclusao_continua_quando_posterior_as_demais(
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
        self._setup_inclusao_continua(
            escola,
            usuario,
            data_inicial="2025-01-01",
            data_final="2025-01-25",
        )

        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": "2025-01-25"}

    def test_limita_inclusao_continua_ao_ultimo_dia_do_mes(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self._setup_inclusao_continua(
            escola,
            usuario,
            data_inicial="2025-01-25",
            data_final="2025-02-05",
        )

        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": "2025-01-31"}

    def test_usa_fim_da_inclusao_continua_iniciada_no_mes_anterior(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self._setup_inclusao_continua(
            escola,
            usuario,
            data_inicial="2024-12-20",
            data_final="2025-01-10",
        )

        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": "2025-01-10"}

    def test_ignora_inclusao_continua_quando_solicitado(
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
        self._setup_inclusao_continua(escola, usuario)

        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
            f"&excluir_inclusoes_continuas=true"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": "2025-01-20"}

    def test_ultima_data_nula_quando_existe_apenas_inclusao_continua(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        self._setup_inclusao_continua(escola, usuario)

        response = client.get(
            f"/escola-solicitacoes/ultimo-dia-com-solicitacao-autorizada-no-mes/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=01&"
            f"ano=2025"
            f"&excluir_inclusoes_continuas=true"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"ultima_data": None}
