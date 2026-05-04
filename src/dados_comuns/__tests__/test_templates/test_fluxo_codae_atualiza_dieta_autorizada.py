from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "fluxo_codae_atualiza_dieta_autorizada.html"
    hidden_email = None
    nome_aluno = "Paulo Pedro"
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
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
    assert "foi atualizado pela NUTRICODAE" in html
    assert nome_aluno in html
