from datetime import datetime, timedelta
import json

import pytest
from rest_framework import status

from sme_sigpae_api.logistica.models import (
    SolicitacaoDeAlteracaoRequisicao,
    SolicitacaoRemessa,
)

pytestmark = pytest.mark.django_db


def test_url_authorized_solicitacao(client_autenticado_dilog):
    response = client_autenticado_dilog.get("/solicitacao-remessa/")
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_numeros(client_autenticado_dilog, guia):
    response = client_autenticado_dilog.get("/solicitacao-remessa/lista-numeros/")
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_confirmadas(client_autenticado_dilog):
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/lista-requisicoes-confirmadas/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor(
    client_autenticado_distribuidor, solicitacao, guia
):
    response = client_autenticado_distribuidor.get(
        "/solicitacao-remessa/exporta-excel-visao-entregas/"
        f"?uuid={str(solicitacao.uuid)}&tem_conferencia=true&tem_insucesso=true"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor_conferidas(
    client_autenticado_distribuidor, solicitacao, guia
):
    response = client_autenticado_distribuidor.get(
        "/solicitacao-remessa/exporta-excel-visao-entregas/"
        f"?uuid={str(solicitacao.uuid)}&tem_conferencia=true&tem_insucesso=false"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor_insucessos(
    client_autenticado_distribuidor, solicitacao, guia
):
    response = client_autenticado_distribuidor.get(
        "/solicitacao-remessa/exporta-excel-visao-entregas/"
        f"?uuid={str(solicitacao.uuid)}&tem_conferencia=false&tem_insucesso=true"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor_sem_parametros(
    client_autenticado_distribuidor, solicitacao, guia
):
    response = client_autenticado_distribuidor.get(
        f"/solicitacao-remessa/exporta-excel-visao-entregas/?uuid={str(solicitacao.uuid)}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_exportar_excel_entregas_dilog(client_autenticado_dilog, solicitacao, guia):
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/exporta-excel-visao-entregas/"
        f"?uuid={str(solicitacao.uuid)}&tem_conferencia=true&tem_insucesso=true"
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_dilog_sem_parametros(
    client_autenticado_dilog, solicitacao, guia
):
    response = client_autenticado_dilog.get(
        f"/solicitacao-remessa/exporta-excel-visao-entregas/?uuid={str(solicitacao.uuid)}"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_excel_analitica_dilog(client_autenticado_dilog, solicitacao, guia):
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/exporta-excel-visao-analitica/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_analitica_distribuidor(
    client_autenticado_distribuidor, solicitacao, guia
):
    response = client_autenticado_distribuidor.get(
        "/solicitacao-remessa/exporta-excel-visao-analitica/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_arquivar_guias_da_requisicao(client_autenticado_dilog, solicitacao, guia):
    payload = {
        "numero_requisicao": str(solicitacao.numero_solicitacao),
        "guias": [f"{guia.numero_guia}"],
    }

    response = client_autenticado_dilog.post(
        "/solicitacao-remessa/arquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    requisicao = SolicitacaoRemessa.objects.first()

    assert response.status_code == status.HTTP_200_OK
    assert requisicao.situacao == SolicitacaoRemessa.ARQUIVADA
    
def test_arquivar_guias_da_requisicao_sem_numero_requisicao(client_autenticado_dilog, guia):
    payload = {
        "numero_requisicao": None,
        "guias": [f"{guia.numero_guia}"],
    }

    response = client_autenticado_dilog.post(
        "/solicitacao-remessa/arquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    mensagem = "É necessario informar o número da requisição ao qual a(s) guia(s) pertece(m)."
    assert mensagem in response.json()
    
def test_arquivar_guias_da_requisicao_sem_guias(client_autenticado_dilog, solicitacao):
    payload = {
        "numero_requisicao": str(solicitacao.numero_solicitacao),
        "guias": None,
    }

    response = client_autenticado_dilog.post(
        "/solicitacao-remessa/arquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    mensagem = "É necessario informar o número das guias para arquivamento."
    assert mensagem in response.json()

def test_arquivar_guias_da_requisicao_distribuidor_nao_pode(
    client_autenticado_distribuidor, solicitacao, guia
):
    payload = {
        "numero_requisicao": str(solicitacao.numero_solicitacao),
        "guias": [f"{guia.numero_guia}"],
    }

    response = client_autenticado_distribuidor.post(
        "/solicitacao-remessa/arquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_desarquivar_guias_da_requisicao_distribuidor_nao_pode(
    client_autenticado_distribuidor, solicitacao, guia
):
    payload = {
        "numero_requisicao": str(solicitacao.numero_solicitacao),
        "guias": [f"{guia.numero_guia}"],
    }
    response = client_autenticado_distribuidor.post(
        "/solicitacao-remessa/desarquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    
def test_desarquivar_guias_da_requisicao(client_autenticado_dilog, solicitacao, guia):
    solicitacao.situacao = SolicitacaoRemessa.ARQUIVADA
    solicitacao.save()
    guia.situacao = SolicitacaoRemessa.ARQUIVADA
    guia.save()
    payload = {
        "numero_requisicao": str(solicitacao.numero_solicitacao),
        "guias": [f"{guia.numero_guia}"],
    }
    response = client_autenticado_dilog.post(
        "/solicitacao-remessa/desarquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    requisicao = SolicitacaoRemessa.objects.first()

    assert response.status_code == status.HTTP_200_OK
    assert requisicao.situacao == SolicitacaoRemessa.ATIVA

def test_desarquivar_guias_da_requisicao_sem_numero_requisicao(client_autenticado_dilog, guia):
    payload = {
        "numero_requisicao": None,
        "guias": [f"{guia.numero_guia}"],
    }

    response = client_autenticado_dilog.post(
        "/solicitacao-remessa/desarquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    mensagem = "É necessario informar o número da requisição ao qual a(s) guia(s) pertece(m)."
    assert mensagem in response.json()
    
def test_desarquivar_guias_da_requisicao_sem_guias(client_autenticado_dilog, solicitacao):
    payload = {
        "numero_requisicao": str(solicitacao.numero_solicitacao),
        "guias": None,
    }

    response = client_autenticado_dilog.post(
        "/solicitacao-remessa/desarquivar/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    mensagem = "É necessario informar o número das guias para desarquivamento."
    assert mensagem in response.json()

def test_url_relatorio_guia_remessa_authorized_dilog(
    client_autenticado_dilog, solicitacao
):
    response = client_autenticado_dilog.get(
        f"/solicitacao-remessa/{str(solicitacao.uuid)}/relatorio-guias-da-requisicao/"
    )
    assert response.status_code == status.HTTP_200_OK


def test_url_solicitacao_de_alteracao_de_requisicao(
    client_autenticado_dilog, solicitacao, guia
):
    response = client_autenticado_dilog.get(
        "/solicitacao-de-alteracao-de-requisicao/?motivos="
        f"{SolicitacaoDeAlteracaoRequisicao.MOTIVO_ALTERAR_ALIMENTO}/"
    )
    resposta = json.loads(response.content)
    esperado = {"count": 0, "next": None, "previous": None, "results": []}
    assert response.status_code == status.HTTP_200_OK
    assert resposta == esperado


def test_solicitacao_remessa_envio_envia_grade(
    client_autenticado_codae_dilog, setup_solicitacao_remessa_envio
):

    response = client_autenticado_codae_dilog.post(
        "/solicitacao-remessa-envio/envia-grade/",
        data=setup_solicitacao_remessa_envio,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK 
    
# def test_solicitacao_confirma_cancelamento_guias(
#     client_autenticado_distribuidor, setup_solicitacao_confirmar_cancelamento
# ):

#     response = client_autenticado_distribuidor.post(
#         "/solicitacao-remessa/confirmar-cancelamento/",
#         data=setup_solicitacao_confirmar_cancelamento,
#         content_type="application/json",
#     )
#     assert response.status_code == status.HTTP_200_OK 
#     mensagem = "Cancelamento realizado com sucesso."
#     assert mensagem in response.json()
    
def test_solicitacao_confirma_cancelamento_guias_sem_requisicao(
    client_autenticado_distribuidor, setup_solicitacao_confirmar_cancelamentos_sem_numero_requisicao
):

    response = client_autenticado_distribuidor.post(
        "/solicitacao-remessa/confirmar-cancelamento/",
        data=setup_solicitacao_confirmar_cancelamentos_sem_numero_requisicao,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    mensagem = "É necessario informar o número da requisição ao qual a(s) guia(s) pertece(m)."
    assert mensagem in response.json()
    
    
def test_solicitacao_confirma_cancelamento_guias_sem_guias(
    client_autenticado_distribuidor, setup_solicitacao_confirmar_cancelamentos_sem_guia
):

    response = client_autenticado_distribuidor.post(
        "/solicitacao-remessa/confirmar-cancelamento/",
        data=setup_solicitacao_confirmar_cancelamentos_sem_guia,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    mensagem = "É necessario informar o número das guias para confirmação do cancelamento."
    assert mensagem in response.json()
    

def test_lista_requisicoes_para_envio(client_autenticado_dilog, solicitacao):
    params = {
        "numero_requisicao": solicitacao.numero_solicitacao, 
        "nome_distribuidor": solicitacao.distribuidor.nome, 
        "data_inicio": (datetime.now() - timedelta(days=10)).date(), 
        "data_fim": datetime.now().date()
    }
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/lista-requisicoes-para-envio/",
        params=params,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.json()

def test_lista_requisicoes_para_envio_distribuidor_nao_pode(client_autenticado_distribuidor, solicitacao):
    params = {
        "numero_requisicao": solicitacao.numero_solicitacao, 
        "nome_distribuidor": solicitacao.distribuidor.nome, 
        "data_inicio": (datetime.now() - timedelta(days=10)).date(), 
        "data_fim": datetime.now().date()
    }
    response = client_autenticado_distribuidor.get(
        "/solicitacao-remessa/lista-requisicoes-para-envio/",
        params=params,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_lista_requisicoes_para_envio_sem_numero_requisicao(client_autenticado_dilog, solicitacao, guia):
    params = {
        "nome_distribuidor": solicitacao.distribuidor.nome, 
        "data_inicio": guia.data_entrega, 
        "data_fim": datetime.now().date()
    }
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/lista-requisicoes-para-envio/",
        params=params,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    informacoes = response.json()
    assert "results" in informacoes
    assert len(informacoes["results"]) == 1
    
def test_lista_requisicoes_para_envio_sem_nome_distribuidor(client_autenticado_dilog, solicitacao, guia):
    params = {
        "numero_requisicao": solicitacao.numero_solicitacao, 
        "data_inicio": guia.data_entrega, 
        "data_fim": datetime.now().date()
    }
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/lista-requisicoes-para-envio/",
        params=params,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    informacoes = response.json()
    assert "results" in informacoes
    assert len(informacoes["results"]) == 1
    
def test_lista_requisicoes_para_envio_sem_data_inicio(client_autenticado_dilog, solicitacao):
    params = {
        "numero_requisicao": solicitacao.numero_solicitacao, 
        "nome_distribuidor": solicitacao.distribuidor.nome, 
        "data_fim": datetime.now().date()
    }
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/lista-requisicoes-para-envio/",
        params=params,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    informacoes = response.json()
    assert "results" in informacoes
    assert len(informacoes["results"]) == 1
    
def test_lista_requisicoes_para_envio_sem_data_fim(client_autenticado_dilog, solicitacao, guia):
    params = {
        "numero_requisicao": solicitacao.numero_solicitacao, 
        "nome_distribuidor": solicitacao.distribuidor.nome, 
        "data_inicio": guia.data_entrega, 
    }
    response = client_autenticado_dilog.get(
        "/solicitacao-remessa/lista-requisicoes-para-envio/",
        params=params,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    informacoes = response.json()
    assert "results" in informacoes
    assert len(informacoes["results"]) == 1
    
    
def test_consolidado_alimentos_solicitacao_valida(client_autenticado_dilog, solicitacao, guia, alimento, embalagem):
    response = client_autenticado_dilog.get(f"/solicitacao-remessa/{solicitacao.uuid}/consolidado-alimentos/")

    assert response.status_code == status.HTTP_200_OK
    informacoes = response.json()

    assert len(informacoes) == 1
    assert informacoes[0]["nome_alimento"] == alimento.nome_alimento
    assert informacoes[0]["peso_total"] == embalagem.capacidade_embalagem * embalagem.qtd_volume
    assert len(informacoes[0]["total_embalagens"]) == 1
    assert informacoes[0]["total_embalagens"][0]["descricao_embalagem"] == embalagem.descricao_embalagem

def test_consolidado_alimentos_solicitacao_inexistente(client_autenticado_dilog, solicitacao):
    response = client_autenticado_dilog.get("/solicitacao-remessa/00000000-0000-0000-0000-000000000000/consolidado-alimentos/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == "Solicitação inexistente."
    
def test_consolidado_alimentos_sem_dados(client_autenticado_dilog, solicitacao):
    response = client_autenticado_dilog.get(f"/solicitacao-remessa/{solicitacao.uuid}/consolidado-alimentos/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
    
    