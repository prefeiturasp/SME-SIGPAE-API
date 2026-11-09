import datetime
from unittest.mock import patch

import pytest
from model_bakery import baker

from src.medicao_inicial.models import CategoriaMedicao, GrupoMedicao
from src.medicao_inicial.validators import validate_lancamento_kit_lanche
from src.medicao_inicial.validators import _uuids_kit_lanche_cemei_somente_cei

pytestmark = pytest.mark.django_db


class TestValidateLancamentoKitLanche:
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
            grupo__nome=GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO,
        )
        return solicitacao, medicao

    @staticmethod
    def _cria_valor_kit(medicao, dia):
        baker.make(
            "ValorMedicao",
            medicao=medicao,
            categoria_medicao=baker.make(
                "CategoriaMedicao", nome=CategoriaMedicao.ALIMENTACAO
            ),
            nome_campo="kit_lanche",
            dia=dia,
            valor="1",
        )

    @staticmethod
    def _cria_kit(escola, publico, dia=6, mes=3):
        return baker.make(
            "SolicitacaoKitLancheCEMEI",
            escola=escola,
            data=datetime.date(2026, mes, dia),
            alunos_cei_e_ou_emei=publico,
        )

    def test_quando_medicao_recreio_valida_apenas_dias_dentro_do_recreio(self, escola):
        recreio = baker.make(
            "RecreioNasFerias",
            data_inicio=datetime.date(2026, 3, 15),
            data_fim=datetime.date(2026, 3, 25),
        )
        solicitacao, medicao = self._cria_solicitacao(escola, recreio)
        self._cria_valor_kit(medicao, "20")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lancamento_kit_lanche(solicitacao, [])

        assert retorno == []

    def test_quando_medicao_recreio_sem_lancamento_no_periodo_retorna_erro(
        self, escola
    ):
        recreio = baker.make(
            "RecreioNasFerias",
            data_inicio=datetime.date(2026, 3, 15),
            data_fim=datetime.date(2026, 3, 25),
        )
        solicitacao, medicao = self._cria_solicitacao(escola, recreio)
        self._cria_valor_kit(medicao, "10")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lancamento_kit_lanche(solicitacao, [])

        assert retorno == [
            {
                "periodo_escolar": GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO,
                "erro": "Restam dias a serem lançados nos Kit Lanches.",
            }
        ]

    def test_quando_medicao_nao_recreio_e_escola_liberada_valida_apenas_fora_do_recreio(
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
        self._cria_valor_kit(medicao, "10")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lancamento_kit_lanche(solicitacao, [])

        assert retorno == []

    def test_quando_medicao_nao_recreio_sem_participacao_valida_todos_os_dias(
        self, escola
    ):
        solicitacao, medicao = self._cria_solicitacao(escola)
        self._cria_valor_kit(medicao, "10")

        with patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10", "20"],
        ):
            retorno = validate_lancamento_kit_lanche(solicitacao, [])

        assert retorno == [
            {
                "periodo_escolar": GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO,
                "erro": "Restam dias a serem lançados nos Kit Lanches.",
            }
        ]

    def test_exclui_kits_somente_cei_da_busca_de_dias(self, escola):
        solicitacao, medicao = self._cria_solicitacao(escola)
        self._cria_valor_kit(medicao, "10")
        uuids = ["uuid-kit-cei"]

        with patch(
            "src.medicao_inicial.validators._uuids_kit_lanche_cemei_somente_cei",
            return_value=uuids,
        ), patch(
            "src.medicao_inicial.validators.get_lista_dias_solicitacoes",
            return_value=["10"],
        ) as mock_dias:
            retorno = validate_lancamento_kit_lanche(solicitacao, [])

        assert retorno == []
        assert (
            mock_dias.call_args.kwargs["uuids_solicitacoes_excluidas"] == uuids
        )

    def test_retorna_apenas_kits_cei(self, escola_cemei):
        kit_cei = self._cria_kit(escola_cemei, "CEI", dia=6)
        self._cria_kit(escola_cemei, "EMEI", dia=7)
        self._cria_kit(escola_cemei, "TODOS", dia=8)

        retorno = _uuids_kit_lanche_cemei_somente_cei(escola_cemei, "03", "2026")

        assert retorno == [kit_cei.uuid]
