"""Factory de questão de conferência para testes."""

from factory import LazyFunction, Sequence
from factory.django import DjangoModelFactory
from faker import Faker

from src.recebimento.models import QuestaoConferencia

fake = Faker("pt_BR")


class QuestaoConferenciaFactory(DjangoModelFactory):
    """Cria uma ``QuestaoConferencia`` com texto e posição sequenciais."""

    class Meta:
        model = QuestaoConferencia

    questao = LazyFunction(lambda: f"{fake.text(max_nb_chars=50).replace('.', '?')}")
    posicao = Sequence(lambda n: n + 1)
