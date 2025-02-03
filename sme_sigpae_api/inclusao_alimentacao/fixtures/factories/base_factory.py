import factory
from factory import DjangoModelFactory, Sequence, SubFactory
from faker import Faker

from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.inclusao_alimentacao.models import (
    DiasMotivosInclusaoDeAlimentacaoCEI,
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoDaCEI,
    InclusaoAlimentacaoNormal,
    MotivoInclusaoNormal,
    QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI,
    QuantidadePorPeriodo,
)
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

fake = Faker("pt_BR")


class MotivoInclusaoNormalFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")

    class Meta:
        model = MotivoInclusaoNormal


class GrupoInclusaoAlimentacaoNormalFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = GrupoInclusaoAlimentacaoNormal


class InclusaoAlimentacaoNormalFactory(DjangoModelFactory):
    motivo = SubFactory(MotivoInclusaoNormalFactory)
    grupo_inclusao = SubFactory(GrupoInclusaoAlimentacaoNormalFactory)

    class Meta:
        model = InclusaoAlimentacaoNormal


class QuantidadePorPeriodoFactory(DjangoModelFactory):
    numero_alunos = Sequence(lambda n: fake.random_int(min=1, max=100))
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    grupo_inclusao_normal = SubFactory(GrupoInclusaoAlimentacaoNormalFactory)

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = QuantidadePorPeriodo


class InclusaoAlimentacaoDaCEIFactory(DjangoModelFactory):
    criado_por = SubFactory(UsuarioFactory)
    escola = SubFactory(EscolaFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_lote = SubFactory(LoteFactory)

    @factory.post_generation
    def tipos_alimentacao(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao.add(tipo_alimentacao)

    class Meta:
        model = InclusaoAlimentacaoDaCEI


class QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEIFactory(
    DjangoModelFactory
):
    inclusao_alimentacao_da_cei = SubFactory(InclusaoAlimentacaoDaCEIFactory)
    faixa_etaria = SubFactory(FaixaEtariaFactory)
    quantidade_alunos = Sequence(lambda n: fake.random_int(min=1, max=100))
    periodo = SubFactory(PeriodoEscolarFactory)

    class Meta:
        model = QuantidadeDeAlunosPorFaixaEtariaDaInclusaoDeAlimentacaoDaCEI


class DiasMotivosInclusaoDeAlimentacaoCEIFactory(DjangoModelFactory):
    inclusao_cei = SubFactory(InclusaoAlimentacaoDaCEIFactory)

    class Meta:
        model = DiasMotivosInclusaoDeAlimentacaoCEI
