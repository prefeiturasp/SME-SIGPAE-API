from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "fluxo_dre_solicita_e_codae_autoriza_ou_nega.html"
    hidden_email = None
    movimentacao_realizada = "ESCOLA_CANCELOU"
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "movimentacao_realizada": movimentacao_realizada,
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
