from model_bakery import baker
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


def test_url_endpoint_lotes(client_autenticado):
    response = client_autenticado.get(f"/{ENDPOINT_LOTES}/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_lotes_delete(client_autenticado, lote):
    response = client_autenticado.delete(f"/{ENDPOINT_LOTES}/{lote.uuid}/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_url_lotes_actions(client_autenticado_da_dre):
    client = client_autenticado_da_dre

    response = client.get("/lotes/meus-lotes-vinculados/")
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_lotes_simples_filtro_edital(
    client_autenticado, lote, diretoria_regional
):
    from src.terceirizada.models import Contrato, Edital

    edital = baker.make(Edital, numero="Edital Teste")
    outro_lote = baker.make("Lote", nome="Outro Lote")
    contrato = baker.make(
        Contrato,
        edital=edital,
        numero="CT-001",
        lotes=[lote],
        make_m2m=True,
    )

    response = client_autenticado.get(
        f"/{ENDPOINT_LOTES_SIMPLES}/",
        {"contratos_do_lote__edital__uuid": edital.uuid},
    )

    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    uuids_retornados = [r["uuid"] for r in results]
    assert str(lote.uuid) in uuids_retornados
    assert str(outro_lote.uuid) not in uuids_retornados
