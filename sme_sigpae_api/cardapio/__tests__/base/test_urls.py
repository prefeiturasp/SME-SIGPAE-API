import json

import pytest
from rest_framework import status

from sme_sigpae_api.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)

pytestmark = pytest.mark.django_db


ENDPOINT_HORARIO_DO_COMBO = "horario-do-combo-tipo-de-alimentacao-por-unidade-escolar"
ENDPOINT_VINCULOS_ALIMENTACAO = "vinculos-tipo-alimentacao-u-e-periodo-escolar"


def test_url_endpoint_alterar_tipos_alimentacao(
    client_autenticado_vinculo_escola_cardapio, alterar_tipos_alimentacao_data
):
    vinculo = alterar_tipos_alimentacao_data["vinculo"]
    tipos_alimentacao = alterar_tipos_alimentacao_data["tipos_alimentacao"]
    dict_params = {
        "periodo_escolar": str(vinculo.periodo_escolar.uuid),
        "tipo_unidade_escolar": str(vinculo.tipo_unidade_escolar.uuid),
        "tipos_alimentacao": [str(tp.uuid) for tp in tipos_alimentacao],
        "uuid": str(vinculo.uuid),
    }
    url = f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/atualizar_lista_de_vinculos/"
    response = client_autenticado_vinculo_escola_cardapio.put(
        url,
        content_type="application/json",
        data=json.dumps({"vinculos": [dict_params]}),
    )
    vinculo_atualizado = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.first()
    )
    assert response.status_code == status.HTTP_200_OK
    assert vinculo_atualizado.tipos_alimentacao.count() == 2


def test_url_endpoint_get_vinculos_tipo_alimentacao(
    client_autenticado_vinculo_escola, vinculo_tipo_alimentacao
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert json[0]["uuid"] == str(vinculo_tipo_alimentacao.uuid)
    assert json[0]["periodo_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.periodo_escolar.uuid
    )
    assert json[0]["tipo_unidade_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.tipo_unidade_escolar.uuid
    )
    assert len(json[0]["tipos_alimentacao"]) == 5

    # testa endpoint de filtro tipo_ue
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/tipo_unidade_escolar/{vinculo_tipo_alimentacao.tipo_unidade_escolar.uuid}/",
    )
    json = response.json()["results"]
    assert json[0]["uuid"] == str(vinculo_tipo_alimentacao.uuid)
    assert json[0]["periodo_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.periodo_escolar.uuid
    )
    assert json[0]["tipo_unidade_escolar"]["uuid"] == str(
        vinculo_tipo_alimentacao.tipo_unidade_escolar.uuid
    )
    assert len(json[0]["tipos_alimentacao"]) == 5


def test_endpoint_horario_do_combo_tipo_alimentacao_unidade_escolar(
    client_autenticado_vinculo_escola, horario_tipo_alimentacao
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_HORARIO_DO_COMBO}/escola/{horario_tipo_alimentacao.escola.uuid}/"
    )
    json = response.json()["results"]
    assert response.status_code == status.HTTP_200_OK
    assert json[0]["uuid"] == str(horario_tipo_alimentacao.uuid)
    assert json[0]["hora_inicial"] == horario_tipo_alimentacao.hora_inicial
    assert json[0]["hora_final"] == horario_tipo_alimentacao.hora_final
    assert json[0]["tipo_alimentacao"] == {
        "uuid": "c42a24bb-14f8-4871-9ee8-05bc42cf3061",
        "posicao": 2,
        "nome": "Lanche",
    }
    assert json[0]["periodo_escolar"] == {
        "uuid": "22596464-271e-448d-bcb3-adaba43fffc8",
        "tipo_turno": None,
        "nome": "TARDE",
        "posicao": None,
        "possui_alunos_regulares": None,
    }
    assert json[0]["escola"] == {
        "uuid": "a627fc63-16fd-482c-a877-16ebc1a82e57",
        "nome": "EMEF JOAO MENDES",
        "codigo_eol": "000546",
        "quantidade_alunos": 0,
    }


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_emef(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_emef
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_emef.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert len(json) == 4
    assert json[0]["periodo_escolar"]["nome"] == "MANHA"
    assert json[1]["periodo_escolar"]["nome"] == "TARDE"
    assert json[2]["periodo_escolar"]["nome"] == "INTEGRAL"
    assert json[3]["periodo_escolar"]["nome"] == "NOITE"


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_emei(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_emei
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_emei.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert len(json) == 3
    assert json[0]["periodo_escolar"]["nome"] == "MANHA"
    assert json[1]["periodo_escolar"]["nome"] == "TARDE"
    assert json[2]["periodo_escolar"]["nome"] == "INTEGRAL"


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_cei(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_cei
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_cei.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert len(json) == 4
    assert json[0]["periodo_escolar"]["nome"] == "INTEGRAL"
    assert json[1]["periodo_escolar"]["nome"] == "PARCIAL"
    assert json[2]["periodo_escolar"]["nome"] == "MANHA"
    assert json[3]["periodo_escolar"]["nome"] == "TARDE"


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_cieja(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_cieja
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_cieja.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert len(json) == 5
    assert json[0]["periodo_escolar"]["nome"] == "MANHA"
    assert json[1]["periodo_escolar"]["nome"] == "INTERMEDIARIO"
    assert json[2]["periodo_escolar"]["nome"] == "TARDE"
    assert json[3]["periodo_escolar"]["nome"] == "VESPERTINO"
    assert json[4]["periodo_escolar"]["nome"] == "NOITE"


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_ceu_gestao(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_ceu_gestao
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_ceu_gestao.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert len(json) == 4
    assert json[0]["periodo_escolar"]["nome"] == "MANHA"
    assert json[1]["periodo_escolar"]["nome"] == "TARDE"
    assert json[2]["periodo_escolar"]["nome"] == "INTEGRAL"
    assert json[3]["periodo_escolar"]["nome"] == "NOITE"


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_emebs(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_emebs
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_emebs.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert len(json) == 4
    assert json[0]["periodo_escolar"]["nome"] == "MANHA"
    assert json[1]["periodo_escolar"]["nome"] == "TARDE"
    assert json[2]["periodo_escolar"]["nome"] == "INTEGRAL"
    assert json[3]["periodo_escolar"]["nome"] == "NOITE"


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_cemei(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_cemei
):
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_cemei.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    assert len(json) == 4

    assert json[0]["tipo_unidade_escolar"]["iniciais"] == "CEI DIRET"
    assert json[0]["periodo_escolar"]["nome"] == "INTEGRAL"

    assert json[1]["tipo_unidade_escolar"]["iniciais"] == "EMEI"
    assert json[1]["periodo_escolar"]["nome"] == "MANHA"

    assert json[1]["tipo_unidade_escolar"]["iniciais"] == "EMEI"
    assert json[2]["periodo_escolar"]["nome"] == "TARDE"

    assert json[1]["tipo_unidade_escolar"]["iniciais"] == "EMEI"
    assert json[3]["periodo_escolar"]["nome"] == "INTEGRAL"
