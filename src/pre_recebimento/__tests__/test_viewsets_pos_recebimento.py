import pytest
from rest_framework import status

from src.dados_comuns.fluxo_status import FichaDeRecebimentoWorkflow
from src.pre_recebimento.cronograma_entrega.fixtures.factories.cronograma_factory import (
    CronogramaFactory,
    EtapasDoCronogramaFactory,
)
from src.recebimento.fixtures.factories.ficha_de_recebimento_factory import (
    FichaDeRecebimentoFactory,
)
from src.terceirizada.fixtures.factories.terceirizada_factory import (
    ContratoFactory,
    EmpresaFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def contrato():
    return ContratoFactory(terceirizada=EmpresaFactory())


@pytest.fixture
def ficha_assinada():
    """Ficha de recebimento com status 'Assinado CODAE' vinculada a um
    cronograma/empresa/contrato próprios."""
    empresa = EmpresaFactory()
    contrato = ContratoFactory(terceirizada=empresa)
    cronograma = CronogramaFactory(contrato=contrato, empresa=empresa)
    etapa = EtapasDoCronogramaFactory(cronograma=cronograma)
    return FichaDeRecebimentoFactory(
        etapa=etapa, status=FichaDeRecebimentoWorkflow.ASSINADA
    )


def test_cronogramas_list_filtra_por_contrato(
    client_autenticado_codae_dilog,
    ficha_assinada,
    contrato,
):
    cronograma = ficha_assinada.etapa.cronograma
    outro_cronograma = CronogramaFactory(
        contrato=contrato, empresa=contrato.terceirizada
    )

    response = client_autenticado_codae_dilog.get(
        "/cronogramas/lista-cronogramas-pos-recebimento/",
        {"contrato_id": str(cronograma.contrato.uuid)},
    )

    assert response.status_code == status.HTTP_200_OK
    resultados = response.json()["results"]
    uuids = [item["uuid"] for item in resultados]
    assert str(cronograma.uuid) in uuids
    assert str(outro_cronograma.uuid) not in uuids


def test_cronogramas_list_com_uuid_invalido_nao_retorna_erro_500(
    client_autenticado_dilog_cronograma,
):
    response = client_autenticado_dilog_cronograma.get(
        "/cronogramas/lista-cronogramas-pos-recebimento/",
        {"contrato_id": "uuid-invalido"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


def test_cronogramas_list_negado_para_perfil_sem_permissao(
    client_autenticado_qualidade,
):
    response = client_autenticado_qualidade.get(
        "/cronogramas/lista-cronogramas-pos-recebimento/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_cronograma_detalhe_retorna_dados_para_preenchimento(
    client_autenticado_dilog_cronograma,
    ficha_assinada,
):
    cronograma = ficha_assinada.etapa.cronograma

    response = client_autenticado_dilog_cronograma.get(
        f"/cronogramas/{cronograma.uuid}/dados-cronograma-pos-recebimento/"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["uuid"] == str(cronograma.uuid)
    assert data["numero"] == cronograma.numero
    assert data["produto"] == cronograma.ficha_tecnica.produto.nome
    assert data["processo_sei"] == cronograma.contrato.processo
    assert data["unidade_medida"] == cronograma.unidade_medida.nome
    assert data["unidade_medida_abreviacao"] == cronograma.unidade_medida.abreviacao
