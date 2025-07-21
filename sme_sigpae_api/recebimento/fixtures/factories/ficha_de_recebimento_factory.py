import base64
from datetime import date, timedelta

from factory import LazyFunction, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.dados_comuns.utils import convert_base64_to_contentfile
from sme_sigpae_api.pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    EtapasDoCronogramaFactory,
)
from sme_sigpae_api.recebimento.models import (
    ArquivoFichaRecebimento,
    FichaDeRecebimento,
    VeiculoFichaDeRecebimento,
)

fake = Faker("pt_BR")


class FichaDeRecebimentoFactory(DjangoModelFactory):
    class Meta:
        model = FichaDeRecebimento

    etapa = SubFactory(EtapasDoCronogramaFactory)
    data_entrega = LazyFunction(
        lambda: fake.date_time_between(
            start_date=date.today() + timedelta(days=10)
        ).date()
    )


class VeiculoFichaDeRecebimentoFactory(DjangoModelFactory):
    class Meta:
        model = VeiculoFichaDeRecebimento

    ficha_recebimento = SubFactory(FichaDeRecebimentoFactory)
    numero = Sequence(lambda n: f"Veículo {n}")


class ArquivoFichaDeRecebimentoFactory(DjangoModelFactory):
    class Meta:
        model = ArquivoFichaRecebimento

    ficha_recebimento = SubFactory(FichaDeRecebimentoFactory)
    arquivo = LazyFunction(
        lambda: convert_base64_to_contentfile(
            f"data:aplication/pdf;base64,{base64.b64encode(b'arquivo pdf teste').decode('utf-8')}"
        )
    )
