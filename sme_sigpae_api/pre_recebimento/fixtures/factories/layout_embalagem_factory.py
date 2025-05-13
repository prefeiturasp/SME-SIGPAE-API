from factory import SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.pre_recebimento.fixtures.factories.cronograma_factory import (
    FichaTecnicaFactory,
)
from sme_sigpae_api.pre_recebimento.models import LayoutDeEmbalagem

fake = Faker("pt_BR")


class LayoutDeEmbalagemFactory(DjangoModelFactory):
    class Meta:
        model = LayoutDeEmbalagem

    ficha_tecnica = SubFactory(FichaTecnicaFactory)
