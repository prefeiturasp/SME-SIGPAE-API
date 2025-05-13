from factory import Sequence
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.perfil.models import Usuario

fake = Faker("pt_BR")


class UsuarioFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")
    username = Sequence(lambda n: fake.random.randint(1, 9999999))
    email = Sequence(lambda n: fake.unique.email())

    class Meta:
        model = Usuario
