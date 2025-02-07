from factory import DjangoModelFactory, Sequence, SubFactory
from faker import Faker

from sme_sigpae_api.escola.fixtures.factories.escola_factory import EscolaFactory
from sme_sigpae_api.produto.models import (
    DataHoraVinculoProdutoEdital,
    Fabricante,
    HomologacaoProduto,
    InformacaoNutricional,
    Marca,
    NomeDeProdutoEdital,
    Produto,
    ProdutoEdital,
    ReclamacaoDeProduto,
    TipoDeInformacaoNutricional,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EditalFactory,
)

fake = Faker("pt_BR")


class ProdutoLogisticaFactory(DjangoModelFactory):
    class Meta:
        model = NomeDeProdutoEdital

    nome = Sequence(lambda n: str(fake.unique.name()).upper())
    tipo_produto = NomeDeProdutoEdital.LOGISTICA


class ProdutoTerceirizadaFactory(DjangoModelFactory):
    class Meta:
        model = NomeDeProdutoEdital

    nome = Sequence(lambda n: str(fake.unique.name()).upper())
    tipo_produto = NomeDeProdutoEdital.TERCEIRIZADA


class FabricanteFactory(DjangoModelFactory):
    class Meta:
        model = Fabricante

    nome = Sequence(lambda n: str(fake.unique.name()).upper())


class MarcaFactory(DjangoModelFactory):
    class Meta:
        model = Marca

    nome = Sequence(lambda n: str(fake.unique.name()).upper())


class TipoDeInformacaoNutricionalFactory(DjangoModelFactory):
    class Meta:
        model = TipoDeInformacaoNutricional


class InformacaoNutricionalFactory(DjangoModelFactory):
    class Meta:
        model = InformacaoNutricional

    tipo_nutricional = SubFactory(TipoDeInformacaoNutricionalFactory)


class ProdutoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: str(fake.unique.name()).upper())
    marca = SubFactory(MarcaFactory)
    fabricante = SubFactory(FabricanteFactory)

    class Meta:
        model = Produto


class HomologacaoProdutoFactory(DjangoModelFactory):
    produto = SubFactory(ProdutoFactory)

    class Meta:
        model = HomologacaoProduto


class ProdutoEditalFactory(DjangoModelFactory):
    produto = SubFactory(ProdutoFactory)
    edital = SubFactory(EditalFactory)
    tipo_produto = ProdutoEdital.COMUM

    class Meta:
        model = ProdutoEdital


class DataHoraVinculoProdutoEditalFactory(DjangoModelFactory):
    produto_edital = SubFactory(ProdutoEditalFactory)

    class Meta:
        model = DataHoraVinculoProdutoEdital


class ReclamacaoDeProdutoFactory(DjangoModelFactory):
    homologacao_produto = SubFactory(HomologacaoProdutoFactory)
    reclamante_registro_funcional = Sequence(lambda n: str(fake.unique.name()).upper())
    reclamante_nome = Sequence(lambda n: str(fake.unique.name()).upper())
    reclamacao = Sequence(lambda n: str(fake.name()).upper())
    escola = SubFactory(EscolaFactory)

    class Meta:
        model = ReclamacaoDeProduto
