import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from freezegun.api import freeze_time

from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    DiretoriaRegionalFactory,
    EscolaFactory,
    FaixaEtariaFactory,
    PeriodoEscolarFactory,
)
from sme_sigpae_api.escola.models import LogAlunosMatriculadosFaixaEtariaDia


class AtualizaCacheMatriculadosPorFaixaCommandTest(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "atualiza_cache_matriculados_por_faixa",
            *args,
            **kwargs,
        )

    def setUp(self) -> None:
        dre = DiretoriaRegionalFactory.create(codigo_eol="801048")
        self.cei_diret = EscolaFactory.create(
            nome="CEI DIRET CABREUVAS",
            codigo_eol="400020",
            tipo_unidade__iniciais="CEI DIRET",
            diretoria_regional=dre,
        )
        self.cci = EscolaFactory.create(
            nome="CCI/CIPS CAMARA MUNICIPAL DE SAO PAULO",
            codigo_eol="400509",
            tipo_unidade__iniciais="CCI/CIPS",
            diretoria_regional=dre,
        )

        PeriodoEscolarFactory.create(nome="INTEGRAL", tipo_turno=6)

        FaixaEtariaFactory.create(inicio=0, fim=1)
        FaixaEtariaFactory.create(inicio=1, fim=4)
        FaixaEtariaFactory.create(inicio=4, fim=6)
        FaixaEtariaFactory.create(inicio=6, fim=7)
        FaixaEtariaFactory.create(inicio=7, fim=12)
        FaixaEtariaFactory.create(inicio=12, fim=48)
        FaixaEtariaFactory.create(inicio=48, fim=73)

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_ue_400020_dados_alunos_2025.json",
            "r",
        ) as file:
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_1 = json.load(
                file
            )

        with open(
            "sme_sigpae_api/escola/__tests__/commands/mocks/mock_ue_400509_dados_alunos_2025.json",
            "r",
        ) as file:
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_2 = json.load(
                file
            )

    @freeze_time("2024-12-26")
    @pytest.mark.django_db(transaction=True)
    @patch("redis.StrictRedis")
    @patch(
        "sme_sigpae_api.eol_servico.utils.EOLServicoSGP.get_alunos_por_escola_por_ano_letivo"
    )
    def test_command_atualiza_cache_matriculados_por_faixa(
        self,
        mock_get_alunos_por_escola_por_ano_letivo,
        mock_redis,
    ) -> None:
        mock_redis_instance = MagicMock()
        mock_redis.return_value = mock_redis_instance

        mock_get_alunos_por_escola_por_ano_letivo.side_effect = [
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_1,
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_1,
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_1,
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_1,
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_2,
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_2,
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_2,
            self.mock_chamada_externa_alunos_por_escola_por_ano_letivo_2,
        ]

        self.call_command()

        mock_redis_instance.delete.assert_called()
        mock_redis_instance.hset.assert_called()

        assert LogAlunosMatriculadosFaixaEtariaDia.objects.count() == 3
        assert (
            LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                escola=self.cei_diret
            ).count()
            == 2
        )
        assert (
            LogAlunosMatriculadosFaixaEtariaDia.objects.filter(escola=self.cci).count()
            == 1
        )
