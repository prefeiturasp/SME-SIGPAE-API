import factory
from factory import LazyAttribute, LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.terceirizada.models import (
    Contrato,
    Edital,
    Modalidade,
    Terceirizada,
)

fake = Faker("pt_BR")


class EmpresaFactory(DjangoModelFactory):
    class Meta:
        model = Terceirizada

    nome_fantasia = Sequence(lambda n: f"Empresa-{n}")
    razao_social = LazyAttribute(
        lambda obj: f"{obj.nome_fantasia} {fake.company_suffix()}"
    )
    cnpj = Sequence(
        lambda n: fake.unique.cnpj().replace(".", "").replace("/", "").replace("-", "")
    )


class EditalFactory(DjangoModelFactory):
    class Meta:
        model = Edital

    numero = Sequence(lambda n: f"{str(n).zfill(5)}")
    objeto = Sequence(lambda n: f"Objeto {n}")


class ModalidadeFactory(DjangoModelFactory):
    class Meta:
        model = Modalidade

    nome = Sequence(lambda n: f"Modalidade {n}")


class ContratoFactory(DjangoModelFactory):
    numero = Sequence(lambda n: f"{str(n).zfill(5)}")
    terceirizada = SubFactory(EmpresaFactory)
    edital = SubFactory(EditalFactory)
    ata = LazyFunction(lambda: str(fake.random_number(digits=10, fix_len=True)))
    numero_chamada_publica = LazyFunction(
        lambda: str(fake.random_number(digits=10, fix_len=True))
    )
    modalidade = SubFactory(ModalidadeFactory)

    @factory.post_generation
    def lotes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for lote in extracted:
                self.lotes.add(lote)

    class Meta:
        model = Contrato
