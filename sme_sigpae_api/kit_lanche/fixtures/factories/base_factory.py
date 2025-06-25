import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    LoteFactory,
)
from sme_sigpae_api.kit_lanche.models import (
    FaixaEtariaSolicitacaoKitLancheCEIAvulsa,
    KitLanche,
    SolicitacaoKitLanche,
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
)
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EditalFactory,
    EmpresaFactory,
)

fake = Faker("pt_BR")


class KitLancheFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")

    @factory.post_generation
    def tipos_unidades(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_unidade in extracted:
                self.tipos_unidades.add(tipo_unidade)

    class Meta:
        model = KitLanche


class SolicitacaoKitLancheFactory(DjangoModelFactory):
    data = factory.Faker("date")
    tempo_passeio = Sequence(lambda n: fake.unique.random_int(min=0, max=2))

    @factory.post_generation
    def kits(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for kit in extracted:
                self.kits.add(kit)

    class Meta:
        model = SolicitacaoKitLanche


class SolicitacaoKitLancheAvulsaFactory(DjangoModelFactory):
    solicitacao_kit_lanche = SubFactory(SolicitacaoKitLancheFactory)
    criado_por = SubFactory(UsuarioFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)
    quantidade_alunos = Sequence(lambda n: fake.unique.random_int(min=1, max=100))
    escola = SubFactory(EscolaFactory)

    @factory.post_generation
    def alunos_com_dieta_especial_participantes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for aluno in extracted:
                self.alunos_com_dieta_especial_participantes.add(aluno)

    class Meta:
        model = SolicitacaoKitLancheAvulsa


class SolicitacaoKitLancheCEIAvulsaFactory(DjangoModelFactory):
    solicitacao_kit_lanche = SubFactory(SolicitacaoKitLancheFactory)
    criado_por = SubFactory(UsuarioFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)
    escola = SubFactory(EscolaFactory)

    @factory.post_generation
    def alunos_com_dieta_especial_participantes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for aluno in extracted:
                self.alunos_com_dieta_especial_participantes.add(aluno)

    class Meta:
        model = SolicitacaoKitLancheCEIAvulsa


class FaixaEtariaSolicitacaoKitLancheCEIAvulsaFactory(DjangoModelFactory):
    solicitacao_kit_lanche_avulsa = SubFactory(SolicitacaoKitLancheCEIAvulsaFactory)
    faixa_etaria = SubFactory(FaixaEtariaFactory)
    quantidade = Sequence(lambda n: fake.random_int(min=0, max=100))

    class Meta:
        model = FaixaEtariaSolicitacaoKitLancheCEIAvulsa
