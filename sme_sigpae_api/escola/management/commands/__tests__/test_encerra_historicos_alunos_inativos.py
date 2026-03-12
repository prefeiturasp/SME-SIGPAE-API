import datetime
import io
from unittest import mock

import pytest
from django.core.management import call_command
from model_bakery import baker

from sme_sigpae_api.escola.management.commands.encerra_historicos_alunos_inativos import (
    CODIGO_SITUACAO_CONCLUIDO,
    DATA_FIM_PADRAO,
    SITUACAO_CONCLUIDA,
    Command,
)
from sme_sigpae_api.escola.models import HistoricoMatriculaAluno

pytestmark = pytest.mark.django_db


@pytest.fixture
def escola():
    return baker.make("Escola", codigo_eol="400001")


@pytest.fixture
def outra_escola():
    return baker.make("Escola", codigo_eol="400002")


@pytest.fixture
def aluno_ativo(escola):
    """Aluno com código EOL que será retornado como ativo pela API."""
    return baker.make("Aluno", codigo_eol="1000001", escola=escola)


@pytest.fixture
def aluno_inativo(escola):
    """Aluno com código EOL que NÃO será retornado como ativo pela API."""
    return baker.make("Aluno", codigo_eol="2000002", escola=escola)


@pytest.fixture
def historico_aluno_ativo(aluno_ativo, escola):
    return baker.make(
        "HistoricoMatriculaAluno",
        aluno=aluno_ativo,
        escola=escola,
        data_inicio=datetime.date(2025, 2, 1),
        data_fim=None,
        codigo_situacao=1,
        situacao="Ativo",
    )


@pytest.fixture
def historico_aluno_inativo(aluno_inativo, escola):
    return baker.make(
        "HistoricoMatriculaAluno",
        aluno=aluno_inativo,
        escola=escola,
        data_inicio=datetime.date(2025, 2, 1),
        data_fim=None,
        codigo_situacao=1,
        situacao="Ativo",
    )


def _mock_api_response(codigos_ativos, status_code=200):
    """Cria uma response mockada da API com os alunos ativos informados."""
    dados = [
        {
            "codigoAluno": int(cod),
            "codigoSituacaoMatricula": 1,
            "codigoTipoTurma": 1,
        }
        for cod in codigos_ativos
    ]
    resp = mock.MagicMock()
    resp.status_code = status_code
    resp.json.return_value = dados
    resp.text = ""
    return resp


@mock.patch(
    "sme_sigpae_api.escola.management.commands.encerra_historicos_alunos_inativos.requests.get"
)
class TestAlunoPermanenceAtivo:
    """Quando o aluno está ativo na API, o histórico NÃO deve ser encerrado."""

    def test_historico_nao_e_encerrado(self, mock_get, historico_aluno_ativo, escola):
        mock_get.return_value = _mock_api_response(["1000001"])

        call_command("encerra_historicos_alunos_inativos")

        historico_aluno_ativo.refresh_from_db()
        assert historico_aluno_ativo.data_fim is None
        assert historico_aluno_ativo.situacao == "Ativo"
        assert historico_aluno_ativo.codigo_situacao == 1

    def test_historico_ativo_mantido_entre_multiplos_alunos(
        self, mock_get, historico_aluno_ativo, historico_aluno_inativo, escola
    ):
        """Ao encerrar um aluno inativo, o ativo deve permanecer inalterado."""
        mock_get.return_value = _mock_api_response(["1000001"])

        call_command("encerra_historicos_alunos_inativos")

        historico_aluno_ativo.refresh_from_db()
        assert historico_aluno_ativo.data_fim is None
        assert historico_aluno_ativo.codigo_situacao == 1


@mock.patch(
    "sme_sigpae_api.escola.management.commands.encerra_historicos_alunos_inativos.requests.get"
)
class TestAlunoInativoEncerraHistorico:
    """Quando o aluno NÃO está ativo na API, o histórico deve ser encerrado."""

    def test_historico_encerrado_com_data_fim_padrao(
        self, mock_get, historico_aluno_inativo, escola
    ):
        """Sem outro histórico ativo em outra escola, data_fim = DATA_FIM_PADRAO."""
        mock_get.return_value = _mock_api_response([])

        call_command("encerra_historicos_alunos_inativos")

        historico_aluno_inativo.refresh_from_db()
        assert historico_aluno_inativo.data_fim == DATA_FIM_PADRAO
        assert historico_aluno_inativo.codigo_situacao == CODIGO_SITUACAO_CONCLUIDO
        assert historico_aluno_inativo.situacao == SITUACAO_CONCLUIDA

    def test_historico_encerrado_com_data_fim_baseada_em_proximo_historico(
        self, mock_get, aluno_inativo, historico_aluno_inativo, escola, outra_escola
    ):
        """Se há histórico ativo em outra escola, data_fim = data_inicio desse - 1."""
        data_inicio_outra = datetime.date(2025, 6, 15)
        baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno_inativo,
            escola=outra_escola,
            data_inicio=data_inicio_outra,
            data_fim=None,
            codigo_situacao=1,
            situacao="Ativo",
        )
        mock_get.return_value = _mock_api_response([])

        call_command("encerra_historicos_alunos_inativos")

        historico_aluno_inativo.refresh_from_db()
        assert (
            historico_aluno_inativo.data_fim
            == data_inicio_outra - datetime.timedelta(days=1)
        )
        assert historico_aluno_inativo.codigo_situacao == CODIGO_SITUACAO_CONCLUIDO
        assert historico_aluno_inativo.situacao == SITUACAO_CONCLUIDA

    def test_multiplos_historicos_inativos_encerrados(self, mock_get, escola):
        """Todos os alunos inativos da escola devem ter histórico encerrado."""
        aluno1 = baker.make("Aluno", codigo_eol="3000001")
        aluno2 = baker.make("Aluno", codigo_eol="3000002")
        h1 = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno1,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 1, 1),
            codigo_situacao=1,
            situacao="Ativo",
        )
        h2 = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno2,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 3, 1),
            codigo_situacao=1,
            situacao="Ativo",
        )
        mock_get.return_value = _mock_api_response([])

        call_command("encerra_historicos_alunos_inativos")

        h1.refresh_from_db()
        h2.refresh_from_db()
        assert h1.data_fim == DATA_FIM_PADRAO
        assert h2.data_fim == DATA_FIM_PADRAO


@mock.patch(
    "sme_sigpae_api.escola.management.commands.encerra_historicos_alunos_inativos.requests.get"
)
class TestHistoricoJaEncerradoNaoEAlterado:
    """Históricos já com data_fim preenchida não devem ser tocados."""

    def test_historico_com_data_fim_nao_e_modificado(
        self, mock_get, aluno_inativo, escola
    ):
        data_fim_original = datetime.date(2024, 12, 1)
        historico = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno_inativo,
            escola=escola,
            data_inicio=datetime.date(2024, 1, 1),
            data_fim=data_fim_original,
            codigo_situacao=5,
            situacao="Concluído",
        )
        mock_get.return_value = _mock_api_response([])

        call_command("encerra_historicos_alunos_inativos")

        historico.refresh_from_db()
        assert historico.data_fim == data_fim_original
        assert historico.codigo_situacao == 5


@mock.patch(
    "sme_sigpae_api.escola.management.commands.encerra_historicos_alunos_inativos.requests.get"
)
class TestFalhaAPINaoAlteraHistoricos:
    """Se a API falha (retorna None), nenhum histórico deve ser alterado."""

    def test_api_falha_nao_encerra_historicos(
        self, mock_get, historico_aluno_inativo, escola
    ):
        resp = mock.MagicMock()
        resp.status_code = 500
        resp.text = "Internal Server Error"
        mock_get.return_value = resp

        call_command("encerra_historicos_alunos_inativos")

        historico_aluno_inativo.refresh_from_db()
        assert historico_aluno_inativo.data_fim is None
        assert historico_aluno_inativo.codigo_situacao == 1


class TestCalculaDataFim:
    """Testes unitários para o método _calcula_data_fim."""

    def test_sem_proximo_historico_retorna_data_padrao(self, escola):
        aluno = baker.make("Aluno", codigo_eol="5000001")
        historico = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 1, 1),
            codigo_situacao=1,
        )

        resultado = Command()._calcula_data_fim(historico)
        assert resultado == DATA_FIM_PADRAO

    def test_com_proximo_historico_em_outra_escola(self, escola, outra_escola):
        aluno = baker.make("Aluno", codigo_eol="5000002")
        historico = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 1, 1),
            codigo_situacao=1,
        )
        baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=outra_escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 7, 1),
            codigo_situacao=1,
        )

        resultado = Command()._calcula_data_fim(historico)
        assert resultado == datetime.date(2025, 6, 30)

    def test_ignora_historico_com_data_fim_preenchida_em_outra_escola(
        self, escola, outra_escola
    ):
        aluno = baker.make("Aluno", codigo_eol="5000003")
        historico = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 1, 1),
            codigo_situacao=1,
        )
        baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=outra_escola,
            data_inicio=datetime.date(2025, 3, 1),
            data_fim=datetime.date(2025, 5, 1),
            codigo_situacao=5,
        )

        resultado = Command()._calcula_data_fim(historico)
        assert resultado == DATA_FIM_PADRAO

    def test_usa_proximo_historico_mais_antigo(self, escola, outra_escola):
        """Se há múltiplos históricos ativos em outras escolas, usa o de data_inicio mais antiga."""
        aluno = baker.make("Aluno", codigo_eol="5000004")
        terceira_escola = baker.make("Escola", codigo_eol="400003")
        historico = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 1, 1),
            codigo_situacao=1,
        )
        baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=outra_escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 9, 1),
            codigo_situacao=1,
        )
        baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno,
            escola=terceira_escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 5, 1),
            codigo_situacao=1,
        )

        resultado = Command()._calcula_data_fim(historico)
        assert resultado == datetime.date(2025, 4, 30)


@mock.patch(
    "sme_sigpae_api.escola.management.commands.encerra_historicos_alunos_inativos.requests.get"
)
class TestEscolasSemHistoricos:
    """Escola sem históricos ativos não deve causar erro."""

    def test_escola_sem_historicos_ativos(self, mock_get, escola):
        mock_get.return_value = _mock_api_response([])
        out = io.StringIO()

        call_command("encerra_historicos_alunos_inativos", stdout=out)

        output = out.getvalue()
        assert "Processamento concluído" in output


@mock.patch(
    "sme_sigpae_api.escola.management.commands.encerra_historicos_alunos_inativos.requests.get"
)
class TestMistoAtivosInativos:
    """Cenário com alunos ativos e inativos na mesma escola."""

    def test_apenas_inativos_sao_encerrados(self, mock_get, escola):
        aluno_a = baker.make("Aluno", codigo_eol="6000001")
        aluno_b = baker.make("Aluno", codigo_eol="6000002")
        aluno_c = baker.make("Aluno", codigo_eol="6000003")

        h_a = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno_a,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 1, 1),
            codigo_situacao=1,
            situacao="Ativo",
        )
        h_b = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno_b,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 2, 1),
            codigo_situacao=1,
            situacao="Ativo",
        )
        h_c = baker.make(
            "HistoricoMatriculaAluno",
            aluno=aluno_c,
            escola=escola,
            data_fim=None,
            data_inicio=datetime.date(2025, 3, 1),
            codigo_situacao=1,
            situacao="Ativo",
        )

        # Apenas aluno_a e aluno_c são retornados como ativos pela API
        mock_get.return_value = _mock_api_response(["6000001", "6000003"])

        call_command("encerra_historicos_alunos_inativos")

        h_a.refresh_from_db()
        h_b.refresh_from_db()
        h_c.refresh_from_db()

        # aluno_a: ativo -> não encerrado
        assert h_a.data_fim is None
        assert h_a.codigo_situacao == 1

        # aluno_b: inativo -> encerrado
        assert h_b.data_fim == DATA_FIM_PADRAO
        assert h_b.codigo_situacao == CODIGO_SITUACAO_CONCLUIDO
        assert h_b.situacao == SITUACAO_CONCLUIDA

        # aluno_c: ativo -> não encerrado
        assert h_c.data_fim is None
        assert h_c.codigo_situacao == 1
