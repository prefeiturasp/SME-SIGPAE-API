from unittest import TestCase

import pytest
from django.core.management import call_command
from django.test import override_settings

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.base.models import (
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from sme_sigpae_api.dados_comuns.models import Contato, TemplateMensagem
from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    AlimentoProprio,
    ClassificacaoDieta,
    MotivoAlteracaoUE,
    MotivoNegacao,
)
from sme_sigpae_api.escola.models import (
    DiretoriaRegional,
    Escola,
    EscolaPeriodoEscolar,
    Lote,
    PeriodoEscolar,
    Subprefeitura,
    TipoGestao,
    TipoUnidadeEscolar,
)
from sme_sigpae_api.inclusao_alimentacao.models import (
    MotivoInclusaoContinua,
    MotivoInclusaoNormal,
)
from sme_sigpae_api.kit_lanche.models import ItemKitLanche, KitLanche
from sme_sigpae_api.perfil.models import Perfil, Usuario
from sme_sigpae_api.perfil.models.perfil import Vinculo
from sme_sigpae_api.produto.data.produtos import data_produtos
from sme_sigpae_api.produto.data.produtos_marcas import data_produtos_marcas
from sme_sigpae_api.produto.models import (
    Fabricante,
    InformacaoNutricional,
    Marca,
    Produto,
    ProtocoloDeDietaEspecial,
    TipoDeInformacaoNutricional,
)
from sme_sigpae_api.terceirizada.models import Contrato, Edital, Terceirizada


class CargaDadosCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "carga_dados",
            *args,
            **kwargs,
        )

    @pytest.mark.django_db(transaction=True)
    @override_settings(DEBUG=True)
    def test_command_carga_dados(self) -> None:
        call_command("flush", verbosity=0, interactive=False)
        assert Perfil.objects.count() == 0
        assert Usuario.objects.count() == 0
        assert MotivoAlteracaoCardapio.objects.count() == 0
        assert MotivoSuspensao.objects.count() == 0
        assert TipoAlimentacao.objects.count() == 0
        assert Contato.objects.count() == 0
        assert TemplateMensagem.objects.count() == 0
        assert DiretoriaRegional.objects.count() == 0
        assert TipoGestao.objects.count() == 0
        assert Terceirizada.objects.count() == 0
        assert Lote.objects.count() == 0
        assert Edital.objects.count() == 0
        assert Contrato.objects.count() == 0
        assert Subprefeitura.objects.count() == 0
        assert MotivoInclusaoContinua.objects.count() == 0
        assert MotivoInclusaoNormal.objects.count() == 0
        assert ItemKitLanche.objects.count() == 0
        assert KitLanche.objects.count() == 0
        assert TipoDeInformacaoNutricional.objects.count() == 0
        assert InformacaoNutricional.objects.count() == 0
        assert Alimento.objects.count() == 0
        assert ClassificacaoDieta.objects.count() == 0
        assert MotivoNegacao.objects.count() == 0
        assert MotivoAlteracaoUE.objects.count() == 0
        assert AlergiaIntolerancia.objects.count() == 0
        assert ProtocoloDeDietaEspecial.objects.count() == 0
        assert TipoUnidadeEscolar.objects.count() == 0
        assert Escola.objects.count() == 0
        assert PeriodoEscolar.objects.count() == 0
        assert EscolaPeriodoEscolar.objects.count() == 0
        assert (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count()
            == 0
        )
        assert ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count() == 0
        assert (
            SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count()
            == 0
        )
        assert Vinculo.objects.count() == 0
        assert Marca.objects.count() == 0
        assert Fabricante.objects.count() == 0
        assert Produto.objects.count() == 0
        assert AlimentoProprio.objects.count() == 0

        self.call_command()

        assert Perfil.objects.count() == 28
        assert Usuario.objects.count() == 41
        assert MotivoAlteracaoCardapio.objects.count() == 3
        assert MotivoSuspensao.objects.count() == 3
        assert TipoAlimentacao.objects.count() == 8
        assert Contato.objects.count() == 1036
        assert TemplateMensagem.objects.count() == 8
        assert DiretoriaRegional.objects.count() == 14
        assert TipoGestao.objects.count() == 4
        assert Terceirizada.objects.count() == 5
        assert Lote.objects.count() == 18
        assert Edital.objects.count() == 1
        assert Contrato.objects.count() == 5
        assert Subprefeitura.objects.count() == 32
        assert MotivoInclusaoContinua.objects.count() == 4
        assert MotivoInclusaoNormal.objects.count() == 3
        assert ItemKitLanche.objects.count() == 7
        assert KitLanche.objects.count() == 10
        assert TipoDeInformacaoNutricional.objects.count() == 6
        assert InformacaoNutricional.objects.count() == 43
        assert Alimento.objects.count() == 9
        assert ClassificacaoDieta.objects.count() == 4
        assert MotivoNegacao.objects.count() == 14
        assert MotivoAlteracaoUE.objects.count() == 2
        assert AlergiaIntolerancia.objects.count() == 322
        assert ProtocoloDeDietaEspecial.objects.count() == 322
        assert TipoUnidadeEscolar.objects.count() == 13
        assert Escola.objects.count() == 1041
        assert PeriodoEscolar.objects.count() == 7
        assert EscolaPeriodoEscolar.objects.count() == 7287
        assert Vinculo.objects.count() == 30
        assert Marca.objects.count() == 193
        assert Fabricante.objects.count() == 193
        assert AlimentoProprio.objects.count() == 9

        vinculos = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count()
        )
        assert vinculos == 91

        combos = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count()
        minimo_combo = 7 * vinculos
        maximo_combo = 12 * vinculos
        assert minimo_combo < combos < maximo_combo
        assert (
            SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.count()
            == combos
        )
        minino_produtos = len(data_produtos)
        maximo_produtos = len(data_produtos) + len(data_produtos_marcas)
        assert minino_produtos < Produto.objects.count() < maximo_produtos
