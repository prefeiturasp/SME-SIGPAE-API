import datetime
import json

import pytest
from model_bakery import baker
from rest_framework import status

from src.dados_comuns import constants
from src.pos_recebimento.models import LoteMemorandoOcorrencia, MemorandoOcorrencia

pytestmark = pytest.mark.django_db


def _post_json(client, url, payload):
    return client.post(
        url,
        content_type="application/json",
        data=json.dumps(payload),
    )


def _cria_usuario_escola(django_user_model, nome_perfil, email):
    """Cria usuário com vínculo ativo em uma Escola e perfil informado."""
    usuario = django_user_model.objects.create_user(
        username=email,
        password=constants.DJANGO_ADMIN_PASSWORD,
        email=email,
        registro_funcional="1234567",
        nome="Usuário da Unidade Educacional",
    )
    escola = baker.make("Escola")
    perfil = baker.make("Perfil", nome=nome_perfil, ativo=True)
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    return usuario, escola


def _payload_memorando():
    return {
        "categoria": MemorandoOcorrencia.CATEGORIA_NAO_PERECIVEIS,
        "produto": "Arroz Tipo 1",
        "tipo_ocorrencia": MemorandoOcorrencia.TIPO_RECLAMACAO_QUALIDADE,
        "lotes": [
            {
                "lote": "LOTE-001",
                "marca": "Marca A",
                "data_fabricacao": "01/01/2026",
                "data_validade": "01/01/2027",
                "quantidade_problema_devolucao": "10.50",
            },
            {
                "lote": "LOTE-002",
                "marca": "Marca B",
                "data_fabricacao": "02/02/2026",
                "data_validade": "02/02/2027",
                "quantidade_problema_devolucao": "0.00",
            },
        ],
    }


@pytest.fixture
def usuario_diretor_ue(django_user_model):
    usuario, escola = _cria_usuario_escola(
        django_user_model,
        constants.DIRETOR_UE,
        "diretor.ue@test.com",
    )
    return usuario, escola


@pytest.fixture
def client_diretor_ue(client, usuario_diretor_ue):
    client.login(
        username=usuario_diretor_ue[0].username,
        password=constants.DJANGO_ADMIN_PASSWORD,
    )
    return client, usuario_diretor_ue


def test_registrar_memorando_ocorrencia_201(client_diretor_ue):
    client, (usuario, escola) = client_diretor_ue

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        _payload_memorando(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    memorando = MemorandoOcorrencia.objects.get(uuid=response.json()["uuid"])
    assert memorando.escola == escola
    assert memorando.criado_por == usuario
    assert memorando.produto == "Arroz Tipo 1"
    assert memorando.lotes.count() == 2
    assert response.json()["lotes"][0]["lote"] == "LOTE-001"
    assert response.json()["lotes"][1]["lote"] == "LOTE-002"


def test_registrar_memorando_ocorrencia_administrador_ue(
    client,
    django_user_model,
):
    usuario, escola = _cria_usuario_escola(
        django_user_model,
        constants.ADMINISTRADOR_UE,
        "administrador.ue@test.com",
    )
    client.login(
        username=usuario.username,
        password=constants.DJANGO_ADMIN_PASSWORD,
    )

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        _payload_memorando(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert (
        MemorandoOcorrencia.objects.get(uuid=response.json()["uuid"]).escola == escola
    )


def test_registrar_memorando_ocorrencia_sem_permissao(client, django_user_model):
    usuario = django_user_model.objects.create_user(
        username="codae@test.com",
        password=constants.DJANGO_ADMIN_PASSWORD,
        email="codae@test.com",
        registro_funcional="7654321",
        nome="Usuário CODAE",
    )
    perfil = baker.make("Perfil", nome=constants.DILOG_QUALIDADE, ativo=True)
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=baker.make("Codae"),
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    client.login(
        username=usuario.username,
        password=constants.DJANGO_ADMIN_PASSWORD,
    )

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        _payload_memorando(),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_registrar_memorando_ocorrencia_campos_obrigatorios(client_diretor_ue):
    client, _ = client_diretor_ue
    payload = _payload_memorando()
    payload.pop("produto")
    payload.pop("lotes")

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "produto" in response.json()
    assert "lotes" in response.json()


def test_registrar_memorando_ocorrencia_quantidade_negativa(client_diretor_ue):
    client, _ = client_diretor_ue
    payload = _payload_memorando()
    payload["lotes"][0]["quantidade_problema_devolucao"] = "-1.00"

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        payload,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "lotes" in response.json()


def test_registrar_memorando_ocorrencia_categoria_flv(client_diretor_ue):
    client, _ = client_diretor_ue
    payload = _payload_memorando()
    payload["categoria"] = MemorandoOcorrencia.CATEGORIA_FLV

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        payload,
    )

    assert response.status_code == status.HTTP_201_CREATED
    memorando = MemorandoOcorrencia.objects.get(uuid=response.json()["uuid"])
    assert memorando.categoria == MemorandoOcorrencia.CATEGORIA_FLV


def test_registrar_memorando_ocorrencia_datas_formato_brasileiro(client_diretor_ue):
    client, _ = client_diretor_ue

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        _payload_memorando(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    lote = LoteMemorandoOcorrencia.objects.get(lote="LOTE-001")
    assert lote.data_fabricacao == datetime.date(2026, 1, 1)
    assert lote.data_validade == datetime.date(2027, 1, 1)
    assert str(lote.quantidade_problema_devolucao) == "10.50"


def test_lotes_persistidos_na_ordem_informada(client_diretor_ue):
    client, _ = client_diretor_ue

    response = _post_json(
        client,
        "/pos-recebimento/memorandos-ocorrencia/",
        _payload_memorando(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    memorando = MemorandoOcorrencia.objects.get(uuid=response.json()["uuid"])
    assert list(memorando.lotes.values_list("ordem", flat=True)) == [1, 2]
