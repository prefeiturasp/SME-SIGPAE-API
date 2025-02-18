from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "pre_recebimento_email_solicitacao_cronograma_parecer_codae.html"
    hidden_email = None
    numero_cronograma = 12234
    status_analise = "autorizou"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_cronograma": numero_cronograma,
        "status_analise": status_analise,
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
        f" A <strong>CODAE</strong> {status_analise} a Solicitação de Alteração do Cronograma <strong>{numero_cronograma}</strong>"
        in html
    )
