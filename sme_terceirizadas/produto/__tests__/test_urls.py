import json

import pytest
from model_mommy import mommy
from rest_framework import status

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import HomologacaoProdutoWorkflow
from ..models import HomologacaoProduto, ProdutoEdital

pytestmark = pytest.mark.django_db

ENDPOINT_ANALISE_SENSORIAL = 'analise-sensorial'
TERCEIRIZADA_RESPONDE = 'terceirizada-responde-analise-sensorial'


def test_url_dados_dashboard_usuario_terceirizada(client_autenticado_da_terceirizada, homologacoes_produto):
    response = client_autenticado_da_terceirizada.get(
        f'/painel-gerencial-homologacoes-produtos/dashboard/'
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json['results']) == 15
    codae_hom = next((x for x in response_json['results'] if x['status'] == 'TERCEIRIZADA_RESPONDEU_RECLAMACAO'), None)
    assert len(codae_hom['dados']) == 1


def test_url_dados_dashboard_usuario_escola(client_autenticado_da_escola, homologacoes_produto):
    response = client_autenticado_da_escola.get(
        f'/painel-gerencial-homologacoes-produtos/dashboard/'
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json['results']) == 12
    codae_hom = next((x for x in response_json['results'] if x['status'] == 'TERCEIRIZADA_RESPONDEU_RECLAMACAO'), None)
    assert len(codae_hom['dados']) == 0


def test_url_dados_dashboard_usuario_nutrisupervisor(client_autenticado_vinculo_codae_nutrisupervisor,
                                                     homologacoes_produto):
    response = client_autenticado_vinculo_codae_nutrisupervisor.get(
        f'/painel-gerencial-homologacoes-produtos/dashboard/'
    )
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json['results']) == 12
    codae_hom = next((x for x in response_json['results'] if x['status'] == 'TERCEIRIZADA_RESPONDEU_RECLAMACAO'), None)
    assert len(codae_hom['dados']) == 1


def test_url_endpoint_homologacao_produto_codae_homologa(client_autenticado_vinculo_codae_produto,
                                                         homologacao_produto_pendente_homologacao,
                                                         edital):
    assert homologacao_produto_pendente_homologacao.status == HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/'
        f'{constants.CODAE_HOMOLOGA}/',
        content_type='application/json',
        data=json.dumps({'editais': [edital.uuid]}))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/'
        f'{constants.CODAE_HOMOLOGA}/',
        content_type='application/json',
        data=json.dumps({'editais': [edital.uuid]}))
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


def test_url_endpoint_homologacao_produto_rascunho(client_autenticado_vinculo_codae_produto,
                                                   homologacao_produto_rascunho,
                                                   especificacao_produto1):
    assert homologacao_produto_rascunho.status == HomologacaoProdutoWorkflow.RASCUNHO
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/rascunho/')
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
        f'{constants.CODAE_PEDE_ANALISE_SENSORIAL}/',
        content_type='application/json',
        data=json.dumps({
            'justificativa': 'É isso',
            'uuidTerceirizada': str(homologacao_produto_pendente_homologacao.rastro_terceirizada.uuid)}))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{homologacao_produto_pendente_homologacao.uuid}/'
        f'{constants.CODAE_PEDE_ANALISE_SENSORIAL}/',
        content_type='application/json',
        data=json.dumps({
            'justificativa': 'É isso',
            'uuidTerceirizada': str(homologacao_produto_pendente_homologacao.rastro_terceirizada.uuid)}))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        'detail': "Erro de transição de estado: Transition 'codae_pede_analise_sensorial' isn't available from state "
                  "'CODAE_PEDIU_ANALISE_SENSORIAL'."}
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-status/codae_pediu_analise_sensorial/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json().get('results')) == 1


def test_url_endpoint_homologacao_produto_codae_pede_analise_sensorial_reclamacao_homologado(
        client_autenticado_vinculo_codae_produto, reclamacao):
    from ...dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow

    assert reclamacao.status == ReclamacaoProdutoWorkflow.AGUARDANDO_AVALIACAO

    response = client_autenticado_vinculo_codae_produto.patch(
        f'/reclamacoes-produtos/{reclamacao.uuid}/'
        f'{constants.CODAE_PEDE_ANALISE_SENSORIAL}/',
        content_type='application/json',
        data=json.dumps({
            'justificativa': 'É isso',
            'uuidTerceirizada': str(reclamacao.homologacao_produto.rastro_terceirizada.uuid)}))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ReclamacaoProdutoWorkflow.AGUARDANDO_ANALISE_SENSORIAL


def test_url_endpoint_homologacao_produto_codae_questiona_ue_reclamacao_homologado(
        client_autenticado_vinculo_codae_produto, reclamacao):
    from ...dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow

    assert reclamacao.status == ReclamacaoProdutoWorkflow.AGUARDANDO_AVALIACAO

    response = client_autenticado_vinculo_codae_produto.patch(
        f'/reclamacoes-produtos/{reclamacao.uuid}/'
        f'{constants.CODAE_QUESTIONA_UE}/',
        content_type='application/json',
        data=json.dumps({'justificativa': 'É isso'}))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_UE


def test_url_endpoint_homologacao_produto_codae_questiona_nutrisupervisor_reclamacao_homologado(
        client_autenticado_vinculo_codae_produto, reclamacao):
    from ...dados_comuns.fluxo_status import ReclamacaoProdutoWorkflow

    assert reclamacao.status == ReclamacaoProdutoWorkflow.AGUARDANDO_AVALIACAO

    response = client_autenticado_vinculo_codae_produto.patch(
        f'/reclamacoes-produtos/{reclamacao.uuid}/'
        f'{constants.CODAE_QUESTIONA_NUTRISUPERVISOR}/',
        content_type='application/json',
        data=json.dumps({'justificativa': 'É isso'}))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['status'] == ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_NUTRISUPERVISOR


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
    client, homologacao_produto = client_autenticado_vinculo_terceirizada_homologacao
    assert homologacao_produto.status == HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_SENSORIAL
    response = client.post(f'/{ENDPOINT_ANALISE_SENSORIAL}/{TERCEIRIZADA_RESPONDE}/', data=json.dumps(body_content),
                           content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'homologacao_produto': '774ad907-d871-4bfd-b1aa-d4e0ecb6c01f',
                               'data': '23/05/2020', 'hora': '20:01:54', 'anexos': [],
                               'responsavel_produto': 'RESPONSAVEL TESTE',
                               'registro_funcional': '02564875', 'observacao': 'OBSERVACAO'}

    homologacao_produto.refresh_from_db()
    assert homologacao_produto.status == HomologacaoProdutoWorkflow.CODAE_PENDENTE_HOMOLOGACAO
    body_content['homologacao_de_produto'] = '774ad907-d871-4bfd-b1aa-d4e0ecb6c01f'
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


def test_url_endpoint_cadastro_de_produto_edital(client_autenticado_vinculo_codae_produto):
    client = client_autenticado_vinculo_codae_produto
    response = client.get(f'/cadastro-produtos-edital/')
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_produtos_logistica(client_autenticado_vinculo_codae_produto,
                                         produto_edital, produto_logistica):
    client = client_autenticado_vinculo_codae_produto
    response = client.get(f'/cadastro-produtos-edital/produtos-logistica/')
    resultado = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert resultado['count'] == 1


def test_url_endpoint_cria_produto_terceirizada(client_autenticado_vinculo_codae_produto):
    client = client_autenticado_vinculo_codae_produto
    payload = {
        'nome': 'BATATA',
        'ativo': 'Ativo'
    }
    response = client.post(f'/cadastro-produtos-edital/', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED


def test_url_endpoint_cria_produto_logistica(client_autenticado_vinculo_codae_produto):
    client = client_autenticado_vinculo_codae_produto
    payload = {
        'nome': 'ARROZ',
        'ativo': 'Ativo',
        'tipo_produto': 'LOGISTICA'
    }
    response = client.post(f'/cadastro-produtos-edital/', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED


def test_url_endpoint_cria_produto_repetido(client_autenticado_vinculo_codae_produto, produto_logistica):
    client = client_autenticado_vinculo_codae_produto
    payload = {
        'nome': 'PRODUTO TESTE',
        'ativo': 'Ativo',
        'tipo_produto': 'LOGISTICA'
    }
    response = client.post(f'/cadastro-produtos-edital/', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_url_endpoint_atualiza_produto(client_autenticado_vinculo_codae_produto, produto_logistica):
    client = client_autenticado_vinculo_codae_produto
    payload = {
        'nome': 'FEIJAO',
        'ativo': 'Ativo'
    }
    response = client.patch(f'/cadastro-produtos-edital/{produto_logistica.uuid}/', data=json.dumps(payload),
                            content_type='application/json')
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_cadastro_produto_os_steps_sem_rascunho(client_autenticado_vinculo_terceirizada,
                                                             marca1, fabricante, info_nutricional1,
                                                             unidade_medida, embalagem_produto):
    payload = {
        'uuid': None,
        'unidade_caseira': '01 copo',
        'tipo': 'algum tipo',
        'tem_aditivos_alergicos': False,
        'prazo_validade': '12 meses',
        'porcao': 'colher de sopa',
        'outras_informacoes': '',
        'numero_registro': '3',
        'nome': 'Novo Produto',
        'marca': str(marca1.uuid),
        'informacoes_nutricionais': [
            {
                'informacao_nutricional': str(info_nutricional1.uuid),
                'quantidade_porcao': '1',
                'valor_diario': '2'
            }
        ],
        'especificacoes': [
            {
                'volume': 3,
                'unidade_de_medida': str(unidade_medida.uuid),
                'embalagem_produto': str(embalagem_produto.uuid)
            }
        ],
        'imagens': [{
            'nome': 'nome.png',
            'arquivo': 'data:image/png;base64,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'  # noqa
        }],
        'fabricante': str(fabricante.uuid),
        'embalagem': '3',
        'eh_para_alunos_com_dieta': False,
        'componentes': 'DEDE',
        'cadastro_finalizado': True
    }

    client = client_autenticado_vinculo_terceirizada
    response = client.post(f'/produtos/', data=json.dumps(payload), content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED


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


def test_url_endpoint_lista_nomes_responder_reclamacao_escola(client_autenticado_vinculo_escola_ue, produto,
                                                              homologacao_produto_gpcodae_questionou_escola,
                                                              reclamacao_ue):

    client = client_autenticado_vinculo_escola_ue
    response = client.get(f'/produtos/lista-nomes-responder-reclamacao-escola/')
    esperado = {'results': [{'uuid': 'uuid', 'nome': produto.nome}]}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_lista_nomes_responder_reclamacao_nutri(client_autenticado_vinculo_escola_nutrisupervisor,
                                                             produto,
                                                             homologacao_produto_gpcodae_questionou_nutrisupervisor,
                                                             reclamacao_nutrisupervisor):

    client = client_autenticado_vinculo_escola_nutrisupervisor
    response = client.get(f'/produtos/lista-nomes-responder-reclamacao-nutrisupervisor/')
    esperado = {'results': [{'uuid': 'uuid', 'nome': produto.nome}]}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_lista_nomes_responder_reclamacao_fabricantes(client_autenticado_vinculo_escola_ue,
                                                                   produto, fabricante,
                                                                   homologacao_produto_gpcodae_questionou_escola,
                                                                   reclamacao_ue):

    client = client_autenticado_vinculo_escola_ue
    response = client.get(f'/fabricantes/lista-nomes-responder-reclamacao-escola/')
    esperado = {'results': [{'uuid': str(fabricante.uuid), 'nome': fabricante.nome}]}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_lista_nomes_responder_reclamacao_fabricantes_nutri(
        client_autenticado_vinculo_escola_nutrisupervisor,
        fabricante,
        homologacao_produto_gpcodae_questionou_nutrisupervisor,
        reclamacao_nutrisupervisor):

    client = client_autenticado_vinculo_escola_nutrisupervisor
    response = client.get(f'/fabricantes/lista-nomes-responder-reclamacao-nutrisupervisor/')
    esperado = {'results': [{'uuid': str(fabricante.uuid), 'nome': fabricante.nome}]}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_lista_nomes_responder_reclamacao_marcas(client_autenticado_vinculo_escola_ue,
                                                              produto, marca1,
                                                              homologacao_produto_gpcodae_questionou_escola,
                                                              reclamacao_ue):

    client = client_autenticado_vinculo_escola_ue
    response = client.get(f'/marcas/lista-nomes-responder-reclamacao-escola/')
    esperado = {'results': [{'uuid': str(marca1.uuid), 'nome': marca1.nome}]}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_lista_nomes_responder_reclamacao_marcas_nutri(
        client_autenticado_vinculo_escola_nutrisupervisor,
        marca1,
        homologacao_produto_gpcodae_questionou_nutrisupervisor,
        reclamacao_nutrisupervisor):

    client = client_autenticado_vinculo_escola_nutrisupervisor
    response = client.get(f'/marcas/lista-nomes-responder-reclamacao-nutrisupervisor/')
    esperado = {'results': [{'uuid': str(marca1.uuid), 'nome': marca1.nome}]}

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_lista_itens_cadastros(client_autenticado_vinculo_escola_ue,
                                            item_cadastrado_1,
                                            item_cadastrado_2,
                                            item_cadastrado_3,
                                            item_cadastrado_4):

    client = client_autenticado_vinculo_escola_ue
    response = client.get(f'/itens-cadastros/')
    esperado = {
        'count': 4,
        'next': None,
        'previous': None,
        'results': [
            {
                'uuid': str(item_cadastrado_4.uuid),
                'nome': item_cadastrado_4.content_object.nome,
                'tipo': item_cadastrado_4.tipo,
                'tipo_display': item_cadastrado_4.get_tipo_display()
            },
            {
                'uuid': str(item_cadastrado_3.uuid),
                'nome': item_cadastrado_3.content_object.nome,
                'tipo': item_cadastrado_3.tipo,
                'tipo_display': item_cadastrado_3.get_tipo_display()
            },
            {
                'uuid': str(item_cadastrado_2.uuid),
                'nome': item_cadastrado_2.content_object.nome,
                'tipo': item_cadastrado_2.tipo,
                'tipo_display': item_cadastrado_2.get_tipo_display()
            },
            {
                'uuid': str(item_cadastrado_1.uuid),
                'nome': item_cadastrado_1.content_object.nome,
                'tipo': item_cadastrado_1.tipo,
                'tipo_display': item_cadastrado_1.get_tipo_display()
            }]
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_detalhe_item_cadastro(client_autenticado_vinculo_escola_ue,
                                            item_cadastrado_1):

    client = client_autenticado_vinculo_escola_ue
    response = client.get(f'/itens-cadastros/{str(item_cadastrado_1.uuid)}/')
    esperado = {
        'uuid': str(item_cadastrado_1.uuid),
        'nome': item_cadastrado_1.content_object.nome,
        'tipo': item_cadastrado_1.tipo,
        'tipo_display': item_cadastrado_1.get_tipo_display()
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_criar_item_cadastro_e_marca(client_autenticado_vinculo_escola_ue):
    from sme_terceirizadas.produto.models import ItemCadastro

    assert ItemCadastro.objects.count() == 0
    client = client_autenticado_vinculo_escola_ue
    payload = {
        'nome': 'Flamengo',
        'tipo': 'MARCA'
    }
    response = client.post(f'/itens-cadastros/', data=json.dumps(payload), content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED
    assert ItemCadastro.objects.count() == 1


def test_url_endpoint_criar_item_cadastro_e_fabricante(client_autenticado_vinculo_escola_ue):
    from sme_terceirizadas.produto.models import ItemCadastro

    assert ItemCadastro.objects.count() == 0
    client = client_autenticado_vinculo_escola_ue
    payload = {
        'nome': 'Anjo',
        'tipo': 'FABRICANTE'
    }
    response = client.post(f'/itens-cadastros/', data=json.dumps(payload), content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED
    assert ItemCadastro.objects.count() == 1


def test_url_endpoint_criar_item_cadastro_e_unidade_medida(client_autenticado_vinculo_escola_ue):
    from sme_terceirizadas.produto.models import ItemCadastro

    assert ItemCadastro.objects.count() == 0
    client = client_autenticado_vinculo_escola_ue
    payload = {
        'nome': 'Kg',
        'tipo': 'UNIDADE_MEDIDA'
    }
    response = client.post(f'/itens-cadastros/', data=json.dumps(payload), content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED
    assert ItemCadastro.objects.count() == 1


def test_url_endpoint_criar_item_cadastro_e_embalagem_produto(client_autenticado_vinculo_escola_ue):
    from sme_terceirizadas.produto.models import ItemCadastro

    assert ItemCadastro.objects.count() == 0
    client = client_autenticado_vinculo_escola_ue
    payload = {
        'nome': 'Bolsa',
        'tipo': 'EMBALAGEM'
    }
    response = client.post(f'/itens-cadastros/', data=json.dumps(payload), content_type='application/json')

    assert response.status_code == status.HTTP_201_CREATED
    assert ItemCadastro.objects.count() == 1


def test_url_endpoint_tipos_item_cadastro(client_autenticado_vinculo_escola_ue):

    client = client_autenticado_vinculo_escola_ue
    response = client.get(f'/itens-cadastros/tipos/')
    esperado = [
        {
            'tipo': 'MARCA',
            'tipo_display': 'Marca'
        },
        {
            'tipo': 'FABRICANTE',
            'tipo_display': 'Fabricante'
        },
        {
            'tipo': 'UNIDADE_MEDIDA',
            'tipo_display': 'Unidade de Medida'
        },
        {
            'tipo': 'EMBALAGEM',
            'tipo_display': 'Embalagem'
        }
    ]

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == esperado


def test_url_endpoint_lista_de_nomes_de_itens_cadastros(client_autenticado_vinculo_escola_ue,
                                                        item_cadastrado_1,
                                                        item_cadastrado_2,
                                                        item_cadastrado_3,
                                                        item_cadastrado_4):

    client = client_autenticado_vinculo_escola_ue
    response = client.get('/itens-cadastros/lista-nomes/')
    resultado = response.json()

    esperado = {
        'results': [
            item_cadastrado_4.content_object.nome,
            item_cadastrado_3.content_object.nome,
            item_cadastrado_2.content_object.nome,
            item_cadastrado_1.content_object.nome
        ]
    }

    assert resultado == esperado


def test_url_endpoint_lista_unidades_de_medida_sem_paginacao(client_autenticado_vinculo_escola_ue,
                                                             unidade_medida):

    client = client_autenticado_vinculo_escola_ue
    response = client.get('/unidades-medida/')
    resultado = response.json()

    esperado = {
        'results': [
            {
                'uuid': str(unidade_medida.uuid),
                'nome': unidade_medida.nome
            }
        ]
    }

    assert resultado == esperado


def test_url_endpoint_lista_embalagens_produto_sem_paginacao(client_autenticado_vinculo_escola_ue,
                                                             embalagem_produto):

    client = client_autenticado_vinculo_escola_ue
    response = client.get('/embalagens-produto/')
    resultado = response.json()

    esperado = {
        'results': [
            {
                'uuid': str(embalagem_produto.uuid),
                'nome': embalagem_produto.nome
            }
        ]
    }

    assert resultado == esperado


def test_url_endpoint_produtos_editais_filtros(client_autenticado_vinculo_codae_produto,
                                               vinculo_produto_edital):
    client = client_autenticado_vinculo_codae_produto
    response = client.get('/produtos-editais/filtros/')
    resultado = response.json()

    esperado = {
        'produtos': [
            {
                'produto__nome': 'Produto1',
                'produto__uuid': 'a37bcf3f-a288-44ae-87ae-dbec181a34d4'
            }
        ],
        'editais': [
            {
                'numero': 'Edital de Pregão nº 56/SME/2016',
                'uuid': '617a8139-02a9-4801-a197-622aa20795b9'
            }
        ]
    }
    assert resultado == esperado


def test_url_endpoint_produtos_editais_filtrar(client_autenticado_vinculo_codae_produto,
                                               vinculo_produto_edital):
    client = client_autenticado_vinculo_codae_produto
    payload = {'page': '1', 'page_size': '10', 'nome': 'Produto1'}
    response = client.get('/produtos-editais/filtrar/', payload)
    resultado = response.json()

    assert resultado['count'] == 1
    assert resultado['page_size'] == 10
    assert resultado['results'][0]['produto']['nome'] == 'Produto1'
    assert resultado['results'][0]['ativo'] is True


def test_url_endpoint_produtos_editais_ativar_inativar(client_autenticado_vinculo_codae_produto,
                                                       vinculo_produto_edital):
    client = client_autenticado_vinculo_codae_produto
    response = client.patch(f'/produtos-editais/{vinculo_produto_edital.uuid}/ativar-inativar-produto/')
    resultado = response.json()
    assert resultado['data']['ativo'] is False

    response = client.patch(f'/produtos-editais/{vinculo_produto_edital.uuid}/ativar-inativar-produto/')
    resultado = response.json()
    assert resultado['data']['ativo'] is True


def test_url_endpoint_produtos_editais_lista_editais_dre(client_autenticado_da_dre, contrato, diretoria_regional):
    client = client_autenticado_da_dre
    response = client.get(f'/produtos-editais/lista-editais-dre/')
    assert response.status_code == status.HTTP_200_OK
    resultado = response.json()
    esperado = {'results': [
        {'uuid': '617a8139-02a9-4801-a197-622aa20795b9',
         'numero': 'Edital de Pregão nº 56/SME/2016'}
    ]}
    assert resultado == esperado


def test_url_endpoint_produtos_editais_filtro_por_parametros_agrupado_terceirizada(client_autenticado_da_dre):
    client = client_autenticado_da_dre
    params = {
        'agrupado_por_nome_e_marca': False,
        'data_homologacao': '14/10/2022',
        'nome_edital': 'Edital de Pregão nº 41/sme/2017',
        'nome_marca': 'IAGRO',
        'nome_produto': 'ARROZ LONGO FINO TIPO 1',
        'nome_terceirizada': 'APETECE'
    }
    response = client.get(f'/painel-gerencial-homologacoes-produtos/filtro-por-parametros-agrupado-terceirizada/',
                          content_type='application/json', **params)
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_produtos_agrupados_marca_produto(client_autenticado_vinculo_codae_produto, produtos_edital_41):
    response = client_autenticado_vinculo_codae_produto.get(
        f'/painel-gerencial-homologacoes-produtos/filtro-por-parametros-agrupado-terceirizada/'
        f'?agrupado_por_nome_e_marca=true&nome_edital=Edital de Pregão nº 41/sme/2017',
        content_type='application/json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'results': [
        {'nome': 'ARROZ', 'marca': 'NAMORADOS | TIO JOÃO', 'edital': 'Edital de Pregão nº 41/sme/2017'}],
        'count': 2,
        'total_marcas': 2}


def test_url_endpoint_homologacao_produto_actions(client_autenticado_vinculo_codae_produto,
                                                  homologacao_produto_escola_ou_nutri_reclamou):

    client = client_autenticado_vinculo_codae_produto

    response = client.get(f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/reclamacao/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/homologacoes-produtos/numero_protocolo/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/homologacoes-produtos/{homologacao_produto_escola_ou_nutri_reclamou.uuid}/'
                          f'gerar-pdf-ficha-identificacao-produto/')
    assert response.status_code == status.HTTP_200_OK


def test_url_endpoint_produto_actions(client_autenticado_vinculo_codae_produto, produto, terceirizada):
    hom = mommy.make('HomologacaoProduto',
                     produto=produto,
                     rastro_terceirizada=terceirizada,
                     status=HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO)
    mommy.make('LogSolicitacoesUsuario', uuid_original=hom.uuid)

    client = client_autenticado_vinculo_codae_produto

    response = client.get(f'/produtos/lista-nomes/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/lista-nomes-unicos/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/lista-nomes-avaliar-reclamacao/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/lista-substitutos/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/todos-produtos/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/{produto.uuid}/relatorio/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/{produto.uuid}/relatorio-analise-sensorial/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/{produto.uuid}/relatorio-analise-sensorial-recebimento/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/filtro-relatorio-situacao-produto/')
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f'/produtos/relatorio-situacao-produto/')
    assert response.status_code == status.HTTP_200_OK


def test_create_produtos_vinculos(client_autenticado_vinculo_codae_produto, produtos_edital_41):
    data = {
        'edital_origem': '12288b47-9d27-4089-8c2e-48a6061d83ea',
        'tipo_produto_edital_origem': 'Comum',
        'tipo_produto': 'Comum',
        'editais_destino_selecionados': [
            'b30a2102-2ae0-404d-8a56-8e5ecd73f868'
        ],
        'outras_informacoes': 'outras informações',
        'produtos_editais': [
            '0f81a49b-0836-42d5-af9e-12cbd7ca76a8'
        ]
    }
    response = client_autenticado_vinculo_codae_produto.post(f'/produtos-editais/', data=json.dumps(data),
                                                             content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    produto = ProdutoEdital.objects.get(uuid='0f81a49b-0836-42d5-af9e-12cbd7ca76a8').produto
    assert produto.vinculos.count() == 3
    assert produto.vinculos.filter(edital__numero='Edital de Pregão nº 78/sme/2016').exists()
    log = produto.homologacao.logs.last()
    assert log.justificativa == (
        '<p>Nome do Produto:</p>'
        '<p>ARROZ</p><br>'
        '<p>Editais que foram vinculados:</p>'
        '<p>Edital de Pregão nº 78/sme/2016</p><br>'
        '<p>Tipo de Produto em que o produto foi vinculado:</p>'
        '<p>Comum</p><br>'
        '<p>Outras informações:</p>'
        '<p>outras informações</p>')


def test_create_produtos_altera_vinculos_tipo_produto(client_autenticado_vinculo_codae_produto, produtos_edital_41):
    data = {
        'edital_origem': '12288b47-9d27-4089-8c2e-48a6061d83ea',
        'tipo_produto_edital_origem': 'Comum',
        'tipo_produto': 'Dieta especial',
        'editais_destino_selecionados': [
            '131f4000-3e31-44f1-9ba5-e7df001a8426'
        ],
        'outras_informacoes': 'outras informações',
        'produtos_editais': [
            '0f81a49b-0836-42d5-af9e-12cbd7ca76a8'
        ]
    }
    response = client_autenticado_vinculo_codae_produto.post(f'/produtos-editais/', data=json.dumps(data),
                                                             content_type='application/json')
    assert response.status_code == status.HTTP_201_CREATED
    produto = ProdutoEdital.objects.get(uuid='0f81a49b-0836-42d5-af9e-12cbd7ca76a8').produto
    assert produto.vinculos.count() == 2
    assert produto.vinculos.filter(
        edital__numero='Edital de Pregão nº 78/sme/2022', tipo_produto='Dieta especial').exists()
    log = produto.homologacao.logs.last()
    assert log.justificativa == (
        '<p>Nome do Produto:</p>'
        '<p>ARROZ</p><br>'
        '<p>Editais que foram vinculados:</p>'
        '<p>Edital de Pregão nº 78/sme/2022</p><br>'
        '<p>Tipo de Produto alterado para:</p>'
        '<p>Dieta especial</p><br>'
        '<p>Outras informações:</p>'
        '<p>outras informações</p>')


def test_produto_viewset_list(client_autenticado_vinculo_codae_produto, produtos_edital_41):
    response = client_autenticado_vinculo_codae_produto.get(
        f'/produtos/?nome_edital=Edital de Pregão nº 41/sme/2017'
        f'&tipo_produto_comum=true'
        f'&eh_para_alunos_com_dieta=false'
        f'&page=1'
        f'&page_size=10')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['count'] == 2
    assert response.json()['results'][0]['produto_edital_tipo_produto'] == 'Comum'


def test_alteracao_dados_produto_homologado(client_autenticado_vinculo_terceirizada, homologacao_produto, marca1,
                                            fabricante, produto, unidade_medida, embalagem_produto, info_nutricional1,
                                            info_nutricional2):
    data = {
        'eh_para_alunos_com_dieta': True,
        'tem_aditivos_alergenicos': True,
        'tem_gluten': '0',
        'aditivos': 'dasdasdasd',
        'nome': produto.nome,
        'marca': str(marca1.uuid),
        'fabricante': str(fabricante.uuid),
        'componentes': 'componente teste',
        'porcao': '1 kg',
        'unidade_caseira': '1 PRATO CHEIO',
        'especificacoes': [
            {
                'volume': 500,
                'unidade_de_medida': str(unidade_medida.uuid),
                'embalagem_produto': str(embalagem_produto.uuid)
            }
        ],
        'prazo_validade': '24 MESES',
        'info_armazenamento': 'O PRODUTO DEVE SER CONSERVADO EM AMABIENTE SECO E FRESCO',
        'anexos': [],
        'uuid': str(produto.uuid),
        'cadastro_atualizado': True,
        'cadastro_finalizado': False,
        'imagens': [],
        'informacoes_nutricionais': [
            {
                'informacao_nutricional': str(info_nutricional1.uuid),
                'quantidade_porcao': '324',
                'valor_diario': '16'
            },
            {
                'informacao_nutricional': str(info_nutricional2.uuid),
                'quantidade_porcao': '69',
                'valor_diario': '23'
            },
        ],
        'outras_informacoes': 'daadsads'
    }
    response = client_autenticado_vinculo_terceirizada.patch(
        f'/homologacoes-produtos/{homologacao_produto.uuid}/alteracao-produto-homologado/',
        content_type='application/json',
        data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['uuid'] != produto.uuid

    uuid_ = response.json()['uuid']
    produto.refresh_from_db()

    response = client_autenticado_vinculo_terceirizada.get(f'/produtos/{uuid_}/')

    assert response.json()['porcao'] == '1 kg'
    assert produto.porcao == '5 cuias'


def test_suspensao_parcial_produto_com_copia(client_autenticado_vinculo_codae_produto, hom_copia):
    original = hom_copia.get_original()
    data = {
        'funcionario_registro_funcional': '3462334',
        'funcionario_nome': 'GPCODAE',
        'funcionario_cargo': '',
        'editais_para_suspensao_ativacao': [
            '0f81a49b-0836-42d5-af9e-12cbd7ca76a8',
            'e42e3b97-6853-4327-841d-34292c33963c'
        ],
        'justificativa': '<p>suspender parcial</p>'
    }
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{hom_copia.uuid}/suspender/',
        content_type='application/json',
        data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['uuid'] == str(original.uuid)
    assert HomologacaoProduto.objects.filter(uuid=hom_copia.uuid).exists() is False


def test_suspensao_total_produto_com_copia(client_autenticado_vinculo_codae_produto, hom_copia_pendente_homologacao):
    original = hom_copia_pendente_homologacao.get_original()
    assert hom_copia_pendente_homologacao.tem_copia is False
    assert original.get_original() == 'Não é cópia.'
    assert original.equaliza_homologacoes_e_se_destroi() == 'Não é cópia.'
    data = {
        'funcionario_registro_funcional': '3462334',
        'funcionario_nome': 'GPCODAE',
        'funcionario_cargo': '',
        'editais_para_suspensao_ativacao': [
            '0f81a49b-0836-42d5-af9e-12cbd7ca76a8',
            'e42e3b97-6853-4327-841d-34292c33963c',
            '3b4f59eb-a686-49e9-beab-3514a93e3184',
        ],
        'justificativa': '<p>suspender total</p>'
    }
    response = client_autenticado_vinculo_codae_produto.patch(
        f'/homologacoes-produtos/{hom_copia_pendente_homologacao.uuid}/suspender/',
        content_type='application/json',
        data=json.dumps(data)
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['uuid'] == str(original.uuid)
    assert HomologacaoProduto.objects.filter(uuid=hom_copia_pendente_homologacao.uuid).exists() is False
