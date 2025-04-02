from unittest import TestCase

import pytest
from django.core.management import call_command
from django.test import override_settings

from sme_sigpae_api.cardapio.models import (
    MotivoAlteracaoCardapio,
    MotivoSuspensao,
    TipoAlimentacao,
)
from sme_sigpae_api.dados_comuns.models import Contato, TemplateMensagem
from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    MotivoAlteracaoUE,
    MotivoNegacao,
)
from sme_sigpae_api.escola.models import (
    DiretoriaRegional,
    Escola,
    Lote,
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
from sme_sigpae_api.produto.models import (
    InformacaoNutricional,
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
        assert Perfil.objects.all().count() == 0
        assert Usuario.objects.all().count() == 0
        assert MotivoAlteracaoCardapio.objects.all().count() == 0
        assert MotivoSuspensao.objects.all().count() == 0
        assert TipoAlimentacao.objects.all().count() == 0
        assert Contato.objects.all().count() == 0
        assert TemplateMensagem.objects.all().count() == 0
        assert DiretoriaRegional.objects.all().count() == 0
        assert TipoGestao.objects.all().count() == 0
        assert Terceirizada.objects.all().count() == 0
        assert Lote.objects.all().count() == 0
        assert Edital.objects.all().count() == 0
        assert Contrato.objects.all().count() == 0
        assert Subprefeitura.objects.all().count() == 0
        assert MotivoInclusaoContinua.objects.all().count() == 0
        assert MotivoInclusaoNormal.objects.all().count() == 0
        assert ItemKitLanche.objects.all().count() == 0
        assert KitLanche.objects.all().count() == 0
        assert TipoDeInformacaoNutricional.objects.all().count() == 0
        assert InformacaoNutricional.objects.all().count() == 0
        assert Alimento.objects.all().count() == 0
        assert ClassificacaoDieta.objects.all().count() == 0
        assert MotivoNegacao.objects.all().count() == 0
        assert MotivoAlteracaoUE.objects.all().count() == 0
        assert AlergiaIntolerancia.objects.all().count() == 0
        assert ProtocoloDeDietaEspecial.objects.all().count() == 0
        assert TipoUnidadeEscolar.objects.all().count() == 0
        assert Escola.objects.all().count() == 0

        self.call_command()

        assert Perfil.objects.all().count() == 27
        assert Usuario.objects.all().count() == 41
        assert MotivoAlteracaoCardapio.objects.all().count() == 3
        assert MotivoSuspensao.objects.all().count() == 3
        assert TipoAlimentacao.objects.all().count() == 8
        assert Contato.objects.all().count() == 1036
        assert TemplateMensagem.objects.all().count() == 8
        assert DiretoriaRegional.objects.all().count() == 14
        assert TipoGestao.objects.all().count() == 4
        assert Terceirizada.objects.all().count() == 5
        assert Lote.objects.all().count() == 18
        assert Edital.objects.all().count() == 1
        assert Contrato.objects.all().count() == 5
        assert Subprefeitura.objects.all().count() == 32
        assert MotivoInclusaoContinua.objects.all().count() == 4
        assert MotivoInclusaoNormal.objects.all().count() == 3
        assert ItemKitLanche.objects.all().count() == 7
        assert KitLanche.objects.all().count() == 10
        assert TipoDeInformacaoNutricional.objects.all().count() == 6
        assert InformacaoNutricional.objects.all().count() == 43
        assert Alimento.objects.all().count() == 9
        assert ClassificacaoDieta.objects.all().count() == 4
        assert MotivoNegacao.objects.all().count() == 14
        assert MotivoAlteracaoUE.objects.all().count() == 2
        assert AlergiaIntolerancia.objects.all().count() == 322
        assert ProtocoloDeDietaEspecial.objects.all().count() == 322
        assert TipoUnidadeEscolar.objects.all().count() == 13
        assert Escola.objects.all().count() == 1041
