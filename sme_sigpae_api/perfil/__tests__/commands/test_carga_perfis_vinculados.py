from unittest import TestCase

import pytest
from django.core.management import call_command
from model_bakery import baker

from sme_sigpae_api.perfil.models.perfil import Perfil, PerfisVinculados

from ....dados_comuns.constants import (
    ADMINISTRADOR_CONTRATOS,
    ADMINISTRADOR_DIETA_ESPECIAL,
    ADMINISTRADOR_GESTAO_PRODUTO,
    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    DILOG_ABASTECIMENTO,
)


class CargaPerfisVinculadosCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "carga_perfis_vinculados",
            *args,
            **kwargs,
        )

    def setUp(self) -> None:
        baker.make(
            Perfil,
            nome=ADMINISTRADOR_DIETA_ESPECIAL,
        )
        baker.make(
            Perfil,
            nome=ADMINISTRADOR_GESTAO_PRODUTO,
        )
        baker.make(
            Perfil,
            nome=ADMINISTRADOR_SUPERVISAO_NUTRICAO,
        )
        baker.make(
            Perfil,
            nome=COORDENADOR_DIETA_ESPECIAL,
        )
        baker.make(
            Perfil,
            nome=COORDENADOR_GESTAO_PRODUTO,
        )
        baker.make(
            Perfil,
            nome=COORDENADOR_SUPERVISAO_NUTRICAO,
        )
        baker.make(
            Perfil,
            nome=COORDENADOR_CODAE_DILOG_LOGISTICA,
        )
        baker.make(
            Perfil,
            nome=ADMINISTRADOR_CONTRATOS,
        )
        baker.make(
            Perfil,
            nome=DILOG_ABASTECIMENTO,
        )

    @pytest.mark.django_db(transaction=True)
    def test_command_carga(self) -> None:
        self.call_command()
        dieta = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_DIETA_ESPECIAL
        )[0]
        assert dieta.perfis_subordinados.first().nome == ADMINISTRADOR_DIETA_ESPECIAL

        produto = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_GESTAO_PRODUTO
        )[0]
        assert produto.perfis_subordinados.first().nome == ADMINISTRADOR_GESTAO_PRODUTO

        coordenador_supervisao_nutricao = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_SUPERVISAO_NUTRICAO
        )[0]
        assert (
            coordenador_supervisao_nutricao.perfis_subordinados.first().nome
            == ADMINISTRADOR_SUPERVISAO_NUTRICAO
        )
        coordenador_dialog_logistica = PerfisVinculados.objects.filter(
            perfil_master__nome=COORDENADOR_CODAE_DILOG_LOGISTICA
        )[0]
        perfis_subordinado_dialog_logistica = list(
            coordenador_dialog_logistica.perfis_subordinados.values_list(
                "nome", flat=True
            )
        )
        assert len(perfis_subordinado_dialog_logistica) == 2
        assert ADMINISTRADOR_CONTRATOS in perfis_subordinado_dialog_logistica
        assert DILOG_ABASTECIMENTO in perfis_subordinado_dialog_logistica
