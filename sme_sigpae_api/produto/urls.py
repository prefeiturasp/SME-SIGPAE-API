from django.urls import include, path
from rest_framework import routers

from .api import viewsets
from .api.dashboard_viewset import HomologacaoProdutoDashboardViewSet

router = routers.DefaultRouter()

router.register("produtos", viewsets.ProdutoViewSet, "Produtos")
router.register(
    "produtos-editais", viewsets.ProdutosEditaisViewSet, "Produtos vinculados a editais"
)
router.register(
    "nome-de-produtos-edital",
    viewsets.NomeDeProdutoEditalViewSet,
    "Nome de Produto Edital",
)
router.register(
    "cadastro-produtos-edital",
    viewsets.CadastroProdutoEditalViewSet,
    "Cadastro de Produto Edital",
)
router.register(
    "homologacoes-produtos",
    viewsets.HomologacaoProdutoViewSet,
    "Homologação de Produtos",
)
router.register(
    "reclamacoes-produtos", viewsets.ReclamacaoProdutoViewSet, "Reclamação de Produtos"
)
router.register(
    "painel-gerencial-homologacoes-produtos",
    viewsets.HomologacaoProdutoPainelGerencialViewSet,
    "Painel Gerencial de Homologação de Produtos",
)
router.register(
    "informacoes-nutricionais",
    viewsets.InformacaoNutricionalViewSet,
    "Informações Nutricionais",
)
router.register(
    "protocolo-dieta-especial",
    viewsets.ProtocoloDeDietaEspecialViewSet,
    "Protocolo Dieta Especial",
)
router.register("fabricantes", viewsets.FabricanteViewSet, "Fabricantes")
router.register("marcas", viewsets.MarcaViewSet, "Marcas")
router.register("produto-imagens", viewsets.ImagensViewset, "Imagens")
router.register(
    "analise-sensorial",
    viewsets.RespostaAnaliseSensorialViewSet,
    basename="analise-sensorial",
)
router.register(
    "solicitacao-cadastro-produto-dieta",
    viewsets.SolicitacaoCadastroProdutoDietaViewSet,
    "Solicitação cadastro de Produtos",
)
router.register(
    "itens-cadastros", viewsets.ItensCadastroViewSet, basename="itens-cadastros"
)
router.register(
    "unidades-medida", viewsets.UnidadesDeMedidaViewSet, basename="unidades-medida"
)
router.register(
    "embalagens-produto",
    viewsets.EmbalagemProdutoViewSet,
    basename="embalagens-produto",
)
router.register(
    "dashboard-produtos",
    HomologacaoProdutoDashboardViewSet,
    basename="dashboard-produtos",
)

urlpatterns = [
    path("", include(router.urls)),
]
