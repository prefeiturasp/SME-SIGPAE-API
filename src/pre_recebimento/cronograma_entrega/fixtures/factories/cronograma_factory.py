from datetime import date, timedelta

from factory import LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from src.pre_recebimento.base.fixtures.factories.unidade_medida_factory import (
    UnidadeMedidaFactory,
)
from src.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    EtapasDoCronograma,
)
from src.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EmpresaFactory,
)

fake = Faker("pt_BR")


class CronogramaFactory(DjangoModelFactory):
    """Factory para geração de dados de teste do modelo Cronograma."""

    class Meta:
        model = Cronograma

    numero = Sequence(
        lambda n: f'{str(fake.unique.random_int(min=0, max=1000))}/{str(fake.date(pattern="%Y"))}'
    )
    contrato = SubFactory(ContratoFactory)
    empresa = SubFactory(EmpresaFactory)
    unidade_medida = SubFactory(UnidadeMedidaFactory)
    ficha_tecnica = SubFactory(FichaTecnicaFactory)
    qtd_total_programada = LazyFunction(
        lambda: fake.random_number(digits=5, fix_len=True) / 100
    )


class EtapasDoCronogramaFactory(DjangoModelFactory):
    """Factory para geração de dados de teste do modelo EtapasDoCronograma."""

    class Meta:
        model = EtapasDoCronograma

    cronograma = SubFactory(CronogramaFactory)
    numero_empenho = LazyFunction(
        lambda: str(fake.random_number(digits=5, fix_len=True))
    )
    qtd_total_empenho = LazyFunction(
        lambda: fake.random_number(digits=5, fix_len=True) / 100
    )
    etapa = Sequence(lambda n: n + 1)
    parte = Sequence(lambda n: n + 1)
    data_programada = LazyFunction(
        lambda: fake.date_time_between(
            start_date=date.today() + timedelta(days=10)
        ).date()
    )
    quantidade = LazyFunction(lambda: fake.random_number(digits=5, fix_len=True) / 100)
    total_embalagens = LazyFunction(
        lambda: fake.random_number(digits=5, fix_len=True) / 100
    )
