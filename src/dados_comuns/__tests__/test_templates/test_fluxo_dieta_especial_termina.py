from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "fluxo_dieta_especial_termina.html"
    hidden_email = None
    eol_aluno = 123456
    nome_aluno = "Paulo Pedro"
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "eol_aluno": eol_aluno,
        "nome_aluno": nome_aluno,
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
        f"A dieta especial do aluno {eol_aluno} - {nome_aluno} foi cancelada automaticamente\n    por término de vigência"
        in html
    )
