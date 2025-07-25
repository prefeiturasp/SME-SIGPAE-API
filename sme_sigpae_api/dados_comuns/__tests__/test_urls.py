import datetime
import json

from faker import Faker
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status

from ...escola.models import TipoUnidadeEscolar
from ..models import (
    CategoriaPerguntaFrequente,
    CentralDeDownload,
    Notificacao,
    PerguntaFrequente,
)

fake = Faker("pt_BR")
Faker.seed(420)


def test_url_cria_faq(client_autenticado_coordenador_codae):
    categoria = baker.make(CategoriaPerguntaFrequente)

    payload = {
        "pergunta": fake.text(),
        "resposta": fake.text(),
        "categoria": categoria.uuid,
    }

    client_autenticado_coordenador_codae.post(
        "/perguntas-frequentes/", content_type="application/json", data=payload
    )

    pergunta = PerguntaFrequente.objects.first()

    assert pergunta.pergunta == payload["pergunta"]
    assert pergunta.resposta == payload["resposta"]
    assert categoria.uuid == payload["categoria"]


def test_url_atualiza_faq(client_autenticado_coordenador_codae):
    pergunta = baker.make(PerguntaFrequente)
    categoria = baker.make(CategoriaPerguntaFrequente)
    payload = {
        "pergunta": fake.text(),
        "resposta": fake.text(),
        "categoria": categoria.uuid,
    }

    client_autenticado_coordenador_codae.patch(
        f"/perguntas-frequentes/{pergunta.uuid}/",
        content_type="application/json",
        data=payload,
    )

    pergunta = PerguntaFrequente.objects.first()

    assert pergunta.pergunta == payload["pergunta"]
    assert pergunta.resposta == payload["resposta"]
    assert categoria.uuid == payload["categoria"]


@freeze_time("2021-06-16")
def test_proximo_dia_util_suspensao_alimentacao_segunda(client_autenticado):
    from sme_sigpae_api.dados_comuns.constants import obter_dias_uteis_apos_hoje

    result = obter_dias_uteis_apos_hoje(3)
    assert str(result) == "2021-06-21"


@freeze_time("2021-06-18")
def test_proximo_dia_util_suspensao_alimentacao_sexta(client_autenticado):
    from sme_sigpae_api.dados_comuns.constants import obter_dias_uteis_apos_hoje

    result = obter_dias_uteis_apos_hoje(3)
    assert str(result) == "2021-06-23"


def test_get_notificacao_quantidade_de_nao_lidos(
    usuario_teste_notificacao_autenticado, notificacao_de_pendencia
):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        "/notificacoes/quantidade-nao-lidos/", content_type="application/json"
    )
    result = json.loads(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert result["quantidade_nao_lidos"] == 1


def test_get_notificacoes(usuario_teste_notificacao_autenticado, notificacao):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get("/notificacoes/", content_type="application/json")
    result = json.loads(response.content)
    esperado = {
        "next": None,
        "previous": None,
        "count": 1,
        "page_size": 5,
        "results": [
            {
                "uuid": str(notificacao.uuid),
                "titulo": notificacao.titulo,
                "descricao": notificacao.descricao,
                "criado_em": notificacao.criado_em.strftime("%d/%m/%Y"),
                "hora": notificacao.hora.strftime("%H:%M"),
                "tipo": Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao.tipo],
                "categoria": Notificacao.CATEGORIA_NOTIFICACAO_NOMES[
                    notificacao.categoria
                ],
                "link": notificacao.link,
                "lido": notificacao.lido,
                "resolvido": notificacao.resolvido,
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_get_notificacoes_gerais(usuario_teste_notificacao_autenticado, notificacao):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get("/notificacoes/gerais/", content_type="application/json")
    result = json.loads(response.content)
    esperado = {
        "next": None,
        "previous": None,
        "count": 1,
        "page_size": 5,
        "results": [
            {
                "uuid": str(notificacao.uuid),
                "titulo": notificacao.titulo,
                "descricao": notificacao.descricao,
                "criado_em": notificacao.criado_em.strftime("%d/%m/%Y"),
                "hora": notificacao.hora.strftime("%H:%M"),
                "tipo": Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao.tipo],
                "categoria": Notificacao.CATEGORIA_NOTIFICACAO_NOMES[
                    notificacao.categoria
                ],
                "link": notificacao.link,
                "lido": notificacao.lido,
                "resolvido": notificacao.resolvido,
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_get_pendencias_nao_resolvidas(
    usuario_teste_notificacao_autenticado, notificacao_de_pendencia
):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        "/notificacoes/pendencias-nao-resolvidas/", content_type="application/json"
    )
    result = json.loads(response.content)
    esperado = {
        "next": None,
        "previous": None,
        "count": 1,
        "page_size": 5,
        "results": [
            {
                "uuid": str(notificacao_de_pendencia.uuid),
                "titulo": notificacao_de_pendencia.titulo,
                "descricao": notificacao_de_pendencia.descricao,
                "criado_em": notificacao_de_pendencia.criado_em.strftime("%d/%m/%Y"),
                "hora": notificacao_de_pendencia.hora.strftime("%H:%M"),
                "tipo": Notificacao.TIPO_NOTIFICACAO_NOMES[
                    notificacao_de_pendencia.tipo
                ],
                "categoria": Notificacao.CATEGORIA_NOTIFICACAO_NOMES[
                    notificacao_de_pendencia.categoria
                ],
                "link": notificacao_de_pendencia.link,
                "lido": notificacao_de_pendencia.lido,
                "resolvido": notificacao_de_pendencia.resolvido,
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_filtro_notificacoes_lidas(usuario_teste_notificacao_autenticado, notificacao):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get("/notificacoes/?lido=true", content_type="application/json")
    result = json.loads(response.content)
    esperado = {
        "next": None,
        "previous": None,
        "count": 1,
        "page_size": 5,
        "results": [
            {
                "uuid": str(notificacao.uuid),
                "titulo": notificacao.titulo,
                "descricao": notificacao.descricao,
                "criado_em": notificacao.criado_em.strftime("%d/%m/%Y"),
                "hora": notificacao.hora.strftime("%H:%M"),
                "tipo": Notificacao.TIPO_NOTIFICACAO_NOMES[notificacao.tipo],
                "categoria": Notificacao.CATEGORIA_NOTIFICACAO_NOMES[
                    notificacao.categoria
                ],
                "link": notificacao.link,
                "lido": notificacao.lido,
                "resolvido": notificacao.resolvido,
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_filtro_notificacoes_por_tipo(
    usuario_teste_notificacao_autenticado, notificacao_de_pendencia
):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        f"/notificacoes/?tipo={Notificacao.TIPO_NOTIFICACAO_PENDENCIA}",
        content_type="application/json",
    )
    result = json.loads(response.content)
    esperado = {
        "next": None,
        "previous": None,
        "count": 1,
        "page_size": 5,
        "results": [
            {
                "uuid": str(notificacao_de_pendencia.uuid),
                "titulo": notificacao_de_pendencia.titulo,
                "descricao": notificacao_de_pendencia.descricao,
                "criado_em": notificacao_de_pendencia.criado_em.strftime("%d/%m/%Y"),
                "hora": notificacao_de_pendencia.hora.strftime("%H:%M"),
                "tipo": Notificacao.TIPO_NOTIFICACAO_NOMES[
                    notificacao_de_pendencia.tipo
                ],
                "categoria": Notificacao.CATEGORIA_NOTIFICACAO_NOMES[
                    notificacao_de_pendencia.categoria
                ],
                "link": notificacao_de_pendencia.link,
                "lido": notificacao_de_pendencia.lido,
                "resolvido": notificacao_de_pendencia.resolvido,
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_put_notificacao_marcar_como_lida(
    usuario_teste_notificacao_autenticado, notificacao
):
    user, client = usuario_teste_notificacao_autenticado
    payload = {"uuid": str(notificacao.uuid), "lido": True}

    response = client.put(
        "/notificacoes/marcar-lido/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_downloads(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get("/downloads/", content_type="application/json")
    result = json.loads(response.content)
    esperado = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "uuid": str(download.uuid),
                "identificador": download.identificador,
                "data_criacao": download.criado_em.strftime("%d/%m/%Y ás %H:%M"),
                "status": CentralDeDownload.STATUS_NOMES[download.status],
                "arquivo": f"http://testserver{download.arquivo.url}",
                "visto": download.visto,
                "msg_erro": download.msg_erro,
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


def test_get_download_quantidade_de_nao_vistos(
    usuario_teste_notificacao_autenticado, download
):
    user, client = usuario_teste_notificacao_autenticado
    response = client.get(
        "/downloads/quantidade-nao-vistos/", content_type="application/json"
    )
    result = json.loads(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert result["quantidade_nao_vistos"] == 1


def test_put_download_marcar_como_lida(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    payload = {"uuid": str(download.uuid), "visto": True}

    response = client.put(
        "/downloads/marcar-visto/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_delete_download(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    response = client.delete(
        f"/downloads/{download.uuid}/", content_type="application/json"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_get_download_filters(usuario_teste_notificacao_autenticado, download):
    user, client = usuario_teste_notificacao_autenticado
    rota = f"""/downloads/?uuid={str(download.uuid)}
           &identificador={download.identificador}
           &status={CentralDeDownload.STATUS_CONCLUIDO}
           &data_geracao={download.criado_em.strftime("%d/%m/%Y")}
           &visto={str(download.visto).lower()}'"""
    url = rota.replace("\n", "").replace(" ", "")
    response = client.get(url, content_type="application/json")
    result = json.loads(response.content)
    esperado = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "uuid": str(download.uuid),
                "identificador": download.identificador,
                "data_criacao": download.criado_em.strftime("%d/%m/%Y ás %H:%M"),
                "status": CentralDeDownload.STATUS_NOMES[download.status],
                "arquivo": f"http://testserver{download.arquivo.url}",
                "visto": download.visto,
                "msg_erro": download.msg_erro,
            }
        ],
    }
    assert response.status_code == status.HTTP_200_OK
    assert result == esperado


@freeze_time("2023-09-25")
def test_get_dias_uteis_escola(
    client_autenticado_da_escola, escola, dia_suspensao_atividades
):
    response = client_autenticado_da_escola.get("/dias-uteis/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "proximos_cinco_dias_uteis": "2023-10-02",
        "proximos_dois_dias_uteis": "2023-09-28",
    }
    response = client_autenticado_da_escola.get("/dias-uteis/?data=25/09/2023")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"data_apos_quatro_dias_uteis": "2023-09-29"}

    response = client_autenticado_da_escola.get(
        f"/dias-uteis/?escola_uuid={escola.uuid}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "proximos_cinco_dias_uteis": "2023-10-03",
        "proximos_dois_dias_uteis": "2023-09-29",
    }


@freeze_time("2023-09-25")
def test_get_dias_uteis_dre(
    client_autenticado_da_dre, escola, dia_suspensao_atividades
):
    response = client_autenticado_da_dre.get(
        "/dias-uteis/?eh_solicitacao_unificada=true"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "proximos_cinco_dias_uteis": "2023-10-03",
        "proximos_dois_dias_uteis": "2023-09-29",
    }


def test_get_feriados_ano_atual(client_autenticado):
    client = client_autenticado
    ano_atual = str(datetime.datetime.now().year)
    response = client.get("/feriados-ano/", content_type="application/json")
    data = json.loads(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert ano_atual in data["results"][0]


def test_get_feriados_ano_atual_e_proximo_ano(client_autenticado):
    client = client_autenticado
    ano_atual = datetime.datetime.now().year
    ano_proximo = ano_atual + 1
    response = client.get(
        "/feriados-ano/ano-atual-e-proximo/", content_type="application/json"
    )
    data = json.loads(response.content)
    assert response.status_code == status.HTTP_200_OK
    assert str(ano_atual) in data["results"][0]
    assert str(ano_proximo) in data["results"][-1]


@freeze_time("2025-04-18")
def test_validacao_duplicidade_lanche_emergencial(
    client_autenticado_vinculo_escola_cemei,
    alteracao_cemei,
    periodo_manha,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche_emergencial,
):
    client, user = client_autenticado_vinculo_escola_cemei
    payload = {
        "escola": alteracao_cemei.escola.uuid,
        "motivo": alteracao_cemei.motivo.uuid,
        "alunos_cei_e_ou_emei": "EMEI",
        "alterar_dia": "28/04/2025",
        "substituicoes_cemei_cei_periodo_escolar": [],
        "substituicoes_cemei_emei_periodo_escolar": [
            {
                "qtd_alunos": "45",
                "matriculados_quando_criado": 261,
                "periodo_escolar": periodo_manha.uuid,
                "tipos_alimentacao_de": [tipo_alimentacao_refeicao.uuid],
                "tipos_alimentacao_para": [tipo_alimentacao_lanche_emergencial.uuid],
            }
        ],
        "datas_intervalo": [{"data": "2025-04-28"}],
    }
    response = client.post(
        "/alteracoes-cardapio-cemei/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == [
        "Já existe uma solicitação de Lanche Emergencial para a mesma data e período selecionado!"
    ]


@freeze_time("2025-04-18")
def test_validacao_duplicidade_lanche_emergencial_2(
    client_autenticado_vinculo_escola_cemei,
    alteracao_cemei,
    periodo_manha,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche_emergencial,
    tipo_alimentacao_lanche,
):
    client, user = client_autenticado_vinculo_escola_cemei
    payload = {
        "escola": alteracao_cemei.escola.uuid,
        "motivo": alteracao_cemei.motivo.uuid,
        "alunos_cei_e_ou_emei": "EMEI",
        "alterar_dia": "28/04/2025",
        "substituicoes_cemei_cei_periodo_escolar": [],
        "substituicoes_cemei_emei_periodo_escolar": [
            {
                "qtd_alunos": "45",
                "matriculados_quando_criado": 261,
                "periodo_escolar": periodo_manha.uuid,
                "tipos_alimentacao_de": [
                    tipo_alimentacao_refeicao.uuid,
                    tipo_alimentacao_lanche.uuid,
                ],
                "tipos_alimentacao_para": [tipo_alimentacao_lanche_emergencial.uuid],
            }
        ],
        "datas_intervalo": [
            {"data": "2025-04-27"},
            {"data": "2025-04-28"},
            {"data": "2025-04-29"},
        ],
    }
    response = client.post(
        "/alteracoes-cardapio-cemei/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == [
        "Já existe uma solicitação de Lanche Emergencial para a mesma data e período selecionado!"
    ]


@freeze_time("2025-04-18")
def test_validacao_duplicidade_lanche_emergencial_caso_valido(
    client_autenticado_vinculo_escola_cemei,
    alteracao_cemei,
    periodo_manha,
    periodo_tarde,
    tipo_alimentacao_lanche,
    tipo_alimentacao_refeicao,
    tipo_alimentacao_lanche_emergencial,
):
    client, user = client_autenticado_vinculo_escola_cemei
    payload = {
        "escola": alteracao_cemei.escola.uuid,
        "motivo": alteracao_cemei.motivo.uuid,
        "alunos_cei_e_ou_emei": "EMEI",
        "alterar_dia": "28/04/2025",
        "substituicoes_cemei_cei_periodo_escolar": [],
        "substituicoes_cemei_emei_periodo_escolar": [
            {
                "qtd_alunos": "45",
                "matriculados_quando_criado": 261,
                "periodo_escolar": periodo_tarde.uuid,
                "tipos_alimentacao_de": [
                    tipo_alimentacao_refeicao.uuid,
                    tipo_alimentacao_lanche.uuid,
                ],
                "tipos_alimentacao_para": [tipo_alimentacao_lanche_emergencial.uuid],
            },
            {
                "qtd_alunos": "45",
                "matriculados_quando_criado": 261,
                "periodo_escolar": periodo_manha.uuid,
                "tipos_alimentacao_de": [tipo_alimentacao_lanche.uuid],
                "tipos_alimentacao_para": [tipo_alimentacao_lanche_emergencial.uuid],
            },
        ],
        "datas_intervalo": [{"data": "2025-04-28"}],
    }
    response = client.post(
        "/alteracoes-cardapio-cemei/", content_type="application/json", data=payload
    )
    assert response.status_code == status.HTTP_201_CREATED
