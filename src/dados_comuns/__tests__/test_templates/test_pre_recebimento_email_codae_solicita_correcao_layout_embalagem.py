from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "pre_recebimento_email_codae_solicita_correcao_layout_embalagem.html"
    hidden_email = None
    numero_ficha = 12234

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_ficha": numero_ficha,
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
        f"A <strong>CODAE</strong> solicitou alterações do Layout de Embalagens referente a<br/>Ficha Técnica Nº <strong>{numero_ficha}</strong>"
        in html
    )
