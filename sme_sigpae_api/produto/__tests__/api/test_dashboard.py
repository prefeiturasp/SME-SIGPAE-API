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
)
from sme_sigpae_api.produto.models import HomologacaoProduto
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EditalFactory,
)

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("client_autenticado_vinculo_escola_ue", "escola")
class TestDashboardGestaoProdutos:
    def setup_produtos(self, escola, usuario, status, status_evento, suspenso=False):
        self.edital = EditalFactory.create(numero="78/SME/2016")
        ContratoFactory.create(
            edital=self.edital,
            terceirizada=escola.lote.terceirizada,
            lotes=[escola.lote],
        )

        escola_2 = EscolaFactory.create()
        edital_2 = EditalFactory.create(numero="31/SME/2022")
        ContratoFactory.create(
            edital=edital_2,
            terceirizada=escola_2.lote.terceirizada,
            lotes=[escola_2.lote],
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
            status=status,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=self.homologacao_produto.uuid,
            status_evento=status_evento,
            usuario=usuario,
        )

        produto_2 = ProdutoFactory.create(
            nome="MACARRAO", marca__nome="ADRIA", fabricante__nome="ADRIA LTDA"
        )
        ProdutoEditalFactory.create(produto=produto_2, edital=edital_2)
        homologacao_produto_2 = HomologacaoProdutoFactory.create(
            produto=produto_2,
            status=status,
        )
        LogSolicitacoesUsuarioFactory.create(
            uuid_original=homologacao_produto_2.uuid,
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

    def test_produtos_homologados(
        self,
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
        client_autenticado_vinculo_escola_ue,
        escola,
    ):
        client, usuario = client_autenticado_vinculo_escola_ue
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
