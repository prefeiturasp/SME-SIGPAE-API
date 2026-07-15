from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "recuperar_senha.html"
    hidden_email = None
    link_recuperar_senha = "https://linkrecuperarsenha.com"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "link_recuperar_senha": link_recuperar_senha,
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
        f'<p><a target="_blank" href="{link_recuperar_senha}">Clique aqui, para criar uma nova senha no SIGPAE</a></p>'
        in html
    )
