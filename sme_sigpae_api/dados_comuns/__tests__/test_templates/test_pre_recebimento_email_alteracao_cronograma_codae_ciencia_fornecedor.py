from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = (
        "pre_recebimento_email_alteracao_cronograma_codae_ciencia_fornecedor.html"
    )
    hidden_email = None
    fornecedor = "Dornecedor XYZ"
    numero_cronograma = 323232

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "fornecedor": fornecedor,
        "numero_cronograma": numero_cronograma,
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
        f"O Fornecedor <strong>{fornecedor}</strong> deu ciência nas Alterações do Cronograma <strong>Nº {numero_cronograma}</strong>"
        in html
    )
