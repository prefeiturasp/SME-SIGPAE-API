from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.dados_comuns.models import Contato, LogSolicitacoesUsuario
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)

fake = Faker("pt_BR")


class LogSolicitacoesUsuarioFactory(DjangoModelFactory):
    uuid_original = fake.uuid4()
    status_evento = Sequence(lambda n: fake.random.randint(1, 30))
    solicitacao_tipo = Sequence(lambda n: fake.random.randint(1, 10))
    usuario = SubFactory(UsuarioFactory)
    justificativa = Sequence(lambda n: f"justificativa - {fake.unique.name()}")
    resposta_sim_nao = fake.boolean()

    class Meta:
        model = LogSolicitacoesUsuario


class ContatoFactory(DjangoModelFactory):
    class Meta:
        model = Contato
