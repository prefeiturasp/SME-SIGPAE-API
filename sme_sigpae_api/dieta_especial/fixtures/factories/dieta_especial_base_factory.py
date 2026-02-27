from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    MotivoAlteracaoUE,
    ProtocoloPadraoDietaEspecial,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
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
    escola_destino = SubFactory(EscolaFactory)
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


class MotivoAlteracaoUEFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Escola {n} - {fake.unique.name()}")

    class Meta:
        model = MotivoAlteracaoUE


class AlergiaIntoleranciaFactory(DjangoModelFactory):
    descricao = Sequence(lambda n: f"Alergia/Intolerância {n} - {fake.word()}")

    class Meta:
        model = AlergiaIntolerancia


class AlimentoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Alimento {n} - {fake.word()}")

    class Meta:
        model = Alimento


class ProtocoloPadraoDietaEspecialFactory(DjangoModelFactory):
    nome_protocolo = Sequence(lambda n: f"Protocolo {n} - {fake.word().upper()}")
    status = "LIBERADO"

    class Meta:
        model = ProtocoloPadraoDietaEspecial


class SubstituicaoAlimentoFactory(DjangoModelFactory):
    solicitacao_dieta_especial = SubFactory(SolicitacaoDietaEspecialFactory)
    alimento = SubFactory(AlimentoFactory)
    tipo = "S"  # S para Substituição ou I para Isento

    class Meta:
        model = SubstituicaoAlimento
