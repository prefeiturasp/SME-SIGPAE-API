import json

import pytest
from rest_framework import status

from sme_terceirizadas.logistica.models import SolicitacaoRemessa

pytestmark = pytest.mark.django_db


def test_url_authorized_solicitacao(client_autenticado_dilog):
    response = client_autenticado_dilog.get('/solicitacao-remessa/')
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_numeros(client_autenticado_dilog, guia):
    response = client_autenticado_dilog.get('/solicitacao-remessa/lista-numeros/')
    assert response.status_code == status.HTTP_200_OK


def test_url_authorized_confirmadas(client_autenticado_dilog):
    response = client_autenticado_dilog.get('/solicitacao-remessa/lista-requisicoes-confirmadas/')
    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor(client_autenticado_distribuidor, solicitacao, guia):
    response = client_autenticado_distribuidor.get(
        f'/solicitacao-remessa/exporta-excel-visao-entregas/'
        f'?uuid={str(solicitacao.uuid)}&tem_conferencia=true&tem_insucesso=true'
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor_conferidas(client_autenticado_distribuidor, solicitacao, guia):
    response = client_autenticado_distribuidor.get(
        f'/solicitacao-remessa/exporta-excel-visao-entregas/'
        f'?uuid={str(solicitacao.uuid)}&tem_conferencia=true&tem_insucesso=false'
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor_insucessos(client_autenticado_distribuidor, solicitacao, guia):
    response = client_autenticado_distribuidor.get(
        f'/solicitacao-remessa/exporta-excel-visao-entregas/'
        f'?uuid={str(solicitacao.uuid)}&tem_conferencia=false&tem_insucesso=true'
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_distribuidor_sem_parametros(client_autenticado_distribuidor, solicitacao, guia):
    response = client_autenticado_distribuidor.get(
        f'/solicitacao-remessa/exporta-excel-visao-entregas/?uuid={str(solicitacao.uuid)}'
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_exportar_excel_entregas_dilog(client_autenticado_dilog, solicitacao, guia):
    response = client_autenticado_dilog.get(
        f'/solicitacao-remessa/exporta-excel-visao-entregas/'
        f'?uuid={str(solicitacao.uuid)}&tem_conferencia=true&tem_insucesso=true'
    )

    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_entregas_dilog_sem_parametros(client_autenticado_dilog, solicitacao, guia):
    response = client_autenticado_dilog.get(
        f'/solicitacao-remessa/exporta-excel-visao-entregas/?uuid={str(solicitacao.uuid)}'
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_excel_analitica_dilog(client_autenticado_dilog, solicitacao, guia):
    response = client_autenticado_dilog.get('/solicitacao-remessa/exporta-excel-visao-analitica/')
    assert response.status_code == status.HTTP_200_OK


def test_url_exportar_excel_analitica_distribuidor(client_autenticado_distribuidor, solicitacao, guia):
    response = client_autenticado_distribuidor.get('/solicitacao-remessa/exporta-excel-visao-analitica/')
    assert response.status_code == status.HTTP_200_OK


def test_arquivar_guias_da_requisicao(client_autenticado_dilog, solicitacao, guia):
    payload = {
        'numero_requisicao': str(solicitacao.numero_solicitacao),
        'guias': [f'{guia.numero_guia}']
    }

    response = client_autenticado_dilog.post(
        '/solicitacao-remessa/arquivar/',
        data=json.dumps(payload),
        content_type='application/json'
    )

    requisicao = SolicitacaoRemessa.objects.first()

    assert response.status_code == status.HTTP_200_OK
    assert requisicao.situacao == SolicitacaoRemessa.ARQUIVADA


def test_desarquivar_guias_da_requisicao(client_autenticado_dilog, solicitacao, guia):
    solicitacao.situacao = SolicitacaoRemessa.ARQUIVADA
    solicitacao.save()
    guia.situacao = SolicitacaoRemessa.ARQUIVADA
    guia.save()
    payload = {
        'numero_requisicao': str(solicitacao.numero_solicitacao),
        'guias': [f'{guia.numero_guia}']
    }
    response = client_autenticado_dilog.post(
        '/solicitacao-remessa/desarquivar/',
        data=json.dumps(payload),
        content_type='application/json'
    )

    requisicao = SolicitacaoRemessa.objects.first()

    assert response.status_code == status.HTTP_200_OK
    assert requisicao.situacao == SolicitacaoRemessa.ATIVA


def test_arquivar_guias_da_requisicao_distribuidor_nao_pode(client_autenticado_distribuidor, solicitacao, guia):
    payload = {
        'numero_requisicao': str(solicitacao.numero_solicitacao),
        'guias': [f'{guia.numero_guia}']
    }

    response = client_autenticado_distribuidor.post(
        '/solicitacao-remessa/arquivar/',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_desarquivar_guias_da_requisicao_distribuidor_nao_pode(client_autenticado_distribuidor, solicitacao, guia):
    payload = {
        'numero_requisicao': str(solicitacao.numero_solicitacao),
        'guias': [f'{guia.numero_guia}']
    }
    response = client_autenticado_distribuidor.post(
        '/solicitacao-remessa/desarquivar/',
        data=json.dumps(payload),
        content_type='application/json'
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_url_relatorio_guia_remessa_authorized_dilog(client_autenticado_dilog, solicitacao):
    response = client_autenticado_dilog.get(
        f'/solicitacao-remessa/{str(solicitacao.uuid)}/relatorio-guias-da-requisicao/')
    assert response.status_code == status.HTTP_200_OK
