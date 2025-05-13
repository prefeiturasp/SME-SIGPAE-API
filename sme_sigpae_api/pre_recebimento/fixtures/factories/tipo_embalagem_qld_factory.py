from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.pre_recebimento.models import TipoEmbalagemQld

fake = Faker("pt_BR")


class TipoEmbalagemQldFactory(DjangoModelFactory):
    class Meta:
        model = TipoEmbalagemQld
