import json

from faker import Faker
from freezegun import freeze_time
from model_mommy import mommy
from rest_framework import status

from ..models import CategoriaPerguntaFrequente, CentralDeDownload, Notificacao, PerguntaFrequente

fake = Faker('pt_BR')
fake.seed(420)


def test_url_cria_faq(client_autenticado_coordenador_codae):
    categoria = mommy.make(CategoriaPerguntaFrequente)

    payload = {
        'pergunta': fake.text(),
        'resposta': fake.text(),
        'categoria': categoria.uuid
    }

    client_autenticado_coordenador_codae.post(
        '/perguntas-frequentes/',
        content_type='application/json',
        data=payload
    )

    pergunta = PerguntaFrequente.objects.first()

    assert pergunta.pergunta == payload['pergunta']
    assert pergunta.resposta == payload['resposta']
    assert categoria.uuid == payload['categoria']


def test_url_atualiza_faq(client_autenticado_coordenador_codae):
    pergunta = mommy.make(PerguntaFrequente)
    categoria = mommy.make(CategoriaPerguntaFrequente)
    payload = {
        'pergunta': fake.text(),
        'resposta': fake.text(),
        'categoria': categoria.uuid
    }

    client_autenticado_coordenador_codae.patch(
        f'/perguntas-frequentes/{pergunta.uuid}/',
        content_type='application/json',
        data=payload
    )

    pergunta = PerguntaFrequente.objects.first()

    assert pergunta.pergunta == payload['pergunta']
    assert pergunta.resposta == payload['resposta']
    assert categoria.uuid == payload['categoria']


@freeze_time('2021-06-16')
def test_proximo_dia_util_suspensao_alimentacao_segunda(client_autenticado):
    from sme_terceirizadas.dados_comuns.constants import obter_dias_uteis_apos_hoje
    result = obter_dias_uteis_apos_hoje(3)
    assert str(result) == '2021-06-21'


@freeze_time('2021-06-18')
def test_proximo_dia_util_suspensao_alimentacao_sexta(client_autenticado):
    from sme_terceirizadas.dados_comuns.constants import obter_dias_uteis_apos_hoje
    result = obter_dias_uteis_apos_hoje(3)
    assert str(result) == '2021-06-23'


def test_get_notificacao_quantidade_de_nao_lidos(usuario_teste_notificacao_autenticado, notificacao_de_pendencia):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f'/notificacoes/quantidade-nao-lidos/', content_type='application/json')
    result = json.loads(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert result['quantidade_nao_lidos'] == 1


def test_get_notificacoes(usuario_teste_notificacao_autenticado, notificacao):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f'/notificacoes/', content_type='application/json')
    result = json.loads(response.content)
    esperado = {
        'next': None,
        'previous': None,
        'count': 1,
        'page_size': 5,
        'results': [
            {
                'uuid': str(notificacao.uuid),
                'titulo': notificacao.titulo,
                'descricao': notificacao.descricao,
                'criado_em': notificacao.criado_em.strftime('%d/%m/%Y'),
                'hora': notificacao.hora.strftime('%H:%M'),
                'tipo': Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao.tipo],
                'categoria': Notificacao.CATEGORIA_NOTIFICACAO_NOMES[notificacao.categoria],
                'link': notificacao.link,
                'lido': notificacao.lido,
                'resolvido': notificacao.resolvido,
            }
        ]
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_get_notificacoes_gerais(usuario_teste_notificacao_autenticado, notificacao):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f'/notificacoes/gerais/', content_type='application/json')
    result = json.loads(response.content)
    esperado = {
        'next': None,
        'previous': None,
        'count': 1,
        'page_size': 5,
        'results': [
            {
                'uuid': str(notificacao.uuid),
                'titulo': notificacao.titulo,
                'descricao': notificacao.descricao,
                'criado_em': notificacao.criado_em.strftime('%d/%m/%Y'),
                'hora': notificacao.hora.strftime('%H:%M'),
                'tipo': Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao.tipo],
                'categoria': Notificacao.CATEGORIA_NOTIFICACAO_NOMES[notificacao.categoria],
                'link': notificacao.link,
                'lido': notificacao.lido,
                'resolvido': notificacao.resolvido,
            }
        ]
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_get_pendencias_nao_resolvidas(usuario_teste_notificacao_autenticado, notificacao_de_pendencia):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f'/notificacoes/pendencias-nao-resolvidas/', content_type='application/json')
    result = json.loads(response.content)
    esperado = {
        'next': None,
        'previous': None,
        'count': 1,
        'page_size': 5,
        'results': [
            {
                'uuid': str(notificacao_de_pendencia.uuid),
                'titulo': notificacao_de_pendencia.titulo,
                'descricao': notificacao_de_pendencia.descricao,
                'criado_em': notificacao_de_pendencia.criado_em.strftime('%d/%m/%Y'),
                'hora': notificacao_de_pendencia.hora.strftime('%H:%M'),
                'tipo': Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao_de_pendencia.tipo],
                'categoria': Notificacao.CATEGORIA_NOTIFICACAO_NOMES[notificacao_de_pendencia.categoria],
                'link': notificacao_de_pendencia.link,
                'lido': notificacao_de_pendencia.lido,
                'resolvido': notificacao_de_pendencia.resolvido,
            }
        ]
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_filtro_notificacoes_lidas(usuario_teste_notificacao_autenticado, notificacao):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f'/notificacoes/?lido=true', content_type='application/json')
    result = json.loads(response.content)
    esperado = {
        'next': None,
        'previous': None,
        'count': 1,
        'page_size': 5,
        'results': [
            {
                'uuid': str(notificacao.uuid),
                'titulo': notificacao.titulo,
                'descricao': notificacao.descricao,
                'criado_em': notificacao.criado_em.strftime('%d/%m/%Y'),
                'hora': notificacao.hora.strftime('%H:%M'),
                'tipo': Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao.tipo],
                'categoria': Notificacao.CATEGORIA_NOTIFICACAO_NOMES[notificacao.categoria],
                'link': notificacao.link,
                'lido': notificacao.lido,
                'resolvido': notificacao.resolvido,
            }
        ]
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_filtro_notificacoes_por_tipo(usuario_teste_notificacao_autenticado, notificacao_de_pendencia):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f'/notificacoes/?tipo={Notificacao.TIPO_NOTIFICACAO_PENDENCIA}', content_type='application/json')
    result = json.loads(response.content)
    esperado = {
        'next': None,
        'previous': None,
        'count': 1,
        'page_size': 5,
        'results': [
            {
                'uuid': str(notificacao_de_pendencia.uuid),
                'titulo': notificacao_de_pendencia.titulo,
                'descricao': notificacao_de_pendencia.descricao,
                'criado_em': notificacao_de_pendencia.criado_em.strftime('%d/%m/%Y'),
                'hora': notificacao_de_pendencia.hora.strftime('%H:%M'),
                'tipo': Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao_de_pendencia.tipo],
                'categoria': Notificacao.CATEGORIA_NOTIFICACAO_NOMES[notificacao_de_pendencia.categoria],
                'link': notificacao_de_pendencia.link,
                'lido': notificacao_de_pendencia.lido,
                'resolvido': notificacao_de_pendencia.resolvido,
            }
        ]
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_put_notificacao_marcar_como_lida(usuario_teste_notificacao_autenticado, notificacao):
    user, client = usuario_teste_notificacao_autenticado
    payload = {
        'uuid': str(notificacao.uuid),
        'lido': True
    }

    response = client.put(
        f'/notificacoes/marcar-lido/', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == status.HTTP_200_OK


def test_get_downloads(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f'/downloads/', content_type='application/json')
    result = json.loads(response.content)
    esperado = {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [
            {
                'uuid': str(download.uuid),
                'identificador': download.identificador,
                'data_criacao': download.criado_em.strftime('%d/%m/%Y ás %H:%M'),
                'status': CentralDeDownload.STATUS_NOMES[download.status],
                'arquivo': f'http://testserver{download.arquivo.url}',
                'visto': download.visto,
                'msg_erro': download.msg_erro
            }
        ]
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_get_download_quantidade_de_nao_vistos(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        '/downloads/quantidade-nao-vistos/', content_type='application/json')
    result = json.loads(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert result['quantidade_nao_vistos'] == 1


def test_put_download_marcar_como_lida(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    payload = {
        'uuid': str(download.uuid),
        'visto': True
    }

    response = client.put(
        '/downloads/marcar-visto/', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == status.HTTP_200_OK


def test_delete_download(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    response = client.delete(
        f'/downloads/{download.uuid}/', content_type='application/json')
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_get_download_filters(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    rota = f"""/downloads/?uuid={str(download.uuid)}
           &identificador={download.identificador}
           &status={CentralDeDownload.STATUS_CONCLUIDO}
           &data_geracao={download.criado_em.strftime("%d/%m/%Y")}
           &visto={str(download.visto).lower()}'"""
    url = rota.replace('\n', '').replace(' ', '')
    response = client.get(url, content_type='application/json')
    result = json.loads(response.content)
    esperado = {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [
            {
                'uuid': str(download.uuid),
                'identificador': download.identificador,
                'data_criacao': download.criado_em.strftime('%d/%m/%Y ás %H:%M'),
                'status': CentralDeDownload.STATUS_NOMES[download.status],
                'arquivo': f'http://testserver{download.arquivo.url}',
                'visto': download.visto,
                'msg_erro': download.msg_erro
            }
        ]
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


@freeze_time('2023-09-25')
def test_get_dias_uteis(client_autenticado_da_escola, escola, dia_suspensao_atividades):
    response = client_autenticado_da_escola.get(f'/dias-uteis/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'proximos_cinco_dias_uteis': '2023-10-02',
        'proximos_dois_dias_uteis': '2023-09-28'
    }
    response = client_autenticado_da_escola.get(f'/dias-uteis/?data=25/09/2023')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'data_apos_quatro_dias_uteis': '2023-09-29'
    }

    response = client_autenticado_da_escola.get(f'/dias-uteis/?escola_uuid={escola.uuid}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'proximos_cinco_dias_uteis': '2023-10-03',
        'proximos_dois_dias_uteis': '2023-09-29'
    }
