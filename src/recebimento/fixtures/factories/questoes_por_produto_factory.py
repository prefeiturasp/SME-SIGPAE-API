"""Factory de questões por produto para testes."""

from factory import SubFactory
from factory.django import DjangoModelFactory

from src.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
)
from src.recebimento.models import QuestoesPorProduto


class QuestoesPorProdutoFactory(DjangoModelFactory):
    """Cria um ``QuestoesPorProduto`` vinculado a uma ``FichaTecnicaFactory``."""

    class Meta:
        model = QuestoesPorProduto

    ficha_tecnica = SubFactory(FichaTecnicaFactory)
