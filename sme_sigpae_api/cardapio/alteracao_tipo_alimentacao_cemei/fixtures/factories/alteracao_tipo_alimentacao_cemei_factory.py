"""Factories para os modelos de Alteração do Tipo de Alimentação CEMEI.

Utiliza ``factory_boy`` para criação de instâncias de teste dos modelos
relacionados à alteração de cardápio para escolas do tipo CEMEI e CEU CEMEI.
"""

import factory
from factory import SubFactory
from factory.django import DjangoModelFactory

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.fixtures.factories.alteracao_tipo_alimentacao_factory import (
    MotivoAlteracaoCardapioFactory,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
    DataIntervaloAlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    LoteFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EmpresaFactory,
)


class AlteracaoCardapioCEMEIFactory(DjangoModelFactory):
    """Factory para o modelo ``AlteracaoCardapioCEMEI``.

    Cria a escola solicitante, o motivo e os campos de rastreio (escola, lote,
    DRE e terceirizada) via subfactories.
    """

    escola = SubFactory(EscolaFactory)
    motivo = SubFactory(MotivoAlteracaoCardapioFactory)
    rastro_escola = SubFactory(EscolaFactory)
    rastro_lote = SubFactory(LoteFactory)
    rastro_dre = SubFactory(DiretoriaRegionalFactory)
    rastro_terceirizada = SubFactory(EmpresaFactory)

    class Meta:
        model = AlteracaoCardapioCEMEI


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEIFactory(DjangoModelFactory):
    """Factory para o modelo ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI``.

    Cria a instância com uma alteração CEMEI e um período escolar via
    subfactories. Suporta adição de tipos de alimentação de origem e destino
    via parâmetros ``tipos_alimentacao_de`` e ``tipos_alimentacao_para``.
    """

    alteracao_cardapio = SubFactory(AlteracaoCardapioCEMEIFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao_de(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_de.add(tipo_alimentacao)

    @factory.post_generation
    def tipos_alimentacao_para(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_para.add(tipo_alimentacao)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI


class SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEIFactory(DjangoModelFactory):
    """Factory para o modelo ``SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI``.

    Cria a instância com uma alteração CEMEI e um período escolar via
    subfactories. Suporta adição de tipos de alimentação de origem e destino
    via parâmetros ``tipos_alimentacao_de`` e ``tipos_alimentacao_para``.
    Diferentemente do lado CEI, não possui faixas etárias aninhadas.
    """

    alteracao_cardapio = SubFactory(AlteracaoCardapioCEMEIFactory)
    periodo_escolar = SubFactory(PeriodoEscolarFactory)

    @factory.post_generation
    def tipos_alimentacao_de(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_de.add(tipo_alimentacao)

    @factory.post_generation
    def tipos_alimentacao_para(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tipo_alimentacao in extracted:
                self.tipos_alimentacao_para.add(tipo_alimentacao)

    class Meta:
        model = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI


class FaixaEtariaSubstituicaoAlimentacaoCEMEICEIFactory(DjangoModelFactory):
    """Factory para o modelo ``FaixaEtariaSubstituicaoAlimentacaoCEMEICEI``.

    Associa automaticamente uma substituição CEI e uma faixa etária via
    subfactories.
    """

    substituicao_alimentacao = SubFactory(
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEIFactory
    )
    faixa_etaria = SubFactory(FaixaEtariaFactory)

    class Meta:
        model = FaixaEtariaSubstituicaoAlimentacaoCEMEICEI


class DataIntervaloAlteracaoCardapioCEMEIFactory(DjangoModelFactory):
    """Factory para o modelo ``DataIntervaloAlteracaoCardapioCEMEI``.

    Associa automaticamente uma ``AlteracaoCardapioCEMEI`` via subfactory.
    """

    alteracao_cardapio_cemei = SubFactory(AlteracaoCardapioCEMEIFactory)

    class Meta:
        model = DataIntervaloAlteracaoCardapioCEMEI
