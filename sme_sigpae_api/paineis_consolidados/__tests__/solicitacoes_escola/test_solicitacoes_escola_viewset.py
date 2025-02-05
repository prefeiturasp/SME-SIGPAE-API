import datetime

import pytest
from freezegun.api import freeze_time
from rest_framework import status

from sme_sigpae_api.cardapio.fixtures.factories.alteracao_cardapio_factory import (
    AlteracaoCardapioFactory,
    DataIntervaloAlteracaoCardapioFactory,
    MotivoAlteracaoCardapioFactory,
    SubstituicaoAlimentacaoNoPeriodoEscolarFactory,
)
from sme_sigpae_api.cardapio.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory,
)
from sme_sigpae_api.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    SolicitacaoDietaEspecialFactory,
)
from sme_sigpae_api.dieta_especial.models import SolicitacaoDietaEspecial
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.inclusao_alimentacao.fixtures.factories.base_factory import (
    DiasMotivosInclusaoDeAlimentacaoCEMEIFactory,
    GrupoInclusaoAlimentacaoNormalFactory,
    InclusaoAlimentacaoNormalFactory,
    InclusaoDeAlimentacaoCEMEIFactory,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEIFactory,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEIFactory,
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


@pytest.mark.usefixtures("client_autenticado_escola_paineis_consolidados", "escola")
class TestEndpointsPainelGerencialDietaEspecialEscola:
    def setup_dieta_alterada_id(self, dieta_alterada_id):
        if dieta_alterada_id:
            SolicitacaoDietaEspecialFactory.create(id=dieta_alterada_id)
            self.solicitacao_dieta_especial.dieta_alterada_id = dieta_alterada_id

    def setup_em_vigencia(self, em_vigencia):
        if em_vigencia is True:
            data_inicio = datetime.date.today() - datetime.timedelta(days=1)
            data_termino = datetime.date.today() + datetime.timedelta(days=1)
            self.solicitacao_dieta_especial.data_inicio = data_inicio
            self.solicitacao_dieta_especial.data_termino = data_termino
            self.solicitacao_dieta_especial.save()
        if em_vigencia is False:
            data_inicio = datetime.date.today() + datetime.timedelta(days=1)
            data_termino = datetime.date.today() + datetime.timedelta(days=2)
            self.solicitacao_dieta_especial.data_inicio = data_inicio
            self.solicitacao_dieta_especial.data_termino = data_termino
            self.solicitacao_dieta_especial.save()

    def setup_solicitacoes(
        self,
        usuario,
        escola,
        status,
        status_evento,
        dieta_alterada_id=None,
        em_vigencia=None,
    ):
        aluno = AlunoFactory.create(codigo_eol="1234567")

        self.solicitacao_dieta_especial = SolicitacaoDietaEspecialFactory.create(
            aluno=aluno,
            ativo=True,
            status=status,
            rastro_escola=escola,
            escola_destino=escola,
        )
        self.setup_dieta_alterada_id(dieta_alterada_id)
        self.setup_em_vigencia(em_vigencia)

        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.solicitacao_dieta_especial.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def setup_solicitacoes_inativas(
        self, usuario, escola, status, status_evento, temporariamente=False
    ):
        aluno = AlunoFactory.create(codigo_eol="1234567")

        self.solicitacao_dieta_especial = SolicitacaoDietaEspecialFactory.create(
            aluno=aluno,
            ativo=False,
            status=status,
            rastro_escola=escola,
        )
        SolicitacaoDietaEspecialFactory.create(
            aluno=aluno,
            tipo_solicitacao="ALTERACAO_UE",
            dieta_alterada=self.solicitacao_dieta_especial if temporariamente else None,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.solicitacao_dieta_especial.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def test_pendentes_autorizacao_dieta_especial(
        self,
        escola,
        client_autenticado_escola_paineis_consolidados,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        )

        response = client.get(
            f"/escola-solicitacoes/pendentes-autorizacao-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_pendentes_autorizacao_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_A_AUTORIZAR,
            status_evento=LogSolicitacoesUsuario.INICIO_FLUXO,
        )

        response = client.get(
            f"/escola-solicitacoes/pendentes-autorizacao-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) == 1

    def test_autorizados_dieta_especial(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        )

        response = client.get(
            f"/escola-solicitacoes/autorizados-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_autorizados_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        )

        response = client.get(
            f"/escola-solicitacoes/autorizados-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) == 1

    def test_negados_dieta_especial(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_NEGOU_PEDIDO,
            status_evento=LogSolicitacoesUsuario.CODAE_NEGOU,
        )

        response = client.get(
            f"/escola-solicitacoes/negados-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_negados_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_NEGOU_PEDIDO,
            status_evento=LogSolicitacoesUsuario.CODAE_NEGOU,
        )

        response = client.get(
            f"/escola-solicitacoes/negados-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) == 1

    def test_cancelados_dieta_especial(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.ESCOLA_CANCELOU,
            status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
        )

        response = client.get(
            f"/escola-solicitacoes/cancelados-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_cancelados_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.ESCOLA_CANCELOU,
            status_evento=LogSolicitacoesUsuario.ESCOLA_CANCELOU,
        )

        response = client.get(
            f"/escola-solicitacoes/cancelados-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) == 1

    def test_autorizadas_temporariamente_dieta_especial(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            dieta_alterada_id=1,
            em_vigencia=True,
        )

        response = client.get(
            f"/escola-solicitacoes/autorizadas-temporariamente-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_autorizadas_temporariamente_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            dieta_alterada_id=2,
            em_vigencia=True,
        )

        response = client.get(
            f"/escola-solicitacoes/autorizadas-temporariamente-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) > 0

    def test_aguardando_inicio_vigencia_dieta_especial(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            dieta_alterada_id=1,
            em_vigencia=False,
        )

        response = client.get(
            f"/escola-solicitacoes/aguardando-vigencia-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_aguardando_inicio_vigencia_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            dieta_alterada_id=3,
            em_vigencia=False,
        )

        response = client.get(
            f"/escola-solicitacoes/aguardando-vigencia-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) > 0

    def test_inativas_temporariamente_dieta_especial(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes_inativas(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            temporariamente=True,
        )

        response = client.get(
            f"/escola-solicitacoes/inativas-temporariamente-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_inativas_temporariamente_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes_inativas(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            temporariamente=True,
        )

        response = client.get(
            f"/escola-solicitacoes/inativas-temporariamente-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) == 1

    def test_inativas_dieta_especial(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes_inativas(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZOU_INATIVACAO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
        )

        response = client.get(
            f"/escola-solicitacoes/inativas-dieta/{escola.uuid}/?limit=6&offset=0"
        )
        assert response.json()["count"] == 1

    def test_inativas_dieta_especial_sem_paginacao(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados

        self.setup_solicitacoes_inativas(
            usuario,
            escola,
            status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZOU_INATIVACAO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_INATIVACAO,
        )

        response = client.get(
            f"/escola-solicitacoes/inativas-dieta/{escola.uuid}/?sem_paginacao=true"
        )
        assert "count" not in response.json()
        assert len(response.json()["results"]) == 1


@pytest.mark.usefixtures("client_autenticado_vinculo_escola_cemei", "escola_cemei")
@freeze_time("2025-02-05")
class TestEndpointInclusoesAutorizadas:
    def setup_solicitacoes(
        self,
        escola_cemei,
        usuario,
        status,
        status_evento,
    ):
        self.faixa_etaria = FaixaEtariaFactory.create(inicio=0, fim=1)
        periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        periodo_integral = PeriodoEscolarFactory.create(nome="INTEGRAL")
        refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory.create(
            tipo_unidade_escolar__iniciais="EMEI",
            periodo_escolar=periodo_manha,
            tipos_alimentacao=[refeicao],
        )
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory.create(
            tipo_unidade_escolar__iniciais="EMEI",
            periodo_escolar=periodo_integral,
            tipos_alimentacao=[refeicao],
        )

        inclusao_alimentacao_cemei = InclusaoDeAlimentacaoCEMEIFactory.create(
            escola=escola_cemei,
            rastro_escola=escola_cemei,
            rastro_lote=escola_cemei.lote,
            rastro_dre=escola_cemei.diretoria_regional,
            status=status,
        )
        QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=inclusao_alimentacao_cemei,
            faixa_etaria=self.faixa_etaria,
            matriculados_quando_criado=10,
            quantidade_alunos=10,
            periodo_escolar=periodo_integral,
        )
        QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=inclusao_alimentacao_cemei,
            matriculados_quando_criado=20,
            quantidade_alunos=20,
            periodo_escolar=periodo_manha,
            tipos_alimentacao=[refeicao],
        )
        DiasMotivosInclusaoDeAlimentacaoCEMEIFactory.create(
            inclusao_alimentacao_cemei=inclusao_alimentacao_cemei, data="2025-02-03"
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=inclusao_alimentacao_cemei.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def test_inclusoes_autorizadas_infantil(
        self,
        client_autenticado_vinculo_escola_cemei,
        escola_cemei,
    ):
        client, usuario = client_autenticado_vinculo_escola_cemei
        self.setup_solicitacoes(
            escola_cemei,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        )

        response = client.get(
            "/escola-solicitacoes/inclusoes-autorizadas/"
            f"?escola_uuid={escola_cemei.uuid}"
            f"&tipo_solicitacao=Inclus%C3%A3o+de"
            f"&mes=2"
            f"&ano=2025"
            f"&periodos_escolares[]=Infantil+MANHA"
            f"&excluir_inclusoes_continuas=true"
        )

        assert response.status_code == status.HTTP_200_OK

        results = response.json()["results"]
        results[0].pop("inclusao_id_externo")
        assert results == [
            {
                "dia": "03",
                "periodo": "MANHA",
                "alimentacoes": "refeicao",
                "numero_alunos": 20,
                "dias_semana": None,
            }
        ]

    def test_inclusoes_autorizadas_parcial(
        self,
        client_autenticado_vinculo_escola_cemei,
        escola_cemei,
    ):
        client, usuario = client_autenticado_vinculo_escola_cemei
        self.setup_solicitacoes(
            escola_cemei,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        )

        response = client.get(
            "/escola-solicitacoes/inclusoes-autorizadas/"
            f"?escola_uuid={escola_cemei.uuid}"
            f"&tipo_solicitacao=Inclus%C3%A3o+de"
            f"&mes=2"
            f"&ano=2025"
            f"&periodos_escolares[]=PARCIAL"
            f"&excluir_inclusoes_continuas=true"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["results"] == [
            {
                "dia": 3,
                "eh_parcial_integral": True,
                "faixas_etarias": [str(self.faixa_etaria.uuid)],
            }
        ]

    def test_inclusoes_autorizadas_integral(
        self,
        client_autenticado_vinculo_escola_cemei,
        escola_cemei,
    ):
        client, usuario = client_autenticado_vinculo_escola_cemei
        self.setup_solicitacoes(
            escola_cemei,
            usuario,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
        )

        response = client.get(
            "/escola-solicitacoes/inclusoes-autorizadas/"
            f"?escola_uuid={escola_cemei.uuid}"
            f"&tipo_solicitacao=Inclus%C3%A3o+de"
            f"&mes=2"
            f"&ano=2025"
            f"&periodos_escolares[]=INTEGRAL"
            f"&excluir_inclusoes_continuas=true"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["results"] == [
            {
                "dia": 3,
                "eh_parcial_integral": False,
                "faixas_etarias": [str(self.faixa_etaria.uuid)],
            }
        ]


@pytest.mark.usefixtures("client_autenticado_escola_paineis_consolidados", "escola")
@freeze_time("2025-02-05")
class TestEndpointAlteracoesAutorizadas:
    def setup_solicitacoes(
        self,
        escola,
        usuario,
        status,
        status_evento,
    ):
        motivo_rpl = MotivoAlteracaoCardapioFactory.create(
            nome="RPL - Refeição por Lanche"
        )
        motivo_lanche_emergencial = MotivoAlteracaoCardapioFactory.create(
            nome="Lanche Emergencial"
        )
        periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        lanche = TipoAlimentacaoFactory.create(nome="Lanche")
        lanche_emergencial = TipoAlimentacaoFactory.create(nome="Lanche Emergencial")

        self.alteracao_tipo_alimentacao_rpl = AlteracaoCardapioFactory.create(
            escola=escola,
            rastro_escola=escola,
            rastro_dre=escola.diretoria_regional,
            rastro_lote=escola.lote,
            motivo=motivo_rpl,
            data_inicial="2025-02-01",
            data_final="2025-02-01",
            status=status,
            uuid="044d9980-30e7-46f4-b329-c2cc406ef999",
        )
        DataIntervaloAlteracaoCardapioFactory.create(
            alteracao_cardapio=self.alteracao_tipo_alimentacao_rpl, data=f"2025-02-01"
        )
        SubstituicaoAlimentacaoNoPeriodoEscolarFactory.create(
            alteracao_cardapio=self.alteracao_tipo_alimentacao_rpl,
            periodo_escolar=periodo_manha,
            tipos_alimentacao_de=[refeicao],
            tipos_alimentacao_para=[lanche],
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.alteracao_tipo_alimentacao_rpl.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

        alteracao_tipo_alimentacao_lanche_emergencial = AlteracaoCardapioFactory.create(
            escola=escola,
            rastro_escola=escola,
            rastro_dre=escola.diretoria_regional,
            rastro_lote=escola.lote,
            motivo=motivo_lanche_emergencial,
            data_inicial="2025-02-01",
            data_final="2025-02-03",
            status=status,
            uuid="c76cfacc-f1cb-4ad6-86a3-5a2dc8dc3cd7",
        )
        for dia in ["01", "02", "03"]:
            DataIntervaloAlteracaoCardapioFactory.create(
                alteracao_cardapio=alteracao_tipo_alimentacao_lanche_emergencial,
                data=f"2025-02-{dia}",
            )
        SubstituicaoAlimentacaoNoPeriodoEscolarFactory.create(
            alteracao_cardapio=alteracao_tipo_alimentacao_lanche_emergencial,
            periodo_escolar=periodo_manha,
            tipos_alimentacao_de=[refeicao, lanche],
            tipos_alimentacao_para=[lanche_emergencial],
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=alteracao_tipo_alimentacao_lanche_emergencial.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def test_alteracoes_autorizadas_rpl(
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

        response = client.get(
            "/escola-solicitacoes/alteracoes-alimentacao-autorizadas/"
            f"?escola_uuid={escola.uuid}"
            f"&tipo_solicitacao=Alteração"
            f"&mes=02"
            f"&ano=2025&"
            f"eh_lanche_emergencial=false"
            f"&nome_periodo_escolar=MANHA"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["results"] == [
            {
                "dia": "01",
                "periodo": "MANHA",
                "numero_alunos": 0,
                "inclusao_id_externo": "044D9",
                "motivo": "RPL - Refeição por Lanche",
            }
        ]

    def test_alteracoes_autorizadas_lanche_emergencial(
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

        response = client.get(
            "/escola-solicitacoes/alteracoes-alimentacao-autorizadas/"
            f"?escola_uuid={escola.uuid}"
            f"&tipo_solicitacao=Alteração"
            f"&mes=02"
            f"&ano=2025&"
            f"eh_lanche_emergencial=true"
            f"&nome_periodo_escolar=MANHA"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "results": [
                {
                    "dia": "01",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                },
                {
                    "dia": "02",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                },
                {
                    "dia": "03",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                },
            ]
        }
