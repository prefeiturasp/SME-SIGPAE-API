import pytest
from django.template.loader import render_to_string


def _dados_template_base(status_analise):
    return {
        "titulo": "Teste template",
        "hidden_email": None,
        "numero_cronograma": "089/2023",
        "status_analise": status_analise,
        "nome_produto": "ARROZ TIPO 1",
        "razao_social": "Razao Social LTDA",
        "nome_fantasia": "Fornecedor XYZ",
        "log_transicao": None,
        "url_solicitacao_alteracao": "http://teste.com",
    }


@pytest.mark.parametrize(
    "status_analise",
    [
        "APROVOU",
        "REPROVOU",
    ],
)
def test_template_email_parecer_codae(status_analise):
    template = "pre_recebimento_email_solicitacao_cronograma_parecer_codae.html"
    dados_template = _dados_template_base(status_analise)

    html = render_to_string(template, context=dados_template)
    assert isinstance(html, str)

    assert "<title>SIGPAE - Notificação</title>" in html
    assert "<p>smecodaesigpae@sme.prefeitura.sp.gov.br</p>" in html
    assert f"<b>{dados_template['titulo']}</b>" in html
    assert (
        'src="https://hom-sigpae.sme.prefeitura.sp.gov.br/django_static/images/email/email-sigpae.png'
        in html
    )
    assert (
        f"A <strong>CODAE</strong> {status_analise.lower()} a Solicitação de Alteração do Cronograma nº "
        f"<strong>{dados_template['numero_cronograma']}</strong> de <strong>{dados_template['nome_produto']}</strong>"
        in html
    )
    assert f"<strong>{dados_template['nome_fantasia']} - {dados_template['razao_social']}</strong>" in html
