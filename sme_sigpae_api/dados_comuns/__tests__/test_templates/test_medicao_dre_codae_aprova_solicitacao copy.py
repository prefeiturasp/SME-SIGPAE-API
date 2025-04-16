from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "medicao_dre_codae_aprova_solicitacao.html"
    hidden_email = None
    mes = 2
    ano = 2025
    usuario = "ADMINISTRADOR CODAE"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "mes": mes,
        "ano": ano,
        "usuario": usuario,
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
        f"A Medição Inicial referente à <strong>{mes} / {ano}</strong> foi aprovada pela {usuario}"
        in html
    )
