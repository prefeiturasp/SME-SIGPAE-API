import pytest
from datetime import date
from rest_framework import status
from model_bakery import baker
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import InterrupcaoProgramadaEntrega

pytestmark = pytest.mark.django_db

def test_datas_bloqueadas_armazenavel(client_autenticado_vinculo_dilog_cronograma):
    client, _ = client_autenticado_vinculo_dilog_cronograma
    url = "/interrupcao-programada-entrega/datas-bloqueadas-armazenavel/"
    
    ano_atual = date.today().year
    ano_proximo = ano_atual + 1
    
    # Criar interrupções válidas (ARMAZENAVEL, ano atual e próximo)
    data1 = date(ano_atual, 1, 10)
    data2 = date(ano_proximo, 2, 20)
    
    baker.make(
        "InterrupcaoProgramadaEntrega",
        data=data1,
        tipo_calendario=InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_ARMAZENAVEL
    )
    baker.make(
        "InterrupcaoProgramadaEntrega",
        data=data2,
        tipo_calendario=InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_ARMAZENAVEL
    )
    
    # Criar interrupção de outro tipo (não deve retornar)
    baker.make(
        "InterrupcaoProgramadaEntrega",
        data=date(ano_atual, 3, 15),
        tipo_calendario=InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_PONTO_A_PONTO
    )
    
    # Criar interrupção de outro ano (não deve retornar)
    baker.make(
        "InterrupcaoProgramadaEntrega",
        data=date(ano_atual - 1, 12, 25),
        tipo_calendario=InterrupcaoProgramadaEntrega.TIPO_CALENDARIO_ARMAZENAVEL
    )

    response = client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    
    assert len(results) == 2
    
    # Datas válidas devem estar no resultado
    # O QuerySet values_list retorna datetime.date objects que são serializados como strings ISO
    assert data1 in results
    assert data2 in results
    
    # Datas inválidas não devem estar no resultado
    assert date(ano_atual, 3, 15) not in results
    assert date(ano_atual - 1, 12, 25) not in results
