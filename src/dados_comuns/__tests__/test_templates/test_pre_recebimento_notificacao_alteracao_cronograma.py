from django.template.loader import render_to_string


def test_template_email_base():
    titulo = "Teste template"
    template = "pre_recebumento_notificacao_alteracao_cronograma.html"
    hidden_email = None
    solicitacao = 12234
    usuario = "ADMINISTRADOR CODAE"
    nome_produto = "Arroz Tipo 1"

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "solicitacao": solicitacao,
        "usuario": usuario,
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
        f"O Fornecedor <strong>{usuario}</strong> Solicitou Alterações no Cronograma <strong>{solicitacao}</strong> de <strong>{nome_produto}</strong>"
        in html
    )
