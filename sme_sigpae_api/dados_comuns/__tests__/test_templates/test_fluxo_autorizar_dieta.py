from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "fluxo_autorizar_dieta.html"
    hidden_email = None
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
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
    assert "ALERTA DE ATENDIMENTO DE DIETA ESPECIAL CEI POLO/RECREIO NAS FÉRIAS" in html

def test_email_alteracao_ue():
    template = "fluxo_autorizar_dieta.html"
    dados_template = {
        "nome_aluno": "Antônio",
        "codigo_eol_aluno": "145879",
        "data_inicio":"20/05/2024",
        "data_termino":"20/06/2024",
        "unidade_destino": "ESCOLA EMEF JOAO",
    }
    html = render_to_string(template, context=dados_template)
    assert isinstance(html, str)
    assert "ALERTA DE ATENDIMENTO DE DIETA ESPECIAL CEI POLO/RECREIO NAS FÉRIAS" in html
    assert f"Comunicamos que o aluno {dados_template['nome_aluno']} Código EOL {dados_template['codigo_eol_aluno']}" in html
    assert f"período de {dados_template["data_inicio"]}" in html
    assert f"a {dados_template["data_termino"]}" in html
    assert f"férias na {dados_template["unidade_destino"]}" in html