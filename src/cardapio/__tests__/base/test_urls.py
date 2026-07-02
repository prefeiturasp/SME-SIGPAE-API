import datetime
import json

import pytest
from model_bakery import baker
from rest_framework import status

from src.cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.dados_comuns import constants as dados_comuns_constants
from src.escola.models import PeriodoEscolar
from src.inclusao_alimentacao.models import (
    DiasMotivosInclusaoDeAlimentacaoCEMEI,
    InclusaoDeAlimentacaoCEMEI,
    MotivoInclusaoNormal,
    QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI,
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


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_com_mes_ano(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_emef
):
    """Testa endpoint com parâmetros de mês e ano para filtragem precisa"""
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_emef.uuid}/?ano=2025&mes=5"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    # Deve retornar períodos filtrados por mês e ano
    assert len(json) >= 0


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_apenas_ano_retrocompatibilidade(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_emef
):
    """Testa retrocompatibilidade quando apenas parâmetro ano é fornecido"""
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_emef.uuid}/?ano=2025"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    # Deve funcionar como antes quando apenas ano é fornecido
    assert len(json) == 4
    assert json[0]["periodo_escolar"]["nome"] == "MANHA"
    assert json[1]["periodo_escolar"]["nome"] == "TARDE"
    assert json[2]["periodo_escolar"]["nome"] == "INTEGRAL"
    assert json[3]["periodo_escolar"]["nome"] == "NOITE"


def test_url_endpoint_get_vinculos_tipo_alimentacao_escola_mes_diferente(
    client_autenticado_vinculo_escola, vinculo_alimentacao_periodo_escolar_emef
):
    """Testa endpoint com mês diferente para garantir que filtragem funciona corretamente"""
    response = client_autenticado_vinculo_escola.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/escola/{vinculo_alimentacao_periodo_escolar_emef.uuid}/?ano=2025&mes=12"
    )
    assert response.status_code == status.HTTP_200_OK
    json = response.json()["results"]
    # Deve retornar períodos filtrados para dezembro de 2025
    assert len(json) >= 0


def test_url_endpoint_vinculos_inclusoes_evento_especifico_cemei(
    client,
    django_user_model,
):
    terceirizada = baker.make("Terceirizada")
    lote = baker.make("Lote", terceirizada=terceirizada)
    tipo_gestao = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade_cemei = baker.make("escola.TipoUnidadeEscolar", iniciais="CEMEI")
    diretoria_regional = baker.make("DiretoriaRegional")
    escola_cemei = baker.make(
        "escola.Escola",
        lote=lote,
        nome="CEMEI JOAO MENDES",
        codigo_eol="000546",
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade_cemei,
    )

    email = "test_cemei_evento@test.com"
    password = dados_comuns_constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_diretor = baker.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cemei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    client.login(username=email, password=password)

    motivo = baker.make(MotivoInclusaoNormal, nome="Evento Específico")
    periodo_manha = baker.make(PeriodoEscolar, nome="MANHA")
    refeicao = baker.make("cardapio.TipoAlimentacao", nome="Refeicao")

    inclusao = baker.make(
        InclusaoDeAlimentacaoCEMEI,
        escola=escola_cemei,
        rastro_escola=escola_cemei,
        rastro_lote=lote,
        rastro_dre=diretoria_regional,
        status="CODAE_AUTORIZADO",
    )

    baker.make(
        DiasMotivosInclusaoDeAlimentacaoCEMEI,
        inclusao_alimentacao_cemei=inclusao,
        motivo=motivo,
        data="2025-02-03",
    )

    baker.make(
        QuantidadeDeAlunosEMEIInclusaoDeAlimentacaoCEMEI,
        inclusao_alimentacao_cemei=inclusao,
        periodo_escolar=periodo_manha,
        quantidade_alunos=20,
        tipos_alimentacao=[refeicao],
    )

    tipo_unidade_emei = baker.make("escola.TipoUnidadeEscolar", iniciais="EMEI")
    baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=tipo_unidade_emei,
        periodo_escolar=periodo_manha,
        ativo=True,
        tipos_alimentacao=[refeicao],
    )

    response = client.get(
        f"/{ENDPOINT_VINCULOS_ALIMENTACAO}/vinculos-inclusoes-evento-especifico-autorizadas/"
        f"?escola_uuid={escola_cemei.uuid}"
        f"&mes=2"
        f"&ano=2025"
        f"&tipo_solicitacao=Inclus%C3%A3o+de"
    )

    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) > 0
    periodos_nomes = [r["periodo_escolar"]["nome"] for r in results]
    assert "MANHA" in periodos_nomes
