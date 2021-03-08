import json

import pytest
from rest_framework import status

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import HomologacaoProdutoWorkflow

pytestmark = pytest.mark.django_db

ENDPOINT_ANALISE_SENSORIAL = 'analise-sensorial'
TERCEIRIZADA_RESPONDE = 'terceirizada-responde-analise-sensorial'


def test_url_endpoint_homologacao_produto_codae_homologa(client_autenticado_vinculo_codae_produto,
                                                         homologacao_produto_pendente_homologacao):
    assert homologacao_produto_pendente_homologacao.status == HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/{constants.CODAE_HOMOLOGA}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/{constants.CODAE_HOMOLOGA}/')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_homologa' isn't available from state "
                  "'CODAE_HOMOLOGADO'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_homologado/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_homologacao_produto_codae_nao_homologa(client_autenticado_vinculo_codae_produto,
                                                             homologacao_produto_pendente_homologacao):
    assert homologacao_produto_pendente_homologacao.status == HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/{constants.CODAE_NAO_HOMOLOGA}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_NAO_HOMOLOGADO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/{constants.CODAE_NAO_HOMOLOGA}/')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_nao_homologa' isn't available from state "
                  "'CODAE_NAO_HOMOLOGADO'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_nao_homologado/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_homologacao_produto_codae_questiona(client_autenticado_vinculo_codae_produto,
                                                          homologacao_produto_pendente_homologacao):
    assert homologacao_produto_pendente_homologacao.status == HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/'
        f'{constants.CODAE_QUESTIONA_PEDIDO}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_QUESTIONADO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/'
        f'{constants.CODAE_QUESTIONA_PEDIDO}/')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_questiona' isn't available from state "
                  "'CODAE_QUESTIONADO'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_questionado/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_homologacao_produto_codae_pede_analise_sensorial(client_autenticado_vinculo_codae_produto,
                                                                       homologacao_produto_pendente_homologacao):
    assert homologacao_produto_pendente_homologacao.status == HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/'
        f'{constants.CODAE_PEDE_ANALISE_SENSORIAL}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/'
        f'{constants.CODAE_PEDE_ANALISE_SENSORIAL}/')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_pede_analise_sensorial' isn't available from state "
                  "'CODAE_PEDIU_ANALISE_SENSORIAL'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_pediu_analise_sensorial/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_homologacao_produto_codae_pede_analise_reclamacao(client_autenticado_vinculo_codae_produto,
                                                                        homologacao_produto_escola_ou_nutri_reclamou):
    body_content = {'justificativa': '<p>a</p>\n',
                    'anexos': [
                        {'nome': 'Captura de tela de 2020-03-11 13-23-57.png',
                         'base64': 'data:image/png;base64,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'}]}  # noqa
    assert (homologacao_produto_escola_ou_nutri_reclamou.status ==
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU)
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/'
        f'{constants.CODAE_PEDE_ANALISE_RECLAMACAO}/',
        data=json.dumps(body_content),
        content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO
    homologacao_produto_escola_ou_nutri_reclamou.refresh_from_db()
    assert homologacao_produto_escola_ou_nutri_reclamou.logs.last().anexos.exists() is True
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/'
        f'{constants.CODAE_PEDE_ANALISE_RECLAMACAO}/',
        data=json.dumps(body_content),
        content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_pediu_analise_reclamacao' isn't available from state "
                  "'CODAE_PEDIU_ANALISE_RECLAMACAO'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_pediu_analise_reclamacao/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_homologacao_produto_recusa_reclamacao(client_autenticado_vinculo_codae_produto,
                                                            homologacao_produto_escola_ou_nutri_reclamou):
    body_content = {'justificativa': '<p>a</p>\n',
                    'anexos': [
                        {'nome': 'Captura de tela de 2020-03-11 13-23-57.png',
                         'base64': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFoAAAAbCAYAAAD8rJjLAAAABHNCSVQICAgIfAhkiAAAABl0RVh0U29mdHdhcmUAZ25vbWUtc2NyZWVuc2hvdO8Dvz4AAAWASURBVGiB7ZlRaFNXGMd/pt5pr10urrFEpJlYoXVLZG0xdeiwgnUsDqqoDxXMUB8Ulg1KseKUERg+VLZ1o5UpzIpVjKIdi9PCFoYpLuIia8TE2Y5VnEFSyq3udN1t3V3jHpraVNOUwYzi8oP78p3v/u85/3u+79yQaQ8ePHhAlieO4WlP4P9C1ugMkTU6Q2SNzhBZozNE1ugMkTU6Qzx/Rkda2bmzla6Rpz2RiUxPNyguNeE+1ou9bh81CwF0Ypc9tJ4NER3QyZ1jZfVmJ1ULZAD0W35aj58n1DsEeWZK12zD+cZcJIDBLtqPnsR3I4YumSiqWM/mjWWYcqbWTYX+cysfNHVTVuemZqH0X/nxxJh8R98L4jnbjZ4c6/PTeuomlk1umpv3897rQ7R/6aVLB0Zu4z3iRV28g/2fN7N/Swmxrw7TfgdAJ9x2GF+8kvqPD9H44Xryrx/j2A9iat2U6IQvhZlllui82MWkac8QkxgtCJ7yolY4sCZtKnEjQtS8jCqrAshYVq7Aej9CJAr0hui6t4CVq4qQc0AudlD5ci/h6yqM9BC5AaUrlzF3Jkizy6hamk/PtTDaVLqpGPyRwM0iHNtXYekOEBpMnaZ1NOJq8KGOBe54cbuaCA4Dqo8GVwOe8wdx17nY/v5OGtrCiIc338Z/pIGdtS5ctXtoOBEkNvZGB3toP+im1rUdV+0eGk92ok7RqlIaLYIevHftON8qJLkoxV0BioLy8G4FRdYQQgchELKCccbYoIyiSAzdFRAfQGizUJRxNWW2An8MIKbSTYF6+Qq9iyopNVdQuShKIChS5k3JSJQeYce1r5HGdysYutCG/w6AoPN4E+dFGTs+aqTZvZmSqIfmttHq6TnXgm84UZ27qzFebcFzKf0cHjdadOL5WsW+yYHl0dYXBwzJbV0CdPR4YowUvTIOjDCak/Q0yTB2zxS6jxEjGPwTe2UJEhK2FaWIKwFiaRY5KTlFLF9ThmmmhLzQSnGeQFUBEaIjMovl66soypNAKcGx1s5fVwKj7SwHuK+i/q4hFdhx7nXjLFfSPuqRw1Cj83Qb6pLtbJsvwaPlYADifycFdEBCmp4YS9UtDaMTm2As48ZLgJ5O91FuBghEe9E+q8U/lq3JBG452DA/3VKnQkqsT4dBgYjnkz8naTTfhOl+hH4NbGtdbD7npf3AHlr0fIorHGx425RWfeJS+vy0X1WJjuzD9V0iFgc+cdG9up7alxT4RSAAE0BcILTRFoGkoGi3Ue8DMsBo6RvnKWDQUWSBeleHwtFdL+4JeNGIDEjpdCegE74Ywvh2PfXLx3eQ2tFEy8UuqueXTKwpA6Dr//6wzFNQDIKBfmBeItavos4wYpR1RJ+O5c0d7FoHuhrmzIFDHJ5lYdfqyc2e2DoKHOxtPsShLxJXswt7nonKumbc6ywoi6wU3gngiwhAJ9bRQWSGFes8wFxKyeyb+L/tQQO0X334fzNje9UEOUVYF00ncsFPbBgQYXzBfooW25AhvW4yWpjAtVxs5RYURXl4FZWXkXstQHh4YrpcYCa3L0woqqFrKp0dofGDMR1KKcte6efCN4n5DvbQfjbIC+XLsEkaodONNJ7uRNVBkhVkCfSR9K8z7Xf0YxRU4twUo/WEG1fie9extZoSCcBC9ZZqxPGD1H8/hJRnxrrWSdU8AAnb+m1UHT3J/noveo5C4ZIato3tyrS644ifOug22nDMmRjHbMUm+wh0CsqMSfFiBzVLD+JpqMUrzcX6Wj7pO+kYCnanC3HCw6e7zzBkUCgsr8G1cbRiKt/Zinq8jX11LejkYi7dgHPl3LSK07L/sGSG5+8n+DNK1ugMkTU6Q2SNzhBZozNE1ugMkTU6Q2SNzhD/AKddUd8cwpvCAAAAAElFTkSuQmCC'}]}  # noqa
    assert (homologacao_produto_escola_ou_nutri_reclamou.status ==
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU)
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/'
        f'{constants.CODAE_RECUSA_RECLAMACAO}/',
        data=json.dumps(body_content),
        content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO
    homologacao_produto_escola_ou_nutri_reclamou.refresh_from_db()
    assert homologacao_produto_escola_ou_nutri_reclamou.logs.last().anexos.exists() is True
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/'
        f'{constants.CODAE_RECUSA_RECLAMACAO}/',
        data=json.dumps(body_content),
        content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_homologa' isn't available from state "
                  "'CODAE_HOMOLOGADO'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_homologado/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_homologacao_produto_aceita_reclamacao(client_autenticado_vinculo_codae_produto,
                                                            homologacao_produto_escola_ou_nutri_reclamou):
    body_content = {'justificativa': '<p>a</p>\n',
                    'anexos': [
                        {'nome': 'Captura de tela de 2020-03-11 13-23-57.png',
                         'base64': 'data:image/png;base64,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'}]}  # noqa
    assert (homologacao_produto_escola_ou_nutri_reclamou.status ==
            HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU)
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/'
        f'{constants.CODAE_ACEITA_RECLAMACAO}/',
        data=json.dumps(body_content),
        content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_AUTORIZOU_RECLAMACAO
    homologacao_produto_escola_ou_nutri_reclamou.refresh_from_db()
    assert homologacao_produto_escola_ou_nutri_reclamou.logs.last().anexos.exists() is True
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/'
        f'{constants.CODAE_ACEITA_RECLAMACAO}/',
        data=json.dumps(body_content),
        content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_autorizou_reclamacao' isn't available from state "
                  "'CODAE_AUTORIZOU_RECLAMACAO'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_autorizou_reclamacao/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_resposta_analise_sensorial(client_autenticado_vinculo_terceirizada_homologacao):
    body_content = {
        'data': '2020-05-23',
        'homologacao_de_produto': '774ad907-d871-4bfd-b1aa-d4e0ecb6c01f',
        'hora': '20:01:54',
        'registro_funcional': '02564875',
        'responsavel_produto': 'RESPONSAVEL TESTE',
        'observacao': 'OBSERVACAO',
        'anexos': []
    }
    client, homologacao_produto, homologacao_produto_1 = client_autenticado_vinculo_terceirizada_homologacao
    assert homologacao_produto.status == HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
    response = client.post(f'/{ENDPOINT_ANALISE_SENSORIAL}/{TERCEIRIZADA_RESPONDE}/', data=json.dumps(body_content),
                           content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'homologacao_de_produto': '774ad907-d871-4bfd-b1aa-d4e0ecb6c01f', 'data': '23/05/2020',
                               'hora': '20:01:54', 'anexos': [], 'responsavel_produto': 'RESPONSAVEL TESTE',
                               'registro_funcional': '02564875', 'observacao': 'OBSERVACAO'}

    assert homologacao_produto_1.status == HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    body_content['homologacao_de_produto'] = '774ad907-d871-4bfd-b1aa-d4e0ecb6c05a'
    response = client.post(f'/{ENDPOINT_ANALISE_SENSORIAL}/{TERCEIRIZADA_RESPONDE}/', data=json.dumps(body_content),
                           content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_endpoint_produtos_listagem(client_autenticado_vinculo_terceirizada):
    client = client_autenticado_vinculo_terceirizada
    response = client.get(f'/produtos/')
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_produtos_filtro_relatorio_reclamacoes(client_autenticado_vinculo_terceirizada):
    client = client_autenticado_vinculo_terceirizada
    response = client.get(f'/produtos/filtro-reclamacoes/')
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_nome_de_produto_edital(client_autenticado_vinculo_terceirizada):
    client = client_autenticado_vinculo_terceirizada
    response = client.get(f'/nome-de-produtos-edital/')
    assert response.status_code == status.HTTP_200_OK


def test_url_produto_ja_existe(client_autenticado_vinculo_terceirizada, produto, marca1, fabricante):
    response = client_autenticado_vinculo_terceirizada.get('/produtos/ja-existe/', {
        'nome': 'Produto1',
        'marca': marca1.uuid,
        'fabricante': fabricante.uuid
    })
    assert response.json()['produto_existe']

    response = client_autenticado_vinculo_terceirizada.get('/produtos/ja-existe/', {
        'nome': 'Produto2',
        'marca': marca1.uuid,
        'fabricante': fabricante.uuid
    })

    assert response.json()['produto_existe'] is False
