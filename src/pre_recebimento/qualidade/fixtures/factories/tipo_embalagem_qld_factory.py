from factory.django import DjangoModelFactory
from faker import Faker

from ...models import TipoEmbalagemQld

fake = Faker("pt_BR")


class TipoEmbalagemQldFactory(DjangoModelFactory):
    class Meta:
        model = TipoEmbalagemQld
