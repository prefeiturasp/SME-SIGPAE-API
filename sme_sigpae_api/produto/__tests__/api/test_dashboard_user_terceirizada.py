import datetime

import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.fixtures.factories.dados_comuns_factories import (
    LogSolicitacoesUsuarioFactory,
)
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.escola.fixtures.factories.escola_factory import EscolaFactory
from sme_sigpae_api.produto.fixtures.factories.produto_factory import (
    DataHoraVinculoProdutoEditalFactory,
    HomologacaoProdutoFactory,
    ProdutoEditalFactory,
    ProdutoFactory,
    ReclamacaoDeProdutoFactory,
)
from sme_sigpae_api.produto.models import HomologacaoProduto
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EditalFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("client_autenticado_vinculo_terceirizada", "escola")
class TestDashboardGestaoProdutosTerceirizada:
    def setup_produtos(self, escola, usuario, status, status_evento, suspenso=False):
        self.edital = EditalFactory.create(numero="78/SME/2016")
        ContratoFactory.create(
            edital=self.edital,
            terceirizada=escola.lote.terceirizada,
            lotes=[escola.lote],
        )

        self.escola_2 = EscolaFactory.create()
        self.edital_2 = EditalFactory.create(numero="31/SME/2022")
        ContratoFactory.create(
            edital=self.edital_2,
            terceirizada=self.escola_2.lote.terceirizada,
            lotes=[self.escola_2.lote],
        )

        self.produto = ProdutoFactory.create(
            nome="SALSICHA", marca__nome="SADIA", fabricante__nome="FRIBOI LTDA"
        )
        self.produto_edital = ProdutoEditalFactory.create(
            produto=self.produto, edital=self.edital, suspenso=suspenso
        )
        DataHoraVinculoProdutoEditalFactory.create(
            produto_edital=self.produto_edital, suspenso=suspenso
        )
        self.homologacao_produto = HomologacaoProdutoFactory.create(
            produto=self.produto,
            rastro_terceirizada=escola.lote.terceirizada,
            status=status,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

        self.produto_2 = ProdutoFactory.create(
            nome="MACARRAO", marca__nome="ADRIA", fabricante__nome="ADRIA LTDA"
        )
        ProdutoEditalFactory.create(produto=self.produto_2, edital=self.edital_2)
        self.homologacao_produto_2 = HomologacaoProdutoFactory.create(
            produto=self.produto_2,
            rastro_terceirizada=self.escola_2.lote.terceirizada,
            status=status,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto_2.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

    def suspende_produto(self, usuario):
        self.produto_edital.suspenso = True
        self.produto_edital.save()

        DataHoraVinculoProdutoEditalFactory.create(
            produto_edital=self.produto_edital, suspenso=True
        )

        self.homologacao_produto.status = (
            HomologacaoProduto.workflow_class.CODAE_SUSPENDEU
        )
        self.homologacao_produto.save()

        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_SUSPENDEU,
            criado_em=datetime.datetime.now() + datetime.timedelta(days=1),
            usuario=usuario,
        )

    def homologa_em_outro_edital(self, usuario):
        vinculo_novo = ProdutoEditalFactory.create(
            produto=self.produto, edital=self.edital_2
        )
        DataHoraVinculoProdutoEditalFactory.create(produto_edital=vinculo_novo)

        self.homologacao_produto.status = (
            HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO
        )
        self.homologacao_produto.save()

        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto.uuid,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
            criado_em=datetime.datetime.now() + datetime.timedelta(days=2),
            usuario=usuario,
        )

    def gera_reclamacao(self, escola, usuario):
        ReclamacaoDeProdutoFactory.create(
            homologacao_produto=self.homologacao_produto, escola=escola
        )

        self.homologacao_produto.status = (
            HomologacaoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        )
        self.homologacao_produto.save()

        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto.uuid,
            status_evento=LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            criado_em=datetime.datetime.now() + datetime.timedelta(days=3),
            usuario=usuario,
        )

    def gera_reclamacao_produto_de_outra_escola(self):
        ReclamacaoDeProdutoFactory.create(
            homologacao_produto=self.homologacao_produto_2, escola=self.escola_2
        )

        self.homologacao_produto_2.status = (
            HomologacaoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        )
        self.homologacao_produto_2.save()

        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto.uuid,
            status_evento=LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            criado_em=datetime.datetime.now() + datetime.timedelta(days=3),
        )

    def test_produtos_homologados(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get("/dashboard-produtos/homologados/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_produtos_homologados_filtro_nome(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get(
            "/dashboard-produtos/homologados/?titulo_produto=SALSICHA"
        )
        assert response.status_code == status.HTTP_200_OK
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_produtos_homologados_filtro_nome_nao_encontra(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get(
            "/dashboard-produtos/homologados/?titulo_produto=PAO HOT DOG"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0

    def test_produtos_homologados_filtro_marca(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get("/dashboard-produtos/homologados/?marca_produto=SADIA")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_produtos_homologados_filtro_marca_nao_encontra(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get("/dashboard-produtos/homologados/?marca_produto=PERDIGAO")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0

    def test_produtos_homologados_filtro_suspenso_nao_encontra(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
            suspenso=True,
        )

        response = client.get("/dashboard-produtos/homologados/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0

    def test_produtos_homologados_filtro_edital(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get(
            "/dashboard-produtos/homologados/?edital_produto=78/SME/2016"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_produtos_homologados_filtro_edital_nao_encontra(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get(
            "/dashboard-produtos/homologados/?edital_produto=31/SME/2022"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0

    def test_produtos_homologados_produto_suspenso_nao_encontra(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )
        self.suspende_produto(usuario)

        response = client.get("/dashboard-produtos/homologados/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0

    def test_produtos_nao_homologados(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_NAO_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_NAO_HOMOLOGADO,
        )

        response = client.get("/dashboard-produtos/nao-homologados/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 2
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "MACARRAO"
            )
            is True
        )

    def test_produtos_suspensos(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )
        self.suspende_produto(usuario)

        response = client.get("/dashboard-produtos/suspensos/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_produtos_suspensos_nao_encontra(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )

        response = client.get("/dashboard-produtos/suspensos/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 0

    def test_produtos_suspensos_homologado_em_outro_edital(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )
        self.suspende_produto(usuario)
        self.homologa_em_outro_edital(usuario)

        response = client.get("/dashboard-produtos/suspensos/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_aguardando_analise_reclamacao(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )
        self.gera_reclamacao(escola, usuario)
        self.gera_reclamacao_produto_de_outra_escola()

        response = client.get("/dashboard-produtos/aguardando-analise-reclamacao/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_pendente_homologacao(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_PENDENTE_HOMOLOGACAO,
            status_evento=LogSolicitacoesUsuario.CODAE_PENDENTE_HOMOLOGACAO,
        )

        response = client.get("/dashboard-produtos/pendente-homologacao/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 2
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "MACARRAO"
            )
            is True
        )

    def test_correcao_de_produtos(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_QUESTIONADO,
            status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU,
        )

        response = client.get("/dashboard-produtos/correcao-de-produtos/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_aguardando_amostra_analise_sensorial(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_SENSORIAL,
            status_evento=LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL,
        )

        response = client.get(
            "/dashboard-produtos/aguardando-amostra-analise-sensorial/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def test_questionamento_da_codae(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )
        self.gera_reclamacao(escola, usuario)
        self.gera_reclamacao_produto_de_outra_escola()

        self.homologacao_produto.status = (
            HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO
        )
        self.homologacao_produto.save()

        self.homologacao_produto_2.status = (
            HomologacaoProduto.workflow_class.CODAE_PEDIU_ANALISE_RECLAMACAO
        )
        self.homologacao_produto_2.save()

        response = client.get("/dashboard-produtos/questionamento-da-codae/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )

    def inclui_novo_edital(self):
        self.edital_3 = EditalFactory.create(numero="99/SME/2025")
        self.escola_3 = EscolaFactory.create()
        ContratoFactory.create(
            edital=self.edital_3,
            terceirizada=self.escola_3.lote.terceirizada,
            lotes=[self.escola_3.lote],
        )
        ProdutoEditalFactory.create(
            produto=self.produto, edital=self.edital_3, suspenso=False
        )
        ProdutoEditalFactory.create(
            produto=self.produto_2, edital=self.edital_3, suspenso=False
        )

    def gera_reclamacao_produto_de_outra_escola_3(self):
        ReclamacaoDeProdutoFactory.create(
            homologacao_produto=self.homologacao_produto, escola=self.escola_3
        )

        self.homologacao_produto.status = (
            HomologacaoProduto.workflow_class.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        )
        self.homologacao_produto.save()

        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto_2.uuid,
            status_evento=LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
            criado_em=datetime.datetime.now() + datetime.timedelta(days=3),
        )

    def test_aguardando_analise_reclamacao_unidade_nao_atendida(
        self,
        client_autenticado_vinculo_terceirizada,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_terceirizada
        self.setup_produtos(
            escola,
            usuario,
            status=HomologacaoProduto.workflow_class.CODAE_HOMOLOGADO,
            status_evento=LogSolicitacoesUsuario.CODAE_HOMOLOGADO,
        )
        self.inclui_novo_edital()
        self.gera_reclamacao_produto_de_outra_escola_3()

        assert (
            HomologacaoProduto.objects.filter(
                reclamacoes__escola__lote__terceirizada=usuario.vinculo_atual.instituicao
            ).count()
            == 0
        )
        assert HomologacaoProduto.objects.filter(reclamacoes__isnull=False).count() == 1

        response = client.get("/dashboard-produtos/aguardando-analise-reclamacao/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["count"] == 1
        assert (
            any(
                produto
                for produto in response.json()["results"]
                if produto["nome_produto"] == "SALSICHA"
            )
            is True
        )
