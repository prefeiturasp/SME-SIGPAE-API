from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "logistica_dilog_aceita_ou_nega_alteracao.html"
    hidden_email = None
    solicitacao = "12548"
    situacao = "cancelada"
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "solicitacao": solicitacao,
        "situacao": situacao,
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
        f" A Solicitação de Alteração <strong>N° {solicitacao}</strong> foi <strong>{situacao}</strong><br/>"
        in html
    )
