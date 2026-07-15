import datetime
from unittest.mock import patch

import pytest
from model_bakery import baker

from src.medicao_inicial.validators import validate_lanche_emergencial

pytestmark = pytest.mark.django_db


class TestValidateLancheEmergencial:
    @staticmethod
    def _cria_solicitacao(escola, recreio_nas_ferias=None):
        solicitacao = baker.make(
            "SolicitacaoMedicaoInicial",
            escola=escola,
            mes="03",
            ano="2026",
            recreio_nas_ferias=recreio_nas_ferias,
        )
        medicao = baker.make(
            "Medicao",
            solicitacao_medicao_inicial=solicitacao,
            grupo__nome="Solicitações de Alimentação",
        )
        return solicitacao, medicao

    @staticmethod
    def _cria_valor_lanche_emergencial(medicao, dia):
        baker.make(
            "ValorMedicao",
            medicao=medicao,
            categoria_medicao=baker.make("CategoriaMedicao", nome="ALIMENTAÇÃO"),
            nome_campo="lanche_emergencial",
            dia=dia,
            valor="1",
        )

    def test_recreio_valida_apenas_dias_dentro_do_recreio(self, escola):
        recreio = baker.make(
            "RecreioNasFerias",
            data_inicio=datetime.date(2026, 3, 15),
            data_fim=datetime.date(2026, 3, 25),
        )
        solicitacao, medicao = self._cria_solicitacao(escola, recreio)
        self._cria_valor_lanche_emergencial(medicao, "20")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lanche_emergencial(solicitacao, [])

        assert retorno == []

    def test_recreio_sem_lancamento_no_periodo_retorna_erro(self, escola):
        recreio = baker.make(
            "RecreioNasFerias",
            data_inicio=datetime.date(2026, 3, 15),
            data_fim=datetime.date(2026, 3, 25),
        )
        solicitacao, medicao = self._cria_solicitacao(escola, recreio)
        self._cria_valor_lanche_emergencial(medicao, "10")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lanche_emergencial(solicitacao, [])

        assert retorno == [
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Restam dias a serem lançados nos Lanches Emergenciais.",
            }
        ]

    def test_nao_recreio_com_escola_liberada_valida_apenas_fora_do_recreio(
        self, escola
    ):
        recreio = baker.make(
            "RecreioNasFerias",
            data_inicio=datetime.date(2026, 3, 15),
            data_fim=datetime.date(2026, 3, 25),
        )
        baker.make(
            "RecreioNasFeriasUnidadeParticipante",
            recreio_nas_ferias=recreio,
            unidade_educacional=escola,
            lote=escola.lote,
            liberar_medicao=True,
        )
        solicitacao, medicao = self._cria_solicitacao(escola)
        self._cria_valor_lanche_emergencial(medicao, "10")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lanche_emergencial(solicitacao, [])

        assert retorno == []

    def test_nao_recreio_com_escola_liberada_sem_lancamento_fora_retorna_erro(
        self, escola
    ):
        recreio = baker.make(
            "RecreioNasFerias",
            data_inicio=datetime.date(2026, 3, 15),
            data_fim=datetime.date(2026, 3, 25),
        )
        baker.make(
            "RecreioNasFeriasUnidadeParticipante",
            recreio_nas_ferias=recreio,
            unidade_educacional=escola,
            lote=escola.lote,
            liberar_medicao=True,
        )
        solicitacao, medicao = self._cria_solicitacao(escola)
        self._cria_valor_lanche_emergencial(medicao, "20")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lanche_emergencial(solicitacao, [])

        assert retorno == [
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Restam dias a serem lançados nos Lanches Emergenciais.",
            }
        ]

    def test_nao_recreio_sem_participacao_valida_todos_os_dias(self, escola):
        solicitacao, medicao = self._cria_solicitacao(escola)
        self._cria_valor_lanche_emergencial(medicao, "10")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lanche_emergencial(solicitacao, [])

        assert retorno == [
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Restam dias a serem lançados nos Lanches Emergenciais.",
            }
        ]

    def test_nao_recreio_sem_participacao_todos_lancados_retorna_sem_erro(self, escola):
        solicitacao, medicao = self._cria_solicitacao(escola)
        self._cria_valor_lanche_emergencial(medicao, "10")
        self._cria_valor_lanche_emergencial(medicao, "20")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lanche_emergencial(solicitacao, [])

        assert retorno == []

    def test_sem_dias_autorizados_retorna_sem_erro(self, escola):
        solicitacao, medicao = self._cria_solicitacao(escola)

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=[],
        ):
            retorno = validate_lanche_emergencial(solicitacao, [])

        assert retorno == []
