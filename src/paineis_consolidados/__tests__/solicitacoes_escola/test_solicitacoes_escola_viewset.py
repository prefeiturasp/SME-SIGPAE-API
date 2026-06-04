import datetime
from collections import namedtuple

import pytest
from django.db.models import Q
from freezegun.api import freeze_time
from model_bakery import baker
from rest_framework import status

from src.cardapio.alteracao_tipo_alimentacao.fixtures.factories.alteracao_tipo_alimentacao_factory import (
    AlteracaoCardapioFactory,
    DataIntervaloAlteracaoCardapioFactory,
    MotivoAlteracaoCardapioFactory,
    SubstituicaoAlimentacaoNoPeriodoEscolarFactory,
)
from src.cardapio.alteracao_tipo_alimentacao_cemei.fixtures.factories.alteracao_tipo_alimentacao_cemei_factory import (
    AlteracaoCardapioCEMEIFactory,
    DataIntervaloAlteracaoCardapioCEMEIFactory,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEIFactory,
)
from src.cardapio.base.fixtures.factories.base_factory import (
    TipoAlimentacaoFactory,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolarFactory,
)
from src.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    SolicitacaoDietaEspecialFactory,
)
from src.dieta_especial.solicitacao_dieta_especial.models import (
    SolicitacaoDietaEspecial,
)
from src.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
)
from src.inclusao_alimentacao.fixtures.factories.base_factory import (
    DiasMotivosInclusaoDeAlimentacaoCEMEIFactory,
    GrupoInclusaoAlimentacaoNormalFactory,
    InclusaoAlimentacaoContinuaFactory,
    InclusaoAlimentacaoNormalFactory,
    InclusaoDeAlimentacaoCEMEIFactory,
    MotivoInclusaoContinuaFactory,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEIFactory,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoCEMEIFactory,
    QuantidadePorPeriodoFactory,
)
from src.inclusao_alimentacao.models import GrupoInclusaoAlimentacaoNormal
from src.medicao_inicial.recreio_nas_ferias.models import RecreioNasFerias
from src.paineis_consolidados.models import SolicitacoesEscola
from src.paineis_consolidados.solicitacoes_escola.api.viewsets import (
    EscolaSolicitacoesViewSet,
)

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
            grupo_inclusao_normal=grupo_inclusao_alimentacao_normal,
            inclusao_alimentacao_continua=None,
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
            dieta_alterada = SolicitacaoDietaEspecialFactory.create()
            self.solicitacao_dieta_especial.dieta_alterada_id = dieta_alterada.id

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
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL,
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
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU_CANCELAMENTO_DIETA_ESPECIAL,
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
            dieta_alterada_id=True,
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
            dieta_alterada_id=True,
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
            dieta_alterada_id=True,
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
            dieta_alterada_id=True,
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
            f"&cemei_emei=true"
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
            f"&cemei_cei=true"
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
            f"&cemei_cei=true"
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
class TestEndpointInclusoesETecAutorizadas:
    def test_inclusoes_etec_autorizadas_respeita_encerrado_a_partir_de(
        self,
        client_autenticado_escola_paineis_consolidados,
        escola,
    ):
        client, usuario = client_autenticado_escola_paineis_consolidados
        periodo_noite = PeriodoEscolarFactory.create(nome="NOITE")
        refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        motivo_etec = MotivoInclusaoContinuaFactory.create(nome="ETEC")

        inclusao = InclusaoAlimentacaoContinuaFactory.create(
            escola=escola,
            motivo=motivo_etec,
            rastro_escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.diretoria_regional,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            data_inicial="2025-02-01",
            data_final="2025-02-10",
        )
        QuantidadePorPeriodoFactory.create(
            grupo_inclusao_normal=None,
            inclusao_alimentacao_continua=inclusao,
            periodo_escolar=periodo_noite,
            numero_alunos=10,
            encerrado_a_partir_de="2025-02-03",
            tipos_alimentacao=[refeicao],
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=inclusao.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            usuario=usuario,
        )

        response = client.get(
            "/escola-solicitacoes/inclusoes-etec-autorizadas/"
            f"?escola_uuid={escola.uuid}"
            f"&mes=02"
            f"&ano=2025"
        )

        assert response.status_code == status.HTTP_200_OK

        results = response.json()["results"]
        for result in results:
            result.pop("inclusao_id_externo")

        assert results == [
            {
                "dia": "01",
                "periodo": "NOITE",
                "alimentacoes": "refeicao",
                "tipos_alimentacao": ["Refeição"],
                "numero_alunos": 10,
            },
            {
                "dia": "02",
                "periodo": "NOITE",
                "alimentacoes": "refeicao",
                "tipos_alimentacao": ["Refeição"],
                "numero_alunos": 10,
            },
            {
                "dia": "03",
                "periodo": "NOITE",
                "alimentacoes": "refeicao",
                "tipos_alimentacao": ["Refeição"],
                "numero_alunos": 10,
            },
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
                    "periodos_escolares": ["MANHA"],
                    "tipos_alimentacao_de": ["Refeição", "Lanche"],
                },
                {
                    "dia": "02",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                    "periodos_escolares": ["MANHA"],
                    "tipos_alimentacao_de": ["Refeição", "Lanche"],
                },
                {
                    "dia": "03",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                    "periodos_escolares": ["MANHA"],
                    "tipos_alimentacao_de": ["Refeição", "Lanche"],
                },
            ]
        }

    def test_alteracoes_autorizadas_lanche_emergencial_recreio_filtra_periodo(
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

        recreio = baker.make(
            RecreioNasFerias,
            data_inicio=datetime.date(2025, 2, 2),
            data_fim=datetime.date(2025, 2, 2),
        )
        baker.make(
            "RecreioNasFeriasUnidadeParticipante",
            recreio_nas_ferias=recreio,
            unidade_educacional=escola,
            lote=escola.lote,
            liberar_medicao=True,
        )

        response = client.get(
            "/escola-solicitacoes/alteracoes-alimentacao-autorizadas/"
            f"?escola_uuid={escola.uuid}"
            f"&tipo_solicitacao=Alteração"
            f"&mes=02"
            f"&ano=2025&"
            f"eh_lanche_emergencial=true"
            f"&recreio_nas_ferias={recreio.uuid}"
            f"&nome_periodo_escolar=MANHA"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["results"] == [
            {
                "dia": "02",
                "numero_alunos": 0,
                "inclusao_id_externo": "C76CF",
                "motivo": "Lanche Emergencial",
                "periodos_escolares": ["MANHA"],
                "tipos_alimentacao_de": ["Refeição", "Lanche"],
            }
        ]

    def test_alteracoes_autorizadas_lanche_emergencial_recreio_sem_unidade_participante(
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

        recreio = baker.make(
            RecreioNasFerias,
            data_inicio=datetime.date(2025, 2, 1),
            data_fim=datetime.date(2025, 2, 3),
        )

        response = client.get(
            "/escola-solicitacoes/alteracoes-alimentacao-autorizadas/"
            f"?escola_uuid={escola.uuid}"
            f"&tipo_solicitacao=Alteração"
            f"&mes=02"
            f"&ano=2025&"
            f"eh_lanche_emergencial=true"
            f"&recreio_nas_ferias={recreio.uuid}"
            f"&nome_periodo_escolar=MANHA"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"results": []}


@pytest.mark.usefixtures("client_autenticado_vinculo_escola_cemei", "escola_cemei")
@freeze_time("2025-02-05")
class TestEndpointAlteracoesAutorizadasCEMEI:
    def setup_solicitacoes(
        self,
        escola_cemei,
        usuario,
        status,
        status_evento,
    ):
        motivo_lanche_emergencial = MotivoAlteracaoCardapioFactory.create(
            nome="Lanche Emergencial"
        )
        periodo_manha = PeriodoEscolarFactory.create(nome="MANHA")
        refeicao = TipoAlimentacaoFactory.create(nome="Refeição")
        lanche = TipoAlimentacaoFactory.create(nome="Lanche")
        lanche_emergencial = TipoAlimentacaoFactory.create(nome="Lanche Emergencial")

        alteracao_tipo_alimentacao_lanche_emergencial = (
            AlteracaoCardapioCEMEIFactory.create(
                escola=escola_cemei,
                rastro_escola=escola_cemei,
                rastro_dre=escola_cemei.diretoria_regional,
                rastro_lote=escola_cemei.lote,
                motivo=motivo_lanche_emergencial,
                data_inicial="2025-02-01",
                data_final="2025-02-03",
                status=status,
                uuid="c76cfacc-f1cb-4ad6-86a3-5a2dc8dc3cd7",
            )
        )
        for dia in ["01", "02", "03"]:
            DataIntervaloAlteracaoCardapioCEMEIFactory.create(
                alteracao_cardapio_cemei=alteracao_tipo_alimentacao_lanche_emergencial,
                data=f"2025-02-{dia}",
            )
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEIFactory.create(
            alteracao_cardapio=alteracao_tipo_alimentacao_lanche_emergencial,
            periodo_escolar=periodo_manha,
            tipos_alimentacao_de=[refeicao, lanche],
            tipos_alimentacao_para=[lanche_emergencial],
            qtd_alunos=0,
            matriculados_quando_criado=0,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=alteracao_tipo_alimentacao_lanche_emergencial.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def test_alteracoes_autorizadas_lanche_emergencial_cemei(
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
            "/escola-solicitacoes/alteracoes-alimentacao-autorizadas/"
            f"?escola_uuid={escola_cemei.uuid}"
            f"&tipo_solicitacao=Alteração"
            f"&mes=02"
            f"&ano=2025&"
            f"eh_lanche_emergencial=true"
            f"&nome_periodo_escolar=Infantil+MANHA"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "results": [
                {
                    "dia": "01",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                    "periodos_escolares": ["MANHA"],
                    "tipos_alimentacao_de": ["Refeição", "Lanche"],
                },
                {
                    "dia": "02",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                    "periodos_escolares": ["MANHA"],
                    "tipos_alimentacao_de": ["Refeição", "Lanche"],
                },
                {
                    "dia": "03",
                    "numero_alunos": 0,
                    "inclusao_id_externo": "C76CF",
                    "motivo": "Lanche Emergencial",
                    "periodos_escolares": ["MANHA"],
                    "tipos_alimentacao_de": ["Refeição", "Lanche"],
                },
            ]
        }

    def test_alteracoes_autorizadas_lanche_emergencial_cemei_recreio_filtra_periodo(
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

        recreio = baker.make(
            RecreioNasFerias,
            data_inicio=datetime.date(2025, 2, 2),
            data_fim=datetime.date(2025, 2, 2),
        )
        baker.make(
            "RecreioNasFeriasUnidadeParticipante",
            recreio_nas_ferias=recreio,
            unidade_educacional=escola_cemei,
            lote=escola_cemei.lote,
            liberar_medicao=True,
        )

        response = client.get(
            "/escola-solicitacoes/alteracoes-alimentacao-autorizadas/"
            f"?escola_uuid={escola_cemei.uuid}"
            f"&tipo_solicitacao=Alteração"
            f"&mes=02"
            f"&ano=2025&"
            f"eh_lanche_emergencial=true"
            f"&recreio_nas_ferias={recreio.uuid}"
            f"&nome_periodo_escolar=Infantil+MANHA"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["results"] == [
            {
                "dia": "02",
                "numero_alunos": 0,
                "inclusao_id_externo": "C76CF",
                "motivo": "Lanche Emergencial",
                "periodos_escolares": ["MANHA"],
                "tipos_alimentacao_de": ["Refeição", "Lanche"],
            }
        ]


@freeze_time("2025-06-30")
def test_url_endpoint_suspensoes_autorizadas_maio(
    client_autenticado_escola_paineis_consolidados, grupo_suspensao_alimentacao
):
    client, _ = client_autenticado_escola_paineis_consolidados
    params = {
        "escola_uuid": grupo_suspensao_alimentacao.escola.uuid,
        "tipo_solicitacao": "Suspensão",
        "mes": "05",
        "ano": "2025",
        "nome_periodo_escolar": "MANHA",
    }

    response = client.get("/escola-solicitacoes/suspensoes-autorizadas/", params)
    assert response.status_code == status.HTTP_200_OK
    resultados = response.json()["results"]

    assert len(resultados) == 3
    dias_resultado = {item["dia"] for item in resultados}
    assert {"10", "15", "20"}.issubset(dias_resultado)


@freeze_time("2025-06-30")
def test_url_endpoint_suspensoes_autorizadas_junho(
    client_autenticado_escola_paineis_consolidados, grupo_suspensao_alimentacao
):
    client, _ = client_autenticado_escola_paineis_consolidados
    params = {
        "escola_uuid": grupo_suspensao_alimentacao.escola.uuid,
        "tipo_solicitacao": "Suspensão",
        "mes": "06",
        "ano": "2025",
        "nome_periodo_escolar": "MANHA",
    }

    response = client.get("/escola-solicitacoes/suspensoes-autorizadas/", params)
    assert response.status_code == status.HTTP_200_OK
    resultados = response.json()["results"]

    assert len(resultados) == 1
    assert resultados[0]["dia"] == "05"


def test_busca_filtro_tipo_solicitacao_kit_lanche_isolado(monkeypatch, escola):
    """
    Isola busca_filtro para validar o comportamento quando tipo_solicitacao='Kit Lanche':
    - Patch dos métodos auxiliares para que apenas busca_por_tipo_solicitacao aplique o filtro.
    - Valida que o resultado final contém somente UNIFICADA e CEMEI.
    """
    Linha = namedtuple(
        "Linha",
        [
            "uuid",
            "escola_uuid",
            "data_evento",
            "tipo_doc",
            "desc_doc",
            "status_evento",
            "status_atual",
        ],
    )

    linhas = [
        Linha(
            uuid="uuid-unificada",
            escola_uuid=escola.uuid,
            data_evento=datetime.date(2024, 12, 16),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
            desc_doc="Kit Lanche Unificado",
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            status_atual="CODAE_AUTORIZADO",
        ),
        Linha(
            uuid="uuid-cemei",
            escola_uuid=escola.uuid,
            data_evento=datetime.date(2024, 12, 15),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
            desc_doc="Kit Lanche CEMEI",
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            status_atual="CODAE_AUTORIZADO",
        ),
        Linha(
            uuid="uuid-alteracao-cardapio",
            escola_uuid=escola.uuid,
            data_evento=datetime.date(2024, 12, 14),
            tipo_doc="ALT_CARDAPIO",
            desc_doc="Alteração de Cardápio",
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            status_atual="CODAE_AUTORIZADO",
        ),
        Linha(
            uuid="uuid-inclusao-alimentacao",
            escola_uuid=escola.uuid,
            data_evento=datetime.date(2024, 12, 13),
            tipo_doc="INC_ALIMENTA",
            desc_doc="Inclusão de Alimentação",
            status_evento=LogSolicitacoesUsuario.CODAE_AUTORIZOU,
            status_atual="CODAE_AUTORIZADO",
        ),
    ]

    class FakeQS:
        def __init__(self, items):
            self.items = list(items)

        def filter(self, **kwargs):
            if "tipo_doc__in" in kwargs:
                tipos = set(kwargs["tipo_doc__in"])
                return FakeQS([x for x in self.items if x.tipo_doc in tipos])
            return FakeQS(self.items)

        def __iter__(self):
            return iter(self.items)

        def __len__(self):
            return len(self.items)

        def __getitem__(self, idx):
            return self.items[idx]

    qs = FakeQS(linhas)

    monkeypatch.setattr(
        SolicitacoesEscola,
        "excluir_inclusoes_continuas",
        classmethod(lambda cls, qs, params: qs),
    )
    monkeypatch.setattr(
        SolicitacoesEscola,
        "filtrar_tipo_doc",
        classmethod(lambda cls, qs, params: qs),
    )

    def fake_busca_por_tipo_solicitacao(cls, qs_arg, params):
        if params.get("tipo_solicitacao") == "Kit Lanche":
            return qs_arg.filter(
                tipo_doc__in=[
                    SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
                    SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
                ]
            )
        return qs_arg

    monkeypatch.setattr(
        SolicitacoesEscola,
        "busca_por_tipo_solicitacao",
        classmethod(fake_busca_por_tipo_solicitacao),
    )
    monkeypatch.setattr(
        SolicitacoesEscola,
        "busca_data_evento",
        classmethod(lambda cls, qs, params: qs),
    )

    resultado = SolicitacoesEscola.busca_filtro(qs, {"tipo_solicitacao": "Kit Lanche"})
    resultado_lista = list(resultado)

    tipos_validos = {
        SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
        SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
    }
    assert len(resultado_lista) == 2
    assert {item.tipo_doc for item in resultado_lista} == tipos_validos


@freeze_time("2026-03-20")
def test_kit_lanches_autorizadas_recreio_sem_unidade_participante(
    client_autenticado_escola_paineis_consolidados,
    escola,
):
    client, _ = client_autenticado_escola_paineis_consolidados

    recreio = baker.make(
        RecreioNasFerias,
        data_inicio=datetime.date(2026, 3, 10),
        data_fim=datetime.date(2026, 3, 15),
    )

    params = {
        "escola_uuid": str(escola.uuid),
        "mes": "03",
        "ano": "2026",
        "tipo_solicitacao": "Kit Lanche",
        "recreio_nas_ferias": str(recreio.uuid),
    }

    response = client.get("/escola-solicitacoes/kit-lanches-autorizadas/", params)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"results": []}


@freeze_time("2026-03-20")
def test_kit_lanches_autorizadas_recreio_liberar_medicao_false(
    client_autenticado_escola_paineis_consolidados,
    escola,
):
    client, _ = client_autenticado_escola_paineis_consolidados

    recreio = baker.make(
        RecreioNasFerias,
        data_inicio=datetime.date(2026, 3, 10),
        data_fim=datetime.date(2026, 3, 15),
    )
    baker.make(
        "RecreioNasFeriasUnidadeParticipante",
        recreio_nas_ferias=recreio,
        unidade_educacional=escola,
        lote=escola.lote,
        liberar_medicao=False,
    )

    params = {
        "escola_uuid": str(escola.uuid),
        "mes": "03",
        "ano": "2026",
        "tipo_solicitacao": "Kit Lanche",
        "recreio_nas_ferias": str(recreio.uuid),
    }

    response = client.get("/escola-solicitacoes/kit-lanches-autorizadas/", params)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"results": []}


@freeze_time("2026-03-20")
def test_kit_lanches_autorizadas_recreio_filtra_periodo_para_todos_tipos(
    client_autenticado_escola_paineis_consolidados,
    escola,
    monkeypatch,
):
    client, _ = client_autenticado_escola_paineis_consolidados

    recreio = baker.make(
        RecreioNasFerias,
        data_inicio=datetime.date(2026, 3, 10),
        data_fim=datetime.date(2026, 3, 15),
    )
    baker.make(
        "RecreioNasFeriasUnidadeParticipante",
        recreio_nas_ferias=recreio,
        unidade_educacional=escola,
        lote=escola.lote,
        liberar_medicao=True,
    )

    Linha = namedtuple("Linha", ["uuid", "data_evento", "tipo_doc"])

    linhas = [
        Linha(
            uuid="uuid-kit-padrao",
            data_evento=datetime.date(2026, 3, 12),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_AVULSA,
        ),
        Linha(
            uuid="uuid-kit-cemei",
            data_evento=datetime.date(2026, 3, 13),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
        ),
        Linha(
            uuid="uuid-kit-unificado",
            data_evento=datetime.date(2026, 3, 14),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
        ),
        Linha(
            uuid="uuid-fora-antes",
            data_evento=datetime.date(2026, 3, 9),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_AVULSA,
        ),
        Linha(
            uuid="uuid-fora-depois",
            data_evento=datetime.date(2026, 3, 16),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
        ),
    ]

    class FakeQS:
        def __init__(self, items):
            self.items = list(items)

        def _matches_q(self, item, q_object):
            resultados = []
            for filho in q_object.children:
                if isinstance(filho, Q):
                    resultados.append(self._matches_q(item, filho))
                    continue

                lookup, value = filho
                if lookup == "data_evento__lt":
                    resultados.append(item.data_evento < value)
                elif lookup == "data_evento__gt":
                    resultados.append(item.data_evento > value)
                elif lookup == "data_evento__lte":
                    resultados.append(item.data_evento <= value)
                elif lookup == "data_evento__gte":
                    resultados.append(item.data_evento >= value)
                else:
                    raise AssertionError(f"Lookup não suportado no teste: {lookup}")

            if q_object.connector == "AND":
                matched = all(resultados)
            else:
                matched = any(resultados)

            return not matched if q_object.negated else matched

        def filter(self, *args, **kwargs):
            filtrados = self.items
            for q_object in args:
                filtrados = [x for x in filtrados if self._matches_q(x, q_object)]

            for lookup, value in kwargs.items():
                if lookup == "data_evento__month":
                    filtrados = [
                        x for x in filtrados if x.data_evento.month == int(value)
                    ]
                elif lookup == "data_evento__year":
                    filtrados = [
                        x for x in filtrados if x.data_evento.year == int(value)
                    ]
                elif lookup == "data_evento__lt":
                    filtrados = [x for x in filtrados if x.data_evento < value]
                elif lookup == "data_evento__gt":
                    filtrados = [x for x in filtrados if x.data_evento > value]
                elif lookup == "data_evento__gte":
                    filtrados = [x for x in filtrados if x.data_evento >= value]
                elif lookup == "data_evento__lte":
                    filtrados = [x for x in filtrados if x.data_evento <= value]
            return FakeQS(filtrados)

        def __iter__(self):
            return iter(self.items)

    fake_qs = FakeQS(linhas)

    monkeypatch.setattr(
        SolicitacoesEscola,
        "get_autorizados",
        classmethod(lambda cls, escola_uuid=None: fake_qs),
    )
    monkeypatch.setattr(
        SolicitacoesEscola,
        "busca_filtro",
        classmethod(lambda cls, qs, params: qs),
    )
    monkeypatch.setattr(
        EscolaSolicitacoesViewSet,
        "remove_duplicados_do_query_set",
        lambda self, qs: qs,
    )
    monkeypatch.setattr(
        EscolaSolicitacoesViewSet,
        "_build_results_kit_lanches",
        lambda self, qs, escola_uuid: [
            {"kit_lanche_id_externo": item.uuid, "tipo_doc": item.tipo_doc}
            for item in qs
        ],
    )

    params = {
        "escola_uuid": str(escola.uuid),
        "mes": "03",
        "ano": "2026",
        "tipo_solicitacao": "Kit Lanche",
        "recreio_nas_ferias": str(recreio.uuid),
    }
    response = client.get("/escola-solicitacoes/kit-lanches-autorizadas/", params)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": [
            {
                "kit_lanche_id_externo": "uuid-kit-padrao",
                "tipo_doc": SolicitacoesEscola.TP_SOL_KIT_LANCHE_AVULSA,
            },
            {
                "kit_lanche_id_externo": "uuid-kit-cemei",
                "tipo_doc": SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
            },
            {
                "kit_lanche_id_externo": "uuid-kit-unificado",
                "tipo_doc": SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
            },
        ]
    }


@freeze_time("2026-03-20")
def test_kit_lanches_autorizadas_sem_recreio_exclui_periodo_de_recreio_para_todos_tipos(
    client_autenticado_escola_paineis_consolidados,
    escola,
    monkeypatch,
):
    client, _ = client_autenticado_escola_paineis_consolidados

    recreio = baker.make(
        RecreioNasFerias,
        data_inicio=datetime.date(2026, 3, 3),
        data_fim=datetime.date(2026, 3, 10),
    )
    baker.make(
        "RecreioNasFeriasUnidadeParticipante",
        recreio_nas_ferias=recreio,
        unidade_educacional=escola,
        lote=escola.lote,
        liberar_medicao=True,
    )

    Linha = namedtuple("Linha", ["uuid", "data_evento", "tipo_doc"])

    linhas = [
        Linha(
            uuid="uuid-fora-padrao",
            data_evento=datetime.date(2026, 3, 1),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_AVULSA,
        ),
        Linha(
            uuid="uuid-dentro-padrao",
            data_evento=datetime.date(2026, 3, 5),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_AVULSA,
        ),
        Linha(
            uuid="uuid-fora-cemei",
            data_evento=datetime.date(2026, 3, 2),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
        ),
        Linha(
            uuid="uuid-dentro-cemei",
            data_evento=datetime.date(2026, 3, 6),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
        ),
        Linha(
            uuid="uuid-fora-unificado",
            data_evento=datetime.date(2026, 3, 11),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
        ),
        Linha(
            uuid="uuid-dentro-unificado",
            data_evento=datetime.date(2026, 3, 8),
            tipo_doc=SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
        ),
    ]

    class FakeQS:
        def __init__(self, items):
            self.items = list(items)

        def _matches_q(self, item, q_object):
            resultados = []
            for filho in q_object.children:
                if isinstance(filho, Q):
                    resultados.append(self._matches_q(item, filho))
                    continue

                lookup, value = filho
                if lookup == "data_evento__lt":
                    resultados.append(item.data_evento < value)
                elif lookup == "data_evento__gt":
                    resultados.append(item.data_evento > value)
                elif lookup == "data_evento__lte":
                    resultados.append(item.data_evento <= value)
                elif lookup == "data_evento__gte":
                    resultados.append(item.data_evento >= value)
                else:
                    raise AssertionError(f"Lookup não suportado no teste: {lookup}")

            if q_object.connector == "AND":
                matched = all(resultados)
            else:
                matched = any(resultados)

            return not matched if q_object.negated else matched

        def filter(self, *args, **kwargs):
            filtrados = self.items
            for q_object in args:
                filtrados = [x for x in filtrados if self._matches_q(x, q_object)]

            for lookup, value in kwargs.items():
                if lookup == "data_evento__month":
                    filtrados = [
                        x for x in filtrados if x.data_evento.month == int(value)
                    ]
                elif lookup == "data_evento__year":
                    filtrados = [
                        x for x in filtrados if x.data_evento.year == int(value)
                    ]
                elif lookup == "data_evento__lt":
                    filtrados = [x for x in filtrados if x.data_evento < value]
                elif lookup == "data_evento__gt":
                    filtrados = [x for x in filtrados if x.data_evento > value]
                elif lookup == "data_evento__gte":
                    filtrados = [x for x in filtrados if x.data_evento >= value]
                elif lookup == "data_evento__lte":
                    filtrados = [x for x in filtrados if x.data_evento <= value]

            return FakeQS(filtrados)

        def __iter__(self):
            return iter(self.items)

    fake_qs = FakeQS(linhas)

    monkeypatch.setattr(
        SolicitacoesEscola,
        "get_autorizados",
        classmethod(lambda cls, escola_uuid=None: fake_qs),
    )
    monkeypatch.setattr(
        SolicitacoesEscola,
        "busca_filtro",
        classmethod(lambda cls, qs, params: qs),
    )
    monkeypatch.setattr(
        EscolaSolicitacoesViewSet,
        "remove_duplicados_do_query_set",
        lambda self, qs: qs,
    )
    monkeypatch.setattr(
        EscolaSolicitacoesViewSet,
        "_build_results_kit_lanches",
        lambda self, qs, escola_uuid: [
            {"kit_lanche_id_externo": item.uuid, "tipo_doc": item.tipo_doc}
            for item in qs
        ],
    )

    params = {
        "escola_uuid": str(escola.uuid),
        "mes": "03",
        "ano": "2026",
        "tipo_solicitacao": "Kit Lanche",
    }
    response = client.get("/escola-solicitacoes/kit-lanches-autorizadas/", params)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": [
            {
                "kit_lanche_id_externo": "uuid-fora-padrao",
                "tipo_doc": SolicitacoesEscola.TP_SOL_KIT_LANCHE_AVULSA,
            },
            {
                "kit_lanche_id_externo": "uuid-fora-cemei",
                "tipo_doc": SolicitacoesEscola.TP_SOL_KIT_LANCHE_CEMEI,
            },
            {
                "kit_lanche_id_externo": "uuid-fora-unificado",
                "tipo_doc": SolicitacoesEscola.TP_SOL_KIT_LANCHE_UNIFICADA,
            },
        ]
    }
