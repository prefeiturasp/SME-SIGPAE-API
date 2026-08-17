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
def empresa():
    return EmpresaFactory()


@pytest.fixture
def ficha_assinada():
    """Ficha de recebimento com status 'Assinado CODAE' vinculada a um
    cronograma/empresa próprios (independentes da fixture empresa)."""
    empresa = EmpresaFactory()
    contrato = ContratoFactory(terceirizada=empresa)
    cronograma = CronogramaFactory(contrato=contrato, empresa=empresa)
    etapa = EtapasDoCronogramaFactory(cronograma=cronograma)
    return FichaDeRecebimentoFactory(
        etapa=etapa, status=FichaDeRecebimentoWorkflow.ASSINADA
    )


def test_empresas_list_retorna_apenas_empresas_com_ficha_assinada(
    client_autenticado_dilog_cronograma,
    ficha_assinada,
    empresa,
):
    empresa_sem_ficha = empresa
    empresa_com_ficha = ficha_assinada.etapa.cronograma.empresa

    response = client_autenticado_dilog_cronograma.get(
        "/terceirizadas/lista-empresas-pos-recebimento/"
    )

    assert response.status_code == status.HTTP_200_OK
    resultados = response.json()["results"]
    uuids = [item["uuid"] for item in resultados]
    assert str(empresa_com_ficha.uuid) in uuids
    assert str(empresa_sem_ficha.uuid) not in uuids


def test_empresas_list_negado_para_perfil_sem_permissao(client_autenticado_qualidade):
    response = client_autenticado_qualidade.get(
        "/terceirizadas/lista-empresas-pos-recebimento/"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_contratos_list_filtra_por_empresa(
    client_autenticado_dilog_cronograma,
    ficha_assinada,
    empresa,
):
    cronograma = ficha_assinada.etapa.cronograma
    outro_contrato = ContratoFactory(terceirizada=empresa)

    response = client_autenticado_dilog_cronograma.get(
        "/contratos/lista-contratos-pos-recebimento/",
        {"empresa_id": str(cronograma.empresa.uuid)},
    )

    assert response.status_code == status.HTTP_200_OK
    resultados = response.json()["results"]
    uuids = [item["uuid"] for item in resultados]
    assert str(cronograma.contrato.uuid) in uuids
    assert str(outro_contrato.uuid) not in uuids


def test_contratos_list_com_uuid_invalido_nao_retorna_erro_500(
    client_autenticado_dilog_cronograma,
):
    response = client_autenticado_dilog_cronograma.get(
        "/contratos/lista-contratos-pos-recebimento/",
        {"empresa_id": "uuid-invalido"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []
