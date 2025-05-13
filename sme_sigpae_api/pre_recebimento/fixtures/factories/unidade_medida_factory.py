from factory import LazyAttribute, Sequence
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.pre_recebimento.models import UnidadeMedida

fake = Faker("pt_BR")


class UnidadeMedidaFactory(DjangoModelFactory):
    class Meta:
        model = UnidadeMedida

    nome = Sequence(lambda n: f"Unidade {n}")
    abreviacao = LazyAttribute(lambda obj: obj.nome[:3])
