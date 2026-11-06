import datetime
from unittest.mock import MagicMock, patch

import pytest
from model_bakery import baker
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from src.dados_comuns.models import LogSolicitacoesUsuario
from src.medicao_inicial.models import MedicaoFinal, RelatorioFinanceiro

BASE_URL = "/medicao-inicial/relatorio-financeiro"
PATCH_RF = "src.eol_servico.utils.EOLServicoSGP.get_dados_usuario"
MSG_RF_NAO_LOCALIZADO = "RF não localizado. Verifique o número informado."
PAYLOAD = {
    "rf_responsavel_conferencia": "1234567",
    "numero_processo_pagamento": "6016.2025/0001234-5",
}


def _resposta_rf(status_code=200, json_data=None):
    resposta = MagicMock()
    resposta.status_code = status_code
    resposta.json.return_value = json_data
    return resposta


@pytest.fixture
def terceirizada_medicao_final():
    return baker.make("Terceirizada", razao_social="SINGULAR GESTÃO DE SERVIÇOS LTDA")


@pytest.fixture
def lote_medicao_final(terceirizada_medicao_final):
    return baker.make(
        "Lote",
        nome="Lote 05",
        terceirizada=terceirizada_medicao_final,
        diretoria_regional=baker.make(
            "DiretoriaRegional", nome="FREGUESIA/BRASILANDIA"
        ),
    )


@pytest.fixture
def grupo_medicao_final():
    return baker.make(
        "GrupoUnidadeEscolar",
        tipos_unidades=[
            baker.make("TipoUnidadeEscolar", iniciais="CEU CEMEI"),
            baker.make("TipoUnidadeEscolar", iniciais="CEMEI"),
        ],
    )


def _cria_relatorio(lote, grupo, mes="08", ano="2025", status_relatorio="EM_ANALISE"):
    return baker.make(
        "RelatorioFinanceiro",
        lote=lote,
        grupo_unidade_escolar=grupo,
        mes=mes,
        ano=ano,
        status=status_relatorio,
    )


@pytest.fixture
def relatorio_em_analise(lote_medicao_final, grupo_medicao_final):
    return _cria_relatorio(lote_medicao_final, grupo_medicao_final)


@pytest.fixture
def contrato_medicao_final(lote_medicao_final, terceirizada_medicao_final):
    contrato = baker.make(
        "Contrato",
        numero="2.456/SME/CODAE/2023",
        processo="6016.2023/0119881-1",
        terceirizada=terceirizada_medicao_final,
        data_proposta=datetime.date(2023, 1, 10),
    )
    contrato.lotes.add(lote_medicao_final)
    return contrato


def _url(relatorio, acao):
    return f"{BASE_URL}/{relatorio.uuid}/{acao}/"


@pytest.mark.django_db
def test_dados_medicao_final_com_contrato(
    client_autenticado_codae_medicao, relatorio_em_analise, contrato_medicao_final
):
    response = client_autenticado_codae_medicao.get(
        _url(relatorio_em_analise, "dados-medicao-final")
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "empresa_contratada": "SINGULAR GESTÃO DE SERVIÇOS LTDA",
        "periodo_inicio": "01/08/2025",
        "periodo_fim": "31/08/2025",
        "lote": "Lote 05",
        "dre": "FREGUESIA/BRASILANDIA",
        "tipos_unidade": "CEMEI, CEU CEMEI",
        "numero_contrato": "2.456/SME/CODAE/2023",
        "numero_processo_administrativo": "6016.2023/0119881-1",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mes,ano,ultimo_dia",
    [
        ("02", "2025", "28/02/2025"),
        ("02", "2024", "29/02/2024"),
        ("02", "2100", "28/02/2100"),
        ("12", "2025", "31/12/2025"),
        ("04", "2025", "30/04/2025"),
    ],
)
def test_dados_medicao_final_periodo(
    client_autenticado_codae_medicao,
    lote_medicao_final,
    grupo_medicao_final,
    mes,
    ano,
    ultimo_dia,
):
    relatorio = _cria_relatorio(lote_medicao_final, grupo_medicao_final, mes, ano)

    response = client_autenticado_codae_medicao.get(
        _url(relatorio, "dados-medicao-final")
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["periodo_inicio"] == f"01/{mes}/{ano}"
    assert response.json()["periodo_fim"] == ultimo_dia


@pytest.mark.django_db
def test_dados_medicao_final_sem_contrato(
    client_autenticado_codae_medicao, relatorio_em_analise
):
    response = client_autenticado_codae_medicao.get(
        _url(relatorio_em_analise, "dados-medicao-final")
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["numero_contrato"] is None
    assert response.json()["numero_processo_administrativo"] is None


@pytest.mark.django_db
def test_dados_medicao_final_ignora_contrato_encerrado_antes_do_periodo(
    client_autenticado_codae_medicao, relatorio_em_analise, contrato_medicao_final
):
    contrato_medicao_final.encerrado = True
    contrato_medicao_final.data_hora_encerramento = datetime.datetime(
        2025, 7, 31, 23, 59, tzinfo=datetime.timezone.utc
    )
    contrato_medicao_final.save()

    response = client_autenticado_codae_medicao.get(
        _url(relatorio_em_analise, "dados-medicao-final")
    )

    assert response.json()["numero_contrato"] is None


@pytest.mark.django_db
def test_dados_medicao_final_relatorio_inexistente(client_autenticado_codae_medicao):
    response = client_autenticado_codae_medicao.get(
        f"{BASE_URL}/3f1d9e8a-6b4c-4a72-9f15-2c8e7b6d1a43/dados-medicao-final/"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_gerar_medicao_final_sucesso(
    client_autenticado_codae_medicao, user_administrador_medicao, relatorio_em_analise
):
    usuario, _ = user_administrador_medicao
    payload = {
        **PAYLOAD,
        "numero_processo_pagamento": "  6016.2025/0001234-5  ",
        "nome_responsavel_conferencia": "NOME FORJADO PELO FRONT",
    }

    with patch(PATCH_RF, return_value=_resposta_rf(200, {"nome": "FULANO DE TAL"})):
        response = client_autenticado_codae_medicao.post(
            _url(relatorio_em_analise, "gerar-medicao-final"),
            payload,
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "GERADA_MEDICAO_FINAL"
    assert response.json()["status_display"] == "Gerada Medição Final"
    assert response.json()["possui_medicao_final"] is True
    relatorio_em_analise.refresh_from_db()
    assert relatorio_em_analise.status == "GERADA_MEDICAO_FINAL"
    medicao_final = relatorio_em_analise.medicao_final
    assert medicao_final.rf_responsavel_conferencia == "1234567"
    assert medicao_final.nome_responsavel_conferencia == "FULANO DE TAL"
    assert medicao_final.numero_processo_pagamento == "6016.2025/0001234-5"
    assert medicao_final.gerado_por == usuario

    log = LogSolicitacoesUsuario.objects.get(uuid_original=relatorio_em_analise.uuid)
    assert log.status_evento == LogSolicitacoesUsuario.MEDICAO_FINAL_GERADA
    assert log.solicitacao_tipo == LogSolicitacoesUsuario.RELATORIO_FINANCEIRO
    assert log.usuario == usuario
    assert log.get_status_evento_display() == "Gerada Medição Final"
    assert list(relatorio_em_analise.logs) == [log]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "campo", ["rf_responsavel_conferencia", "numero_processo_pagamento"]
)
@pytest.mark.parametrize("valor", [None, "", "   "])
def test_gerar_medicao_final_campo_obrigatorio(
    client_autenticado_codae_medicao, relatorio_em_analise, campo, valor
):
    payload = {**PAYLOAD, campo: valor}

    with patch(PATCH_RF) as mock_consulta:
        response = client_autenticado_codae_medicao.post(
            _url(relatorio_em_analise, "gerar-medicao-final"),
            payload,
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert campo in response.json()
    mock_consulta.assert_not_called()
    assert not MedicaoFinal.objects.exists()


@pytest.mark.django_db
def test_gerar_medicao_final_campo_ausente(
    client_autenticado_codae_medicao, relatorio_em_analise
):
    response = client_autenticado_codae_medicao.post(
        _url(relatorio_em_analise, "gerar-medicao-final"),
        {},
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert set(response.json()) == set(PAYLOAD)


@pytest.mark.django_db
def test_gerar_medicao_final_rf_com_letras(
    client_autenticado_codae_medicao, relatorio_em_analise
):
    payload = {**PAYLOAD, "rf_responsavel_conferencia": "12a4567"}

    response = client_autenticado_codae_medicao.post(
        _url(relatorio_em_analise, "gerar-medicao-final"),
        payload,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "rf_responsavel_conferencia" in response.json()


@pytest.mark.django_db
def test_gerar_medicao_final_rf_nao_localizado(
    client_autenticado_codae_medicao, relatorio_em_analise
):
    with patch(PATCH_RF, return_value=_resposta_rf(404)):
        response = client_autenticado_codae_medicao.post(
            _url(relatorio_em_analise, "gerar-medicao-final"),
            PAYLOAD,
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"rf_responsavel_conferencia": [MSG_RF_NAO_LOCALIZADO]}
    relatorio_em_analise.refresh_from_db()
    assert relatorio_em_analise.status == "EM_ANALISE"
    assert not MedicaoFinal.objects.exists()
    assert not LogSolicitacoesUsuario.objects.exists()


@pytest.mark.django_db
def test_gerar_medicao_final_servico_rf_indisponivel(
    client_autenticado_codae_medicao, relatorio_em_analise
):
    with patch(PATCH_RF, side_effect=ConnectionError("fora do ar")):
        response = client_autenticado_codae_medicao.post(
            _url(relatorio_em_analise, "gerar-medicao-final"),
            PAYLOAD,
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    relatorio_em_analise.refresh_from_db()
    assert relatorio_em_analise.status == "EM_ANALISE"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "status_relatorio", ["RELATORIO_FINANCEIRO_GERADO", "FINALIZADO"]
)
def test_gerar_medicao_final_status_nao_elegivel(
    client_autenticado_codae_medicao,
    lote_medicao_final,
    grupo_medicao_final,
    status_relatorio,
):
    relatorio = _cria_relatorio(
        lote_medicao_final, grupo_medicao_final, status_relatorio=status_relatorio
    )

    with patch(PATCH_RF) as mock_consulta:
        response = client_autenticado_codae_medicao.post(
            _url(relatorio, "gerar-medicao-final"),
            PAYLOAD,
            content_type="application/json",
        )

    mock_consulta.assert_not_called()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Em análise" in response.json()["non_field_errors"][0]
    relatorio.refresh_from_db()
    assert relatorio.status == status_relatorio
    assert not MedicaoFinal.objects.exists()
    assert not LogSolicitacoesUsuario.objects.exists()


@pytest.mark.django_db
def test_gerar_medicao_final_ja_gerada(
    client_autenticado_codae_medicao, user_administrador_medicao, relatorio_em_analise
):
    usuario, _ = user_administrador_medicao
    baker.make(
        "MedicaoFinal",
        relatorio_financeiro=relatorio_em_analise,
        gerado_por=usuario,
    )

    with patch(PATCH_RF, return_value=_resposta_rf(200, {"nome": "FULANO"})):
        response = client_autenticado_codae_medicao.post(
            _url(relatorio_em_analise, "gerar-medicao-final"),
            PAYLOAD,
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "já foi gerada" in response.json()["non_field_errors"][0]
    assert MedicaoFinal.objects.count() == 1


@pytest.mark.django_db
def test_gerar_medicao_final_duas_vezes_nao_duplica(
    client_autenticado_codae_medicao, relatorio_em_analise
):
    url = _url(relatorio_em_analise, "gerar-medicao-final")
    with patch(PATCH_RF, return_value=_resposta_rf(200, {"nome": "FULANO"})):
        primeira = client_autenticado_codae_medicao.post(
            url, PAYLOAD, content_type="application/json"
        )
        segunda = client_autenticado_codae_medicao.post(
            url, PAYLOAD, content_type="application/json"
        )

    assert primeira.status_code == status.HTTP_200_OK
    assert segunda.status_code == status.HTTP_400_BAD_REQUEST
    assert MedicaoFinal.objects.count() == 1
    assert LogSolicitacoesUsuario.objects.count() == 1


@pytest.mark.django_db
def test_gerar_medicao_final_sem_permissao(
    client_autenticado_diretoria_regional, relatorio_em_analise
):
    with patch(PATCH_RF, return_value=_resposta_rf(200, {"nome": "FULANO"})):
        response = client_autenticado_diretoria_regional.post(
            _url(relatorio_em_analise, "gerar-medicao-final"),
            PAYLOAD,
            content_type="application/json",
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    relatorio_em_analise.refresh_from_db()
    assert relatorio_em_analise.status == "EM_ANALISE"
    assert not MedicaoFinal.objects.exists()
    assert not LogSolicitacoesUsuario.objects.exists()


@pytest.mark.django_db
def test_gerar_medicao_final_relatorio_inexistente(client_autenticado_codae_medicao):
    response = client_autenticado_codae_medicao.post(
        f"{BASE_URL}/3f1d9e8a-6b4c-4a72-9f15-2c8e7b6d1a43/gerar-medicao-final/",
        PAYLOAD,
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_listagem_expoe_status_e_possui_medicao_final(
    client_autenticado_codae_medicao,
    user_administrador_medicao,
    lote_medicao_final,
    grupo_medicao_final,
):
    usuario, _ = user_administrador_medicao
    gerado = _cria_relatorio(
        lote_medicao_final,
        grupo_medicao_final,
        mes="08",
        status_relatorio="GERADA_MEDICAO_FINAL",
    )
    baker.make("MedicaoFinal", relatorio_financeiro=gerado, gerado_por=usuario)
    em_analise = _cria_relatorio(lote_medicao_final, grupo_medicao_final, mes="09")

    response = client_autenticado_codae_medicao.get(
        f"{BASE_URL}/", {"status": "GERADA_MEDICAO_FINAL,EM_ANALISE"}
    )

    assert response.status_code == status.HTTP_200_OK
    resultados = {r["uuid"]: r for r in response.json()["results"]}
    assert resultados[str(gerado.uuid)]["status"] == "GERADA_MEDICAO_FINAL"
    assert resultados[str(gerado.uuid)]["status_display"] == "Gerada Medição Final"
    assert resultados[str(gerado.uuid)]["possui_medicao_final"] is True
    assert resultados[str(em_analise.uuid)]["possui_medicao_final"] is False


def test_workflow_transicao_gerar_medicao_final_apenas_de_em_analise():
    workflow = RelatorioFinanceiro.workflow_class
    assert [
        (t.name, [s.name for s in t.source], t.target.name)
        for t in workflow.transitions
    ] == [("gerar_medicao_final", ["EM_ANALISE"], "GERADA_MEDICAO_FINAL")]


@pytest.mark.django_db
def test_transicao_gerar_medicao_final_exige_usuario(relatorio_em_analise):
    with pytest.raises(PermissionDenied):
        relatorio_em_analise.gerar_medicao_final()

    assert relatorio_em_analise.status == "EM_ANALISE"
    relatorio_em_analise.refresh_from_db()
    assert relatorio_em_analise.status == "EM_ANALISE"
    assert not LogSolicitacoesUsuario.objects.exists()
