from factory import LazyFunction, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from src.recebimento.fixtures.factories.ficha_de_recebimento_factory import (
    FichaDeRecebimentoFactory,
)
from src.recebimento.fixtures.factories.questao_conferencia_factory import (
    QuestaoConferenciaFactory,
)
from src.recebimento.models import QuestaoFichaRecebimento

fake = Faker("pt_BR")


class QuestaoFichaRecebimentoFactory(DjangoModelFactory):
    class Meta:
        model = QuestaoFichaRecebimento

    ficha_recebimento = SubFactory(FichaDeRecebimentoFactory)
    questao_conferencia = SubFactory(QuestaoConferenciaFactory)
    resposta = fake.pybool(truth_probability=50)
    tipo_questao = LazyFunction(
        lambda: fake.random.choice(
            [
                QuestaoFichaRecebimento.TIPO_QUESTAO_PRIMARIA,
                QuestaoFichaRecebimento.TIPO_QUESTAO_SECUNDARIA,
            ]
        )
    )
