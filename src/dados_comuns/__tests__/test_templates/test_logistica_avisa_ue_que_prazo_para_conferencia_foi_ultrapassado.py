from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "logistica_avisa_ue_que_prazo_para_conferencia_foi_ultrapassado.html"
    hidden_email = None
    numero_guia = "12548"
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_guia": numero_guia,
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
        f"A Guia de Remessa <b>Nº {numero_guia}</b>, com data de entrega prevista"
        in html
    )
