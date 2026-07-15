from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "logistica_aguardando_cancelamento_distribuidor.html"
    hidden_email = None
    solicitacao = "#123XYZ"
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "solicitacao": solicitacao,
    }

    html = render_to_string(template, context=dados_template)
    assert isinstance(html, str)

    assert "<title>SIGPAE - Notificação</title>" in html
    assert "<p>smecodaesigpae@sme.prefeitura.sp.gov.br</p>" in html
    assert f"<b>{titulo}</b>" in html
    assert (
        'src="https://hom-sigpae.sme.prefeitura.sp.gov.br/django_static/images/email/email-sigpae.png'
        in html
    )
    assert (
        f"Foi disponibilizado para sua análise o <strong>Cancelamento</strong> de Guia(s) de <br/>"
        in html
    )
    assert (
        f"Remessa pertencentes a Requisição <strong>Nº {solicitacao}.</strong>" in html
    )
