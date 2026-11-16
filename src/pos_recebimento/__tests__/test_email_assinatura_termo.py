import json
import logging
from unittest.mock import patch

import pytest
from django.template.loader import render_to_string
from rest_framework import status

from src.dados_comuns import constants as const
from src.pos_recebimento.api.services import TermoRecebimentoProvisorioService
from src.pos_recebimento.models import TermoRecebimentoProvisorio

pytestmark = pytest.mark.django_db

URL_TERMOS = "/pos-recebimento/termos/"
PATH_TASK = "src.pos_recebimento.api.services.envia_email_unico_task"
BASE_URL_TESTE = "https://sigpae.teste"
ROTA_DETALHAR_TERMO = "/pos-recebimento/detalhar-termo-recebimento-provisorio"
TEMPLATE_EMAIL = "pos_recebimento_email_assinatura_termo_recebimento.html"
ASSUNTO = "Assinatura do Termo de Recebimento Provisório"
EMAIL_RODAPE = "smecodaesigpae@sme.prefeitura.sp.gov.br"


def _post_termo(client, payload):
    return client.post(
        URL_TERMOS,
        content_type="application/json",
        data=json.dumps(payload),
    )


def _emails_enviados(mock_task):
    return [chamada.kwargs["email"] for chamada in mock_task.delay.call_args_list]


@pytest.fixture
def mock_task():
    with patch(PATH_TASK) as mock:
        yield mock


@pytest.fixture
def base_url_teste():
    with patch("src.pos_recebimento.api.services.base_url", BASE_URL_TESTE):
        yield BASE_URL_TESTE


def _html_enviado_ao_primeiro_fiscal(termo, mock_task):
    TermoRecebimentoProvisorioService.envia_email_assinatura_fiscais(termo)
    return mock_task.delay.call_args_list[0].kwargs["html"]


@pytest.mark.parametrize(
    "client_fixture",
    ["client_autenticado_dilog_cronograma", "client_autenticado_codae_dilog"],
)
def test_salvar_e_enviar_envia_email_individual_aos_tres_fiscais(
    request,
    client_fixture,
    payload_termo,
    tres_fiscais,
    mock_task,
    django_capture_on_commit_callbacks,
):
    client = request.getfixturevalue(client_fixture)

    with django_capture_on_commit_callbacks(execute=True):
        response = _post_termo(client, payload_termo)

    assert response.status_code == status.HTTP_201_CREATED
    assert mock_task.delay.call_count == 3
    for fiscal, chamada in zip(tres_fiscais, mock_task.delay.call_args_list):
        assert chamada.kwargs["email"] == fiscal.email
        assert chamada.kwargs["assunto"] == ASSUNTO
        assert f"Olá, <strong>{fiscal.nome}</strong>!" in chamada.kwargs["html"]


def test_email_agendado_somente_apos_commit(
    client_autenticado_dilog_cronograma,
    payload_termo,
    mock_task,
    django_capture_on_commit_callbacks,
):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        response = _post_termo(client_autenticado_dilog_cronograma, payload_termo)

    assert response.status_code == status.HTTP_201_CREATED
    assert len(callbacks) == 1
    mock_task.delay.assert_not_called()


def test_fiscal_duplicado_recebe_um_unico_email(
    client_autenticado_dilog_cronograma,
    payload_termo,
    tres_fiscais,
    mock_task,
    django_capture_on_commit_callbacks,
):
    payload = {**payload_termo, "fiscal_2": payload_termo["fiscal_1"]}

    with django_capture_on_commit_callbacks(execute=True):
        response = _post_termo(client_autenticado_dilog_cronograma, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert _emails_enviados(mock_task) == [tres_fiscais[0].email, tres_fiscais[2].email]


def test_usuario_que_nao_e_fiscal_nao_recebe_email(
    client_autenticado_dilog_cronograma,
    payload_termo,
    usuario_fiscal,
    mock_task,
    django_capture_on_commit_callbacks,
):
    with django_capture_on_commit_callbacks(execute=True):
        response = _post_termo(client_autenticado_dilog_cronograma, payload_termo)

    assert response.status_code == status.HTTP_201_CREATED
    emails = _emails_enviados(mock_task)
    assert usuario_fiscal.email not in emails
    assert "cronograma@teste.com" not in emails


def test_fiscal_sem_email_nao_interrompe_envio_aos_demais(
    client_autenticado_dilog_cronograma,
    payload_termo,
    tres_fiscais,
    mock_task,
    django_capture_on_commit_callbacks,
    caplog,
):
    fiscal_sem_email = tres_fiscais[1]
    fiscal_sem_email.email = ""
    fiscal_sem_email.save(update_fields=["email"])

    with caplog.at_level(logging.WARNING, logger="src.pos_recebimento.api.services"):
        with django_capture_on_commit_callbacks(execute=True):
            response = _post_termo(client_autenticado_dilog_cronograma, payload_termo)

    assert response.status_code == status.HTTP_201_CREATED
    assert _emails_enviados(mock_task) == [tres_fiscais[0].email, tres_fiscais[2].email]
    assert str(fiscal_sem_email.uuid) in caplog.text


def test_falha_no_envio_nao_desfaz_criacao_do_termo(
    client_autenticado_dilog_cronograma,
    payload_termo,
    mock_task,
    django_capture_on_commit_callbacks,
):
    mock_task.delay.side_effect = ConnectionError("broker indisponível")

    with django_capture_on_commit_callbacks(execute=True):
        response = _post_termo(client_autenticado_dilog_cronograma, payload_termo)

    assert response.status_code == status.HTTP_201_CREATED
    termo = TermoRecebimentoProvisorio.objects.get(uuid=response.json()["uuid"])
    assert termo.status == TermoRecebimentoProvisorio.ENVIADO_FISCAIS


def test_criacao_invalida_nao_envia_email(
    client_autenticado_dilog_cronograma,
    payload_termo,
    mock_task,
    django_capture_on_commit_callbacks,
):
    payload = {**payload_termo, "cronogramas": []}

    with django_capture_on_commit_callbacks(execute=True):
        response = _post_termo(client_autenticado_dilog_cronograma, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_task.delay.assert_not_called()


def test_assinatura_do_fiscal_nao_envia_email(
    client,
    tres_fiscais,
    termo_para_assinatura,
    mock_task,
    django_capture_on_commit_callbacks,
):
    client.login(
        username=tres_fiscais[0].username, password=const.DJANGO_ADMIN_PASSWORD
    )

    with django_capture_on_commit_callbacks(execute=True):
        response = client.patch(
            f"{URL_TERMOS}{termo_para_assinatura.uuid}/fiscal-assina-termo/",
            content_type="application/json",
            data=json.dumps({"password": const.DJANGO_ADMIN_PASSWORD}),
        )

    assert response.status_code == status.HTTP_200_OK
    mock_task.delay.assert_not_called()


def test_template_email_contem_titulo_link_do_termo_e_rodape(
    termo_para_assinatura, tres_fiscais, mock_task, base_url_teste
):
    html = _html_enviado_ao_primeiro_fiscal(termo_para_assinatura, mock_task)

    url_termo = (
        f"{base_url_teste}{ROTA_DETALHAR_TERMO}?uuid={termo_para_assinatura.uuid}"
    )
    assert "<b>Termo de Recebimento Provisório</b>" in html
    assert f"Olá, <strong>{tres_fiscais[0].nome}</strong>!" in html
    assert "<strong>TERMO DE RECEBIMENTO PROVISÓRIO</strong>" in html
    assert f'<a href="{base_url_teste}" target="_blank"' in html
    assert f'<a href="{url_termo}" target="_blank"' in html
    assert "seja sempre um sucesso!\n" in html
    assert 'sucesso!"' not in html


def test_link_acessar_termo_alinhado_a_esquerda(
    termo_para_assinatura, mock_task, base_url_teste
):
    html = _html_enviado_ao_primeiro_fiscal(termo_para_assinatura, mock_task)

    celula_link = html.split("Acessar Termo</a>")[0].rsplit("<td ", 1)[1]
    assert celula_link.startswith('align="left" style="text-align: left;')


@pytest.mark.parametrize(
    "react_app_url,base_esperada",
    [
        ("https://sigpae.teste", "https://sigpae.teste"),
        ("http://localhost:3000", "http://localhost:3000"),
        ("sigpae.teste", "https://sigpae.teste"),
        ("localhost:3000", "http://localhost:3000"),
    ],
)
def test_links_do_email_sao_absolutos_com_protocolo(
    termo_para_assinatura, mock_task, react_app_url, base_esperada
):
    with patch("src.pos_recebimento.api.services.base_url", react_app_url):
        html = _html_enviado_ao_primeiro_fiscal(termo_para_assinatura, mock_task)

    url_termo = (
        f"{base_esperada}{ROTA_DETALHAR_TERMO}?uuid={termo_para_assinatura.uuid}"
    )
    assert f'<a href="{url_termo}" target="_blank"' in html
    assert f'<a href="{base_esperada}" target="_blank"' in html


def test_template_parametriza_nome_do_termo():
    html = render_to_string(
        TEMPLATE_EMAIL,
        {
            "titulo": "Termo de Recebimento Definitivo",
            "nome_termo": "Termo de Recebimento Definitivo",
            "nome_destinatario": "Fiscal",
            "url_sigpae": BASE_URL_TESTE,
            "url_termo": BASE_URL_TESTE,
        },
    )

    assert "<b>Termo de Recebimento Definitivo</b>" in html
    assert "<strong>TERMO DE RECEBIMENTO DEFINITIVO</strong>" in html


def test_rodape_segue_o_padrao_dos_demais_emails(
    termo_para_assinatura, mock_task, base_url_teste
):
    html = _html_enviado_ao_primeiro_fiscal(termo_para_assinatura, mock_task)

    assert f"<p>{EMAIL_RODAPE}</p>" in html
    assert "mailto:" not in html


def test_rodape_oculto_quando_hidden_email():
    html = render_to_string(TEMPLATE_EMAIL, {"titulo": "Titulo", "hidden_email": True})

    assert EMAIL_RODAPE not in html
