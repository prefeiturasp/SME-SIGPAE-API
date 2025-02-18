from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "pre_recebimento_email_fornecedor_envia_layout_embalagem.html"
    hidden_email = None
    numero_ficha = 12234
    nome_empresa = "Fornecedor XYZ"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_ficha": numero_ficha,
        "nome_empresa": nome_empresa,
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
        f"O fornecedor <strong>{nome_empresa}</strong> enviou o Layout de Embalagens referente a Ficha Técnica <strong>{numero_ficha}</strong>"
        in html
    )
