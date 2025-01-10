from factory import DjangoModelFactory, Sequence, SubFactory
from faker import Faker

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    EscolaFactory,
)

fake = Faker("pt_BR")


class ClassificacaoDietaFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Escola {n} - {fake.unique.name()}")

    class Meta:
        model = ClassificacaoDieta


class SolicitacaoDietaEspecialFactory(DjangoModelFactory):
    aluno = SubFactory(AlunoFactory)
    rastro_escola = SubFactory(EscolaFactory)
    classificacao = SubFactory(ClassificacaoDietaFactory)

    class Meta:
        model = SolicitacaoDietaEspecial
