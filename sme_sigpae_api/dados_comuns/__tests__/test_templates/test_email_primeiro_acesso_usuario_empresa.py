from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "email_primeiro_acesso_usuario_empresa.html"
    hidden_email = None
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
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
        f"<p>A liberação do acesso ao SIGPAE tem o intuito de agilizar o processo de cadastramento e uso do sistema, contudo, não gera responsabilidade contratual. O contrato será firmado, somente após a sua assinatura.</p>"
        in html
    )
