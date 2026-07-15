from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "pre_recebimento_email_fornecedor_envia_layout_embalagem.html"
    hidden_email = None
    numero_ficha = 12234
    nome_empresa = "Fornecedor XYZ"
    razao_social = "Razao Social"
    nome_produto = "ARROZ TIPO 1"
    data_envio = "01/01/2024"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_ficha": numero_ficha,
        "nome_empresa": nome_empresa,
        "razao_social": razao_social,
        "nome_produto": nome_produto,
        "data_envio": data_envio,
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
        f'<p style="margin-bottom: 56px;"><strong>{nome_empresa} - {razao_social}</strong> do <strong>{nome_produto}</strong> em {data_envio} enviou o layout de embalagem referente a Ficha Técnica <strong>{numero_ficha}</strong></p>'
        in html
    )
