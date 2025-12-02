import pytest
from freezegun import freeze_time
from rest_framework import status

from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial

pytestmark = pytest.mark.django_db


@freeze_time("2025-12-02")
@pytest.mark.usefixtures("client_autenticado_vinculo_dre_dieta", "escola")
class TestUseCaseRelatorioDietasAutorizadas:
    def _setup_periodos_escolares(self, periodo_escolar_factory):
        self.periodo_integral = periodo_escolar_factory.create(nome="INTEGRAL")

    def _setup_usuario_escola(self, usuario_factory, vinculo_factory, escola):
        self.usuario_escola = usuario_factory.create()
        self.vinculo_escola_diretor = vinculo_factory.create(
            usuario=self.usuario_escola,
            object_id=escola.id,
            instituicao=escola,
            perfil__nome="DIRETOR_UE",
            data_inicial="2025-09-01",
            data_final=None,
            ativo=True,
        )

    def _setup_classificacao_dieta(self, classificacao_dieta_factory):
        self.classificacao_tipo_a = classificacao_dieta_factory.create(nome="Tipo A")
        self.classificacao_tipo_b = classificacao_dieta_factory.create(nome="Tipo B")

    def _setup_alunos(self, aluno_factory, escola):
        self.aluno_1 = aluno_factory.create(
            codigo_eol="1234567",
            periodo_escolar=self.periodo_integral,
            escola=escola,
            nome="MARIA SILVA",
        )
        self.aluno_2 = aluno_factory.create(
            codigo_eol="7654321",
            periodo_escolar=self.periodo_integral,
            escola=escola,
            nome="JOÃO COSTA",
        )
        self.aluno_3 = aluno_factory.create(
            codigo_eol=None,
            periodo_escolar=None,
            escola=None,
            nome="GOHAN MENESES",
            nao_matriculado=True,
        )

    def _setup_motivo_alteracao_ue(self, motivo_alteracao_ue_factory):
        self.cei_polo = motivo_alteracao_ue_factory.create(nome="Dieta Especial - Polo")
        self.recreio_nas_ferias = motivo_alteracao_ue_factory.create(
            nome="Dieta Especial - Recreio nas Férias"
        )
        self.outro = motivo_alteracao_ue_factory.create(nome="Dieta Especial - Outro")

    def setup_dieta_cei_polo(
        self,
        solicitacao_dieta_especial_factory,
        log_solicitacoes_usuario_factory,
        escola,
    ):
        self.dieta_autorizada = solicitacao_dieta_especial_factory.create(
            aluno=self.aluno_1,
            tipo_solicitacao=SolicitacaoDietaEspecial.COMUM,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            rastro_escola=escola,
            escola_destino=escola,
            classificacao=self.classificacao_tipo_a,
            ativo=False,
        )
        log_solicitacoes_usuario_factory.create(
            uuid_original=self.dieta_autorizada.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
            usuario=self.usuario_escola,
        )

        self.solicitacao_cei_polo = solicitacao_dieta_especial_factory.create(
            rastro_escola=escola,
            aluno=self.aluno_1,
            escola_destino__lote=escola.lote,
            escola_destino__diretoria_regional=escola.diretoria_regional,
            tipo_solicitacao=SolicitacaoDietaEspecial.ALTERACAO_UE,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            data_inicio="2025-12-01",
            data_termino="2025-12-10",
            dieta_alterada=self.dieta_autorizada,
            motivo_alteracao_ue=self.cei_polo,
            ativo=True,
        )
        log_solicitacoes_usuario_factory.create(
            uuid_original=self.solicitacao_cei_polo.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            solicitacao_tipo=LogSolicitacoesUsuario.DIETA_ESPECIAL,
            usuario=self.usuario_escola,
        )

    def _setup_dietas_autorizadas(
        self,
        solicitacao_dieta_especial_factory,
        log_solicitacoes_usuario_factory,
        escola,
    ):
        self.setup_dieta_cei_polo(
            solicitacao_dieta_especial_factory, log_solicitacoes_usuario_factory, escola
        )

    def _setup(
        self,
        escola,
        periodo_escolar_factory,
        usuario_factory,
        vinculo_factory,
        classificacao_dieta_factory,
        aluno_factory,
        motivo_alteracao_ue_factory,
        solicitacao_dieta_especial_factory,
        log_solicitacoes_usuario_factory,
    ):
        self._setup_periodos_escolares(periodo_escolar_factory)
        self._setup_usuario_escola(usuario_factory, vinculo_factory, escola)
        self._setup_classificacao_dieta(classificacao_dieta_factory)
        self._setup_alunos(aluno_factory, escola)
        self._setup_motivo_alteracao_ue(motivo_alteracao_ue_factory)
        self._setup_dietas_autorizadas(
            solicitacao_dieta_especial_factory, log_solicitacoes_usuario_factory, escola
        )

    def test_relatorio_dietas_autorizadas_cei_polo_recreio_e_outro(
        self,
        client_autenticado_vinculo_dre_dieta,
        escola,
        periodo_escolar_factory,
        usuario_factory,
        vinculo_factory,
        classificacao_dieta_factory,
        aluno_factory,
        motivo_alteracao_ue_factory,
        solicitacao_dieta_especial_factory,
        log_solicitacoes_usuario_factory,
    ):
        self._setup(
            escola,
            periodo_escolar_factory,
            usuario_factory,
            vinculo_factory,
            classificacao_dieta_factory,
            aluno_factory,
            motivo_alteracao_ue_factory,
            solicitacao_dieta_especial_factory,
            log_solicitacoes_usuario_factory,
        )
        client, _ = client_autenticado_vinculo_dre_dieta
        response = client.get(
            "/solicitacoes-dieta-especial/relatorio-dieta-especial-terceirizada/?limit=10&offset=0&recreio_nas_ferias=true&cei_polo=true&status_selecionado=AUTORIZADAS",
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
