from django.template.loader import render_to_string


def test_template_email_base():
    numero_cronograma = "012/2541"
    titulo = f"Cronograma Criado: Nº {numero_cronograma}"
    template = "pre_recebimento_email_criacao_cronograma_semanal.html"
    hidden_email = False
    data_evento = "20/11/2025"
    url_detalhe_cronograma = "https:test.br/pre-recebimento/detalhe-cronograma-semanal?uuid=7f67f203-f0f3-4d7d-9543-f3e29b465651"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_cronograma": numero_cronograma,
        "data_evento": data_evento,
        "url_detalhe_cronograma": url_detalhe_cronograma,
    }
    html = render_to_string(template, context=dados_template)
    assert isinstance(html, str)

    assert "<title>SIGPAE - Notificação</title>" in html
    assert f"<b>{titulo}</b>" in html
    assert (
        'src="https://hom-sigpae.sme.prefeitura.sp.gov.br/django_static/images/email/email-sigpae.png'
        in html
    )
    assert (
        f"Olá! A <strong>CODAE</strong> criou o Cronograma <strong> Nº {numero_cronograma}</strong> em {data_evento}: "
        in html
    )

    assert (
        f"""<a href="{url_detalhe_cronograma}">Clique aqui para acessar o cronograma</a>"""
        in html
    )
    assert "<p>smecodaesigpae@sme.prefeitura.sp.gov.br</p>" in html


def test_template_email_base_hidden_email_true():
    numero_cronograma = "012/2541"
    titulo = f"Cronograma Criado: Nº {numero_cronograma}"
    template = "pre_recebimento_email_criacao_cronograma_semanal.html"
    hidden_email = True
    data_evento = "20/11/2025"
    url_detalhe_cronograma = "https:test.br/pre-recebimento/detalhe-cronograma-semanal?uuid=7f67f203-f0f3-4d7d-9543-f3e29b465651"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_cronograma": numero_cronograma,
        "data_evento": data_evento,
        "url_detalhe_cronograma": url_detalhe_cronograma,
    }
    html = render_to_string(template, context=dados_template)
    assert isinstance(html, str)

    assert "<title>SIGPAE - Notificação</title>" in html
    assert f"<b>{titulo}</b>" in html
    assert (
        'src="https://hom-sigpae.sme.prefeitura.sp.gov.br/django_static/images/email/email-sigpae.png'
        in html
    )
    assert (
        f"Olá! A <strong>CODAE</strong> criou o Cronograma <strong> Nº {numero_cronograma}</strong> em {data_evento}: "
        in html
    )

    assert (
        f"""<a href="{url_detalhe_cronograma}">Clique aqui para acessar o cronograma</a>"""
        in html
    )
    assert "<p>smecodaesigpae@sme.prefeitura.sp.gov.br</p>" not in html
