from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.perfil.models import Perfil, Usuario, Vinculo

fake = Faker("pt_BR")


class UsuarioFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")
    username = Sequence(lambda n: fake.random.randint(1, 9999999))
    email = Sequence(lambda n: fake.unique.email())

    class Meta:
        model = Usuario


class PerfilFactory(DjangoModelFactory):
    class Meta:
        model = Perfil


class VinculoFactory(DjangoModelFactory):
    usuario = SubFactory(UsuarioFactory)
    perfil = SubFactory(PerfilFactory)

    class Meta:
        model = Vinculo
