from rest_framework import status

from ...services import NovoSGPServicoLogado, NovoSGPServicoLogadoException

ENDPOINT_ALUNOS_POR_PERIODO = "quantidade-alunos-por-periodo"


ENDPOINT_LOTES = "lotes"


ENDPOINT_LISTA_DIAS = "dias-suspensao-atividades/lista-dias"


def _mock_obter_token_erro(monkeypatch):
    def _raise_login_error(self):
        raise NovoSGPServicoLogadoException("Não foi possível logar no sistema")

    monkeypatch.setattr(NovoSGPServicoLogado, "_obter_token", _raise_login_error)


ENDPOINT_LOTES_SIMPLES = "lotes-simples"


def test_url_endpoint_subprefeitura_actions(client_autenticado_da_dre):
    client = client_autenticado_da_dre

    response = client.get("/subprefeituras/lista-completa/")
    assert response.status_code == status.HTTP_200_OK
