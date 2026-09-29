import pytest
from freezegun.api import freeze_time

from src.escola.fixtures.factories.escola_factory import FaixaEtariaFactory
from src.escola.management.commands.atualiza_cache_matriculados_por_faixa import (
    Command,
)


@pytest.mark.django_db
class GetListaFiltradaAlunosEolTest:
    def setup_method(self):
        self.command = Command()

    def _monta_aluno(self, codigo, data_nascimento, tipo_turno=6):
        return {
            "codigoAluno": codigo,
            "nomeAluno": "ALUNO TESTE",
            "dataNascimento": f"{data_nascimento}T00:00:00",
            "tipoTurno": tipo_turno,
        }

    @freeze_time("2026-09-16")
    def test_aluno_que_pertence_a_faixa_e_incluido(self):
        faixa = FaixaEtariaFactory.create(inicio=48, fim=73)
        lista = [self._monta_aluno("1", "2020-09-01")]

        filtrados = self.command.get_lista_filtrada_alunos_eol(lista, 6, faixa)

        assert len(filtrados) == 1

    @freeze_time("2026-09-16")
    def test_aluno_mais_velho_que_6_anos_e_incluido_na_ultima_faixa(self):
        faixa = FaixaEtariaFactory.create(inicio=48, fim=73)
        lista = [self._monta_aluno("1", "2020-05-25")]

        filtrados = self.command.get_lista_filtrada_alunos_eol(lista, 6, faixa)

        assert len(filtrados) == 1

    @freeze_time("2026-09-16")
    def test_aluno_fora_da_faixa_sem_mais_de_6_anos_e_excluido(self):
        faixa = FaixaEtariaFactory.create(inicio=48, fim=73)
        lista = [self._monta_aluno("1", "2023-01-01")]

        filtrados = self.command.get_lista_filtrada_alunos_eol(lista, 6, faixa)

        assert len(filtrados) == 0

    @freeze_time("2026-09-16")
    def test_aluno_mais_velho_nao_e_incluido_em_faixa_que_nao_e_a_ultima(self):
        faixa = FaixaEtariaFactory.create(inicio=12, fim=48)
        lista = [self._monta_aluno("1", "2020-05-25")]

        filtrados = self.command.get_lista_filtrada_alunos_eol(lista, 6, faixa)

        assert len(filtrados) == 0

    @freeze_time("2026-09-16")
    def test_aluno_de_outro_periodo_e_excluido(self):
        faixa = FaixaEtariaFactory.create(inicio=48, fim=73)
        lista = [self._monta_aluno("1", "2020-05-25", tipo_turno=4)]

        filtrados = self.command.get_lista_filtrada_alunos_eol(lista, 6, faixa)

        assert len(filtrados) == 0
