from unittest import TestCase
from unittest.mock import Mock

from sme_sigpae_api.escola.management.commands.atualiza_cache_matriculados_por_faixa import (
    Command,
)


class TrataCemeiAoGerarLogsTest(TestCase):
    def setUp(self) -> None:
        self.command = Command()
        self.faixa = Mock()

        self.escola_cemei = Mock()
        self.escola_cemei.eh_cemei = True
        self.escola_cemei.quantidade_alunos_cei_por_periodo_por_faixa = Mock()

        self.escola_nao_cemei = Mock()
        self.escola_nao_cemei.eh_cemei = False

    def test_nao_cemei_nao_altera_quantidade_nem_pula(self):
        pula, qtd = self.command.trata_cemei_ao_gerar_logs(
            self.escola_nao_cemei, "PARCIAL", self.faixa, 5
        )

        self.assertFalse(pula)
        self.assertEqual(qtd, 5)

    def test_cemei_parcial_nao_recalcula_quantidade_e_nao_pula(self):
        self.escola_cemei.quantidade_alunos_cei_por_periodo_por_faixa.return_value = 999

        pula, qtd = self.command.trata_cemei_ao_gerar_logs(
            self.escola_cemei, "PARCIAL", self.faixa, 7
        )

        self.assertFalse(pula)
        self.assertEqual(qtd, 7)
        self.escola_cemei.quantidade_alunos_cei_por_periodo_por_faixa.assert_not_called()

    def test_cemei_integral_recalcula_quantidade(self):
        self.escola_cemei.quantidade_alunos_cei_por_periodo_por_faixa.return_value = 10

        pula, qtd = self.command.trata_cemei_ao_gerar_logs(
            self.escola_cemei, "INTEGRAL", self.faixa, 0
        )

        self.assertFalse(pula)
        self.assertEqual(qtd, 10)
        self.escola_cemei.quantidade_alunos_cei_por_periodo_por_faixa.assert_called_once_with(
            "INTEGRAL", self.faixa
        )

    def test_cemei_integral_pula_quando_quantidade_zero(self):
        self.escola_cemei.quantidade_alunos_cei_por_periodo_por_faixa.return_value = 0

        pula, qtd = self.command.trata_cemei_ao_gerar_logs(
            self.escola_cemei, "INTEGRAL", self.faixa, 5
        )

        self.assertTrue(pula)
        self.assertEqual(qtd, 0)

    def test_cemei_outro_periodo_pula(self):
        pula, qtd = self.command.trata_cemei_ao_gerar_logs(
            self.escola_cemei, "INTERMEDIARIO", self.faixa, 5
        )

        self.assertTrue(pula)
        self.assertEqual(qtd, 5)
