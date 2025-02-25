from factory import DjangoModelFactory, Sequence, SubFactory
from faker import Faker

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunoFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
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


class LogQuantidadeDietasAutorizadasFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)
    quantidade = Sequence(lambda n: fake.random_int(min=0, max=100))
    classificacao = SubFactory(ClassificacaoDietaFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    class Meta:
        model = LogQuantidadeDietasAutorizadas


class LogQuantidadeDietasAutorizadasCEIFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)
    quantidade = Sequence(lambda n: fake.random_int(min=0, max=100))
    classificacao = SubFactory(ClassificacaoDietaFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    faixa_etaria = SubFactory(FaixaEtariaFactory)

    class Meta:
        model = LogQuantidadeDietasAutorizadasCEI
