import pytest
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from sme_sigpae_api.terceirizada.models import Terceirizada

pytestmark = pytest.mark.django_db


def test_post_cronogramas(
    client_autenticado_vinculo_dilog_cronograma,
    contrato_factory,
    empresa_factory,
    ficha_tecnica_factory,
    unidade_medida_factory,
    tipo_embalagem_qld_factory,
):
    client, _ = client_autenticado_vinculo_dilog_cronograma
    empresa = empresa_factory(tipo_servico=Terceirizada.FORNECEDOR)
    contrato = contrato_factory(terceirizada=empresa)
    ficha_tecnica = ficha_tecnica_factory()
    armazem = empresa_factory(tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM)
    unidade_medida = unidade_medida_factory()
    tipo_embalagem_qld = tipo_embalagem_qld_factory()

    payload = {
        "cadastro_finalizado": True,
        "contrato": f"{contrato.uuid}",
        "empresa": f"{empresa.uuid}",
        "ficha_tecnica": f"{ficha_tecnica.uuid}",
        "armazem": f"{armazem.uuid}",
        "qtd_total_programada": "10",
        "unidade_medida": f"{unidade_medida.uuid}",
        "tipo_embalagem_secundaria": f"{tipo_embalagem_qld.uuid}",
        "custo_unitario_produto": 1.59,
        "etapas": [
            {
                "numero_empenho": "10",
                "qtd_total_empenho": 10,
                "etapa": 1,
                "data_programada": "2024-07-29",
                "quantidade": "10",
                "total_embalagens": "10",
            }
        ],
        "programacoes_de_recebimento": [{}],
        "password": DJANGO_ADMIN_PASSWORD,
    }
    response = client.post(f"/cronogramas/", payload)

    assert response.status_code == status.HTTP_201_CREATED
