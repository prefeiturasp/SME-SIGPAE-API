from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from src.dieta_especial.fixtures.factories.dieta_especial_base_factory import (
    ClassificacaoDietaFactory,
)
from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from src.escola.fixtures.factories.escola_factory import (
    EscolaFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
)

fake = Faker("pt_BR")


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
