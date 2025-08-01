from factory import LazyFunction, SubFactory
from factory.django import DjangoModelFactory
from faker import Faker

from sme_sigpae_api.pre_recebimento.base.fixtures.factories.unidade_medida_factory import (
    UnidadeMedidaFactory,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.fixtures.factories.fabricante_ficha_tecnica_factory import (
    FabricanteFichaTecnicaFactory,
)
from sme_sigpae_api.produto.fixtures.factories.produto_factory import (
    MarcaFactory,
    ProdutoLogisticaFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)

from ...models import (
    AnaliseFichaTecnica,
    FichaTecnicaDoProduto,
)

fake = Faker("pt_BR")


class FichaTecnicaFactory(DjangoModelFactory):
    class Meta:
        model = FichaTecnicaDoProduto

    empresa = SubFactory(EmpresaFactory)
    produto = SubFactory(ProdutoLogisticaFactory)
    marca = SubFactory(MarcaFactory)
    categoria = LazyFunction(
        lambda: fake.random.choice(
            [
                FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS,
                FichaTecnicaDoProduto.CATEGORIA_NAO_PERECIVEIS,
            ]
        )
    )
    peso_liquido_embalagem_primaria = LazyFunction(
        lambda: fake.random_number(digits=5, fix_len=True) / 100
    )
    unidade_medida_primaria = SubFactory(UnidadeMedidaFactory)
    peso_liquido_embalagem_secundaria = LazyFunction(
        lambda: fake.random_number(digits=5, fix_len=True) / 100
    )
    unidade_medida_secundaria = SubFactory(UnidadeMedidaFactory)
    embalagem_primaria = LazyFunction(lambda: fake.text())
    embalagem_secundaria = LazyFunction(lambda: fake.text())
    fabricante = SubFactory(FabricanteFichaTecnicaFactory)
    envasador_distribuidor = SubFactory(FabricanteFichaTecnicaFactory)


class AnaliseFichaTecnicaFactory(DjangoModelFactory):
    class Meta:
        model = AnaliseFichaTecnica

    ficha_tecnica = SubFactory(FichaTecnicaFactory)
