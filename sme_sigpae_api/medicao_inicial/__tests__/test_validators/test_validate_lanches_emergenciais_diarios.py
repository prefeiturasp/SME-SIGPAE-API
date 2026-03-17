import datetime

import pytest

from sme_sigpae_api.medicao_inicial.validators import (
    validate_lanches_emergenciais_diarios,
)

pytestmark = pytest.mark.django_db


class TestValidateLanchesEmergenciaisDiarios:
    @staticmethod
    def _cria_solicitacao_emebs(solicitacao_medicao_inicial_factory, escola_emebs):
        return solicitacao_medicao_inicial_factory.create(
            escola=escola_emebs,
            mes="03",
            ano="2024",
        )

    @staticmethod
    def _cria_lanche_e_calendario(
        solicitacao,
        lanche_emergencial_diario_factory,
        dia_calendario_factory,
    ):
        lanche_emergencial_diario_factory.create(
            escola=solicitacao.escola,
            data_inicial=datetime.date(2024, 3, 5),
            data_final=datetime.date(2024, 3, 7),
        )
        for dia in range(1, 32):
            dia_calendario_factory.create(
                escola=solicitacao.escola,
                data=datetime.date(2024, 3, dia),
                dia_letivo=dia in {5, 7},
                periodo_escolar=None,
            )

    def test_retorna_lista_sem_alteracao_quando_escola_emebs_nao_tem_lanche_diario(
        self,
        solicitacao_medicao_inicial_factory,
        escola_emebs,
    ):
        solicitacao = self._cria_solicitacao_emebs(
            solicitacao_medicao_inicial_factory, escola_emebs
        )
        lista_erros = []

        retorno = validate_lanches_emergenciais_diarios(solicitacao, lista_erros)

        assert solicitacao.escola.eh_emebs is True
        assert retorno == []

    def test_adiciona_erro_quando_escola_emebs_tem_lanche_diario_e_nao_tem_medicao_do_grupo(
        self,
        solicitacao_medicao_inicial_factory,
        escola_emebs,
        lanche_emergencial_diario_factory,
        dia_calendario_factory,
    ):
        solicitacao = self._cria_solicitacao_emebs(
            solicitacao_medicao_inicial_factory, escola_emebs
        )
        self._cria_lanche_e_calendario(
            solicitacao,
            lanche_emergencial_diario_factory,
            dia_calendario_factory,
        )
        lista_erros = []

        retorno = validate_lanches_emergenciais_diarios(solicitacao, lista_erros)

        assert retorno == [
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Restam dias a serem lançados nos Lanches Emergenciais.",
            }
        ]

    def test_adiciona_erro_quando_escola_emebs_tem_lanche_diario_e_faltam_dias_lancados(
        self,
        solicitacao_medicao_inicial_factory,
        escola_emebs,
        lanche_emergencial_diario_factory,
        dia_calendario_factory,
        medicao_factory,
        valor_medicao_factory,
        categoria_medicao_factory,
    ):
        solicitacao = self._cria_solicitacao_emebs(
            solicitacao_medicao_inicial_factory, escola_emebs
        )
        self._cria_lanche_e_calendario(
            solicitacao,
            lanche_emergencial_diario_factory,
            dia_calendario_factory,
        )
        medicao = medicao_factory.create(
            solicitacao_medicao_inicial=solicitacao,
            periodo_escolar=None,
            grupo__nome="Solicitações de Alimentação",
        )
        valor_medicao_factory.create(
            medicao=medicao,
            categoria_medicao=categoria_medicao_factory.create(),
            nome_campo="lanche_emergencial",
            dia="05",
            valor=1,
        )
        lista_erros = []

        retorno = validate_lanches_emergenciais_diarios(solicitacao, lista_erros)

        assert solicitacao.dias_lanche_emergencial_diario == ["05", "07"]
        assert retorno == [
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Restam dias a serem lançados nos Lanches Emergenciais.",
            }
        ]

    def test_retorna_sem_erros_quando_escola_emebs_tem_todos_os_dias_lancados(
        self,
        solicitacao_medicao_inicial_factory,
        escola_emebs,
        lanche_emergencial_diario_factory,
        dia_calendario_factory,
        medicao_factory,
        valor_medicao_factory,
        categoria_medicao_factory,
    ):
        solicitacao = self._cria_solicitacao_emebs(
            solicitacao_medicao_inicial_factory, escola_emebs
        )
        self._cria_lanche_e_calendario(
            solicitacao,
            lanche_emergencial_diario_factory,
            dia_calendario_factory,
        )
        medicao = medicao_factory.create(
            solicitacao_medicao_inicial=solicitacao,
            periodo_escolar=None,
            grupo__nome="Solicitações de Alimentação",
        )
        categoria = categoria_medicao_factory.create()
        valor_medicao_factory.create(
            medicao=medicao,
            categoria_medicao=categoria,
            nome_campo="lanche_emergencial",
            dia="05",
            valor=1,
        )
        valor_medicao_factory.create(
            medicao=medicao,
            categoria_medicao=categoria,
            nome_campo="lanche_emergencial",
            dia="07",
            valor=1,
        )
        lista_erros = []

        retorno = validate_lanches_emergenciais_diarios(solicitacao, lista_erros)

        assert retorno == []
