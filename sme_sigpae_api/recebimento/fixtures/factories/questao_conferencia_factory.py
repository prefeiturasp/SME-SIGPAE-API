from factory import LazyFunction, Sequence
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.recebimento.models import QuestaoConferencia

fake = Faker("pt_BR")


class QuestaoConferenciaFactory(DjangoModelFactory):
    class Meta:
        model = QuestaoConferencia

    questao = LazyFunction(lambda: f"{fake.text(max_nb_chars=50).replace('.', '?')}")
    posicao = Sequence(lambda n: n + 1)
