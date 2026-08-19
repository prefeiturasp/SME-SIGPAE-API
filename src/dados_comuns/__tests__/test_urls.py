import datetime
import json

import pytest
from django.core.cache import cache
from faker import Faker
from freezegun import freeze_time
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIRequestFactory

from ...escola.models import TipoUnidadeEscolar
from ...perfil.models import Usuario
from ..models import (
    CategoriaPerguntaFrequente,
    CentralDeDownload,
    Notificacao,
    PerguntaFrequente,
    VersaoSistema,
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
    from src.dados_comuns.constants import obter_dias_uteis_apos_hoje

    result = obter_dias_uteis_apos_hoje(3)
    assert str(result) == "2021-06-21"


@freeze_time("2021-06-18")
def test_proximo_dia_util_suspensao_alimentacao_sexta(client_autenticado):
    from src.dados_comuns.constants import obter_dias_uteis_apos_hoje

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

    factory = APIRequestFactory()
    request = factory.get("/")
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
                "arquivo": request.build_absolute_uri(download.arquivo.url),
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

    factory = APIRequestFactory()
    request = factory.get("/")
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
                "arquivo": request.build_absolute_uri(download.arquivo.url),
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


def test_url_cria_categoria_pergunta_frequente(
    client_autenticado_coordenador_codae,
):
    payload = {"nome": "Alimentação Escolar"}

    response = client_autenticado_coordenador_codae.post(
        "/categorias-pergunta-frequente/",
        content_type="application/json",
        data=payload,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["nome"] == payload["nome"]
    assert CategoriaPerguntaFrequente.objects.filter(
        nome=payload["nome"],
    ).exists()


def test_url_nao_cria_categoria_pergunta_frequente_duplicada(
    client_autenticado_coordenador_codae,
):
    baker.make(
        CategoriaPerguntaFrequente,
        nome="Alimentação e Nutrição",
    )

    payload = {"nome": "  ALIMENTACAO E NUTRICAO  "}

    response = client_autenticado_coordenador_codae.post(
        "/categorias-pergunta-frequente/",
        content_type="application/json",
        data=payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["nome"][0]
        == "Não é possível cadastrar a categoria, pois já existe uma categoria com esse nome. Altere o nome informado e tente novamente."
    )
    assert CategoriaPerguntaFrequente.objects.count() == 1


def test_url_nao_cria_categoria_com_usuario_sem_permissao(
    usuario_teste_notificacao_autenticado,
):
    _, client = usuario_teste_notificacao_autenticado
    payload = {"nome": "Gestão de Produtos"}

    response = client.post(
        "/categorias-pergunta-frequente/",
        content_type="application/json",
        data=payload,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not CategoriaPerguntaFrequente.objects.filter(
        nome=payload["nome"],
    ).exists()


def test_url_atualiza_categoria_pergunta_frequente(
    client_autenticado_coordenador_codae,
):
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Nome anterior",
    )
    payload = {"nome": "Alimentação Escolar"}

    response = client_autenticado_coordenador_codae.put(
        f"/categorias-pergunta-frequente/{categoria.uuid}/",
        content_type="application/json",
        data=payload,
    )

    assert response.status_code == status.HTTP_200_OK

    categoria.refresh_from_db()

    assert categoria.nome == payload["nome"]
    assert response.json()["nome"] == payload["nome"]


def test_url_atualiza_parcialmente_categoria_pergunta_frequente(
    client_autenticado_coordenador_codae,
):
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Nome anterior",
    )
    payload = {"nome": "Gestão de Produtos"}

    response = client_autenticado_coordenador_codae.patch(
        f"/categorias-pergunta-frequente/{categoria.uuid}/",
        content_type="application/json",
        data=payload,
    )

    assert response.status_code == status.HTTP_200_OK

    categoria.refresh_from_db()

    assert categoria.nome == payload["nome"]
    assert response.json()["nome"] == payload["nome"]


def test_url_exclui_categoria_pergunta_frequente(
    client_autenticado_coordenador_codae,
):
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Categoria para exclusão",
    )

    response = client_autenticado_coordenador_codae.delete(
        f"/categorias-pergunta-frequente/{categoria.uuid}/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not CategoriaPerguntaFrequente.objects.filter(
        uuid=categoria.uuid,
    ).exists()


def test_url_usuario_sem_permissao_nao_exclui_categoria(
    usuario_teste_notificacao_autenticado,
):
    _, client = usuario_teste_notificacao_autenticado

    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Categoria protegida",
    )

    response = client.delete(
        f"/categorias-pergunta-frequente/{categoria.uuid}/",
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert CategoriaPerguntaFrequente.objects.filter(
        uuid=categoria.uuid,
    ).exists()


def test_url_api_version_sucesso(client):
    cache.clear()
    versao = VersaoSistema.objects.get()
    versao.versao = "2.5.1"
    versao.save()
    response = client.get("/api-version/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"API_Version": "2.5.1"}


def test_url_api_version_versao_vazia(client):
    cache.clear()
    versao = VersaoSistema.objects.get()
    versao.versao = ""
    versao.save()
    response = client.get("/api-version/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Não foi possível obter a última versão da API"
    }



def test_url_atualiza_categoria_pergunta_frequente(
    client_autenticado_coordenador_codae,
):
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Categoria Antiga",
    )

    payload = {
        "nome": "Categoria Atualizada",
    }

    response = client_autenticado_coordenador_codae.patch(
        f"/categorias-pergunta-frequente/{categoria.uuid}/",
        content_type="application/json",
        data=payload,
    )

    categoria.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert categoria.nome == "Categoria Atualizada"


def test_url_atualiza_categoria_mantem_perguntas_vinculadas(
    client_autenticado_coordenador_codae,
):
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Categoria Antiga",
    )
    pergunta_1 = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        pergunta="Primeira pergunta",
    )
    pergunta_2 = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        pergunta="Segunda pergunta",
    )

    response = client_autenticado_coordenador_codae.patch(
        f"/categorias-pergunta-frequente/{categoria.uuid}/",
        content_type="application/json",
        data={"nome": "Categoria Atualizada"},
    )

    pergunta_1.refresh_from_db()
    pergunta_2.refresh_from_db()
    categoria.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert categoria.nome == "Categoria Atualizada"
    assert pergunta_1.categoria == categoria
    assert pergunta_2.categoria == categoria
    assert PerguntaFrequente.objects.filter(categoria=categoria).count() == 2


def test_url_exclui_categoria_e_perguntas_vinculadas(
    client_autenticado_coordenador_codae,
):
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        nome="Categoria para Excluir",
    )
    pergunta_1 = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        pergunta="Primeira pergunta",
    )
    pergunta_2 = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        pergunta="Segunda pergunta",
    )

    categoria_uuid = categoria.uuid
    pergunta_1_uuid = pergunta_1.uuid
    pergunta_2_uuid = pergunta_2.uuid

    response = client_autenticado_coordenador_codae.delete(
        f"/categorias-pergunta-frequente/{categoria_uuid}/",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert not CategoriaPerguntaFrequente.objects.filter(
        uuid=categoria_uuid
    ).exists()
    assert not PerguntaFrequente.objects.filter(
        uuid=pergunta_1_uuid
    ).exists()
    assert not PerguntaFrequente.objects.filter(
        uuid=pergunta_2_uuid
    ).exists()

def test_url_exclui_apenas_perguntas_da_categoria_excluida(
    client_autenticado_coordenador_codae,
):
    categoria_excluida = baker.make(
        CategoriaPerguntaFrequente,
        nome="Categoria para Excluir",
    )
    categoria_mantida = baker.make(
        CategoriaPerguntaFrequente,
        nome="Categoria Mantida",
    )

    pergunta_excluida = baker.make(
        PerguntaFrequente,
        categoria=categoria_excluida,
        pergunta="Pergunta que deve ser excluída",
    )
    pergunta_mantida = baker.make(
        PerguntaFrequente,
        categoria=categoria_mantida,
        pergunta="Pergunta que deve permanecer",
    )

    response = client_autenticado_coordenador_codae.delete(
        f"/categorias-pergunta-frequente/{categoria_excluida.uuid}/",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert not CategoriaPerguntaFrequente.objects.filter(
        uuid=categoria_excluida.uuid
    ).exists()
    assert not PerguntaFrequente.objects.filter(
        uuid=pergunta_excluida.uuid
    ).exists()

    assert CategoriaPerguntaFrequente.objects.filter(
        uuid=categoria_mantida.uuid
    ).exists()
    assert PerguntaFrequente.objects.filter(
        uuid=pergunta_mantida.uuid
    ).exists()

def test_url_lista_categorias_ordenadas_da_mais_antiga_para_mais_recente(
    client_autenticado_coordenador_codae,
):
    categoria_1 = baker.make(
        CategoriaPerguntaFrequente,
        nome="Primeira Categoria",
    )
    categoria_2 = baker.make(
        CategoriaPerguntaFrequente,
        nome="Segunda Categoria",
    )
    categoria_3 = baker.make(
        CategoriaPerguntaFrequente,
        nome="Terceira Categoria",
    )

    response = client_autenticado_coordenador_codae.get(
        "/categorias-pergunta-frequente/",
    )

    assert response.status_code == status.HTTP_200_OK

    categorias = response.json()["results"]

    uuids = [categoria["uuid"] for categoria in categorias]

    assert uuids.index(str(categoria_1.uuid)) < uuids.index(
        str(categoria_2.uuid)
    )
    assert uuids.index(str(categoria_2.uuid)) < uuids.index(
        str(categoria_3.uuid)
    )


def test_url_cadastra_duvida_frequente_com_perfil_autorizado(
    client,
    usuario_com_perfil_autorizado_a_cadastrar_novas_categorias_na_pagina_de_ajuda,
):
    usuario = (
        usuario_com_perfil_autorizado_a_cadastrar_novas_categorias_na_pagina_de_ajuda
    )
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        uuid="16e630a8-4564-4c32-888a-47615407b4b4",
    )
    perfil = baker.make(
        "Perfil",
        uuid="602e25e5-3d0e-44a2-8993-6b30742ee924",
        ativo=True,
    )
    client.force_login(usuario)

    response = client.post(
        "/perguntas-frequentes/",
        content_type="application/json",
        data={
            "categoria": str(categoria.uuid),
            "perfis": [str(perfil.uuid)],
            "todos_os_perfis": False,
            "pergunta": "Como consultar uma dúvida frequente?",
            "resposta": "Acesse a página de Ajuda.",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    pergunta = PerguntaFrequente.objects.get(uuid=response.json()["uuid"])
    assert pergunta.categoria == categoria
    assert list(pergunta.perfis.all()) == [perfil]


def test_url_nao_cadastra_duvida_frequente_com_perfil_nao_autorizado(
    usuario_teste_notificacao_autenticado,
):
    _, client = usuario_teste_notificacao_autenticado
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        uuid="e9273c66-396d-4996-8530-4251037e36f2",
    )

    response = client.post(
        "/perguntas-frequentes/",
        content_type="application/json",
        data={
            "categoria": str(categoria.uuid),
            "perfis": [],
            "todos_os_perfis": True,
            "pergunta": "Dúvida sem permissão",
            "resposta": "Esta dúvida não deve ser cadastrada.",
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not PerguntaFrequente.objects.filter(
        pergunta="Dúvida sem permissão"
    ).exists()


def test_url_lista_apenas_duvidas_visiveis_para_perfil_atual(
    client_autenticado_coordenador_codae,
):
    usuario = Usuario.objects.get(email="cogestor_1@sme.prefeitura.sp.gov.br")
    perfil_atual = usuario.vinculo_atual.perfil
    outro_perfil = baker.make(
        "Perfil",
        uuid="6886938f-73a8-4be5-b223-943c580863a2",
        ativo=True,
    )
    categoria = baker.make(
        CategoriaPerguntaFrequente,
        uuid="2794fa5f-0bd8-4687-97ae-67b6ea21403c",
    )
    pergunta_todos = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        todos_os_perfis=True,
        uuid="6d003422-d965-47cf-a618-a12c23cb5464",
    )
    pergunta_perfil_atual = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        todos_os_perfis=False,
        uuid="22573ae0-8364-41fb-a35f-64136942d67d",
    )
    pergunta_outro_perfil = baker.make(
        PerguntaFrequente,
        categoria=categoria,
        todos_os_perfis=False,
        uuid="782b6b12-1180-4788-ad71-a967e4313859",
    )
    pergunta_perfil_atual.perfis.add(perfil_atual)
    pergunta_outro_perfil.perfis.add(outro_perfil)

    response = client_autenticado_coordenador_codae.get("/perguntas-frequentes/")

    assert response.status_code == status.HTTP_200_OK
    uuids = {item["uuid"] for item in response.json()["results"]}
    assert uuids == {
        str(pergunta_todos.uuid),
        str(pergunta_perfil_atual.uuid),
    }


def test_url_mantem_categorias_e_filtra_perguntas_por_perfil_atual(
    client_autenticado_coordenador_codae,
):
    usuario = Usuario.objects.get(email="cogestor_1@sme.prefeitura.sp.gov.br")
    perfil_atual = usuario.vinculo_atual.perfil
    outro_perfil = baker.make(
        "Perfil",
        uuid="3b198176-5b92-447a-be4e-a31b58797c68",
        ativo=True,
    )
    categoria_com_pergunta = baker.make(
        CategoriaPerguntaFrequente,
        uuid="1ff561ec-f454-4303-8bbc-43a577b9eeaf",
    )
    categoria_sem_pergunta_visivel = baker.make(
        CategoriaPerguntaFrequente,
        uuid="db8cf575-3b92-4b4b-b654-c6235952957c",
    )
    pergunta_visivel = baker.make(
        PerguntaFrequente,
        categoria=categoria_com_pergunta,
        todos_os_perfis=False,
        uuid="118bdfa7-7ab0-447a-a431-5659d0b54cf5",
    )
    pergunta_invisivel = baker.make(
        PerguntaFrequente,
        categoria=categoria_sem_pergunta_visivel,
        todos_os_perfis=False,
        uuid="af441715-b128-4247-85a7-c621824e55c4",
    )
    pergunta_visivel.perfis.add(perfil_atual)
    pergunta_invisivel.perfis.add(outro_perfil)

    response = client_autenticado_coordenador_codae.get(
        "/categorias-pergunta-frequente/perguntas-por-categoria/"
    )

    assert response.status_code == status.HTTP_200_OK
    categorias = {item["uuid"]: item["perguntas"] for item in response.json()}
    assert categorias[str(categoria_com_pergunta.uuid)][0]["uuid"] == str(
        pergunta_visivel.uuid
    )
    assert categorias[str(categoria_sem_pergunta_visivel.uuid)] == []
