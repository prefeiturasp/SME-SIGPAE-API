from factory import LazyFunction, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.pre_recebimento.models.cronograma import FabricanteFichaTecnica
from sme_sigpae_api.produto.fixtures.factories.produto_factory import FabricanteFactory

fake = Faker("pt_BR")


class FabricanteFichaTecnicaFactory(DjangoModelFactory):
    class Meta:
        model = FabricanteFichaTecnica

    fabricante = SubFactory(FabricanteFactory)
    cnpj = LazyFunction(
        lambda: fake.cnpj().replace(".", "").replace("-", "").replace("/", "")
    )
    cep = LazyFunction(lambda: fake.postcode().replace("-", ""))
    endereco = LazyFunction(lambda: fake.street_name())
    numero = LazyFunction(lambda: fake.building_number())
    complemento = LazyFunction(lambda: fake.sentence(nb_words=3))
    bairro = LazyFunction(lambda: fake.bairro())
    cidade = LazyFunction(lambda: fake.city())
    estado = LazyFunction(lambda: fake.estado_sigla())
    email = LazyFunction(lambda: fake.email())
    telefone = LazyFunction(lambda: fake.phone_number()[:13])
