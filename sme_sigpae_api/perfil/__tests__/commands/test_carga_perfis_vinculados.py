from unittest import TestCase

import pytest
from django.core.management import call_command
from model_mommy import mommy

from sme_sigpae_api.perfil.models.perfil import Perfil, PerfisVinculados

from ....dados_comuns.constants import (
    ADMINISTRADOR_DICAE,
    ADMINISTRADOR_DIETA_ESPECIAL,
    ADMINISTRADOR_GESTAO_PRODUTO,
    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_SUPERVISAO_NUTRICAO,
)


class CargaPerfisVinculadosCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "carga_perfis_vinculados",
            *args,
            **kwargs,
        )

    def setUp(self) -> None:
        mommy.make(
            Perfil,
            nome=ADMINISTRADOR_DIETA_ESPECIAL,
        )
        mommy.make(
            Perfil,
            nome=ADMINISTRADOR_GESTAO_PRODUTO,
        )
        mommy.make(
            Perfil,
            nome=ADMINISTRADOR_SUPERVISAO_NUTRICAO,
        )
        mommy.make(
            Perfil,
            nome=COORDENADOR_DIETA_ESPECIAL,
        )
        mommy.make(
            Perfil,
            nome=COORDENADOR_GESTAO_PRODUTO,
        )
        mommy.make(
            Perfil,
            nome=COORDENADOR_SUPERVISAO_NUTRICAO,
        )
        mommy.make(
            Perfil,
            nome=COORDENADOR_CODAE_DILOG_LOGISTICA,
        )
        mommy.make(
            Perfil,
            nome=ADMINISTRADOR_DICAE,
        )

    @pytest.mark.django_db(transaction=True)
    def test_command_carga(self) -> None:
        self.call_command()
        dieta = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_DIETA_ESPECIAL
        )[0]
        produto = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_GESTAO_PRODUTO
        )[0]
        coordenador_supervisao_nutricao = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_SUPERVISAO_NUTRICAO
        )[0]
        coordenador_dialog_logistica = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_CODAE_DILOG_LOGISTICA
        )[0]
        assert dieta.perfis_subordinados.first().nome == ADMINISTRADOR_DIETA_ESPECIAL
        assert produto.perfis_subordinados.first().nome == ADMINISTRADOR_GESTAO_PRODUTO
        assert (
            coordenador_supervisao_nutricao.perfis_subordinados.first().nome
            == ADMINISTRADOR_SUPERVISAO_NUTRICAO
        )
        assert (
            coordenador_dialog_logistica.perfis_subordinados.first().nome
            == ADMINISTRADOR_DICAE
        )
