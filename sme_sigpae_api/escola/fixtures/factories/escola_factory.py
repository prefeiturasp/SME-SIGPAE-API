from random import random

from factory import DjangoModelFactory, LazyAttribute, Sequence, SubFactory
from faker import Faker

from sme_sigpae_api.escola.constants import CEI_OU_EMEI, INFANTIL_OU_FUNDAMENTAL
from sme_sigpae_api.escola.models import (
    Aluno,
    DiretoriaRegional,
    Escola,
    FaixaEtaria,
    LogAlunosMatriculadosPeriodoEscola,
    Lote,
    PeriodoEscolar,
    TipoTurma,
    TipoUnidadeEscolar,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

fake = Faker("pt_BR")


class TipoUnidadeEscolarFactory(DjangoModelFactory):
    class Meta:
        model = TipoUnidadeEscolar


class DiretoriaRegionalFactory(DjangoModelFactory):
    class Meta:
        model = DiretoriaRegional

    nome = Sequence(lambda n: f"Diretoria regional {n} - {fake.unique.company()}")
    codigo_eol = Sequence(lambda n: fake.unique.random_int(min=1, max=999999))


class LoteFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Lote {n} - {fake.unique.company()}")
    diretoria_regional = SubFactory(DiretoriaRegionalFactory)
    terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = Lote


class EscolaFactory(DjangoModelFactory):
    class Meta:
        model = Escola

    nome = Sequence(lambda n: f"Escola {n} - {fake.unique.company()}")
    codigo_eol = Sequence(lambda n: fake.unique.random_int(min=1, max=999999))
    lote = SubFactory(LoteFactory)
    diretoria_regional = SubFactory(DiretoriaRegionalFactory)
    tipo_unidade = SubFactory(TipoUnidadeEscolarFactory)


class PeriodoEscolarFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"Periodo {n} - {fake.unique.word()}")
    tipo_turno = Sequence(lambda n: fake.random_int(min=1, max=7))

    class Meta:
        model = PeriodoEscolar


class LogAlunosMatriculadosPeriodoEscolaFactory(DjangoModelFactory):
    class Meta:
        model = LogAlunosMatriculadosPeriodoEscola

    escola = SubFactory(EscolaFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    quantidade_alunos = Sequence(lambda n: fake.unique.random_int(min=0, max=100))
    tipo_turma = Sequence(
        lambda n: [fake.random_element([choice[0] for choice in TipoTurma.choices()])]
    )
    cei_ou_emei = LazyAttribute(
        lambda o: fake.random_element(elements=[choice[0] for choice in CEI_OU_EMEI])
    )
    infantil_ou_fundamental = LazyAttribute(
        lambda o: fake.random_element(
            elements=[choice[0] for choice in INFANTIL_OU_FUNDAMENTAL]
        )
    )


class FaixaEtariaFactory(DjangoModelFactory):
    inicio = Sequence(lambda n: fake.unique.random_int(min=0, max=10))
    fim = Sequence(lambda n: fake.unique.random_int(min=11, max=36))

    class Meta:
        model = FaixaEtaria


class AlunoFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"{fake.word()}")
    escola = SubFactory(EscolaFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)
    codigo_eol = LazyAttribute(lambda _: random.randint(1000000, 9999999))
    data_nascimento = LazyAttribute(
        lambda _: fake.date_of_birth(minimum_age=1, maximum_age=6)
    )

    class Meta:
        model = Aluno
