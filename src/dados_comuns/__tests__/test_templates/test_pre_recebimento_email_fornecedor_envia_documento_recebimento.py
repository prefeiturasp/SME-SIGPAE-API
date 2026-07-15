from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "pre_recebimento_email_fornecedor_envia_documento_recebimento.html"
    hidden_email = None
    numero_cronograma = 12234
    nome_empresa = "Fornecedor XYZ"
    nome_produto = "maça"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_cronograma": numero_cronograma,
        "nome_empresa": nome_empresa,
        "nome_produto": nome_produto,
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
        f"O Fornecedor <strong>{nome_empresa}</strong> enviou os Documentos de Recebimento referente ao Cronograma <strong>Nº {numero_cronograma}</strong> do Produto <strong>{nome_produto}</strong>"
        in html
    )
