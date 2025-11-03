import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    MotivoSuspensao,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
    SuspensaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

fake = Faker("pt_BR")


class GrupoSuspensaoAlimentacaoFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = GrupoSuspensaoAlimentacao


class MotivoSuspensaoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"nome - {fake.name()}")

    class Meta:
        model = MotivoSuspensao


class SuspensaoAlimentacaoFactory(DjangoModelFactory):
    grupo_suspensao = SubFactory(GrupoSuspensaoAlimentacaoFactory)
    motivo = SubFactory(MotivoSuspensaoFactory)

    class Meta:
        model = SuspensaoAlimentacao


class QuantidadePorPeriodoSuspensaoAlimentacaoFactory(DjangoModelFactory):
    grupo_suspensao = SubFactory(GrupoSuspensaoAlimentacaoFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    numero_alunos = Sequence(lambda n: fake.random_int(min=1, max=100))

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = QuantidadePorPeriodoSuspensaoAlimentacao


class SuspensaoAlimentacaoNoPeriodoEscolarFactory(DjangoModelFactory):
    suspensao_alimentacao = SubFactory(SuspensaoAlimentacaoFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    qtd_alunos = Sequence(lambda n: fake.random_int(min=1, max=100))

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = SuspensaoAlimentacaoNoPeriodoEscolar
