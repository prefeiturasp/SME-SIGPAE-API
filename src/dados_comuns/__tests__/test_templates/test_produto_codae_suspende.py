from django.template.loader import render_to_string
from model_bakery import baker


def test_template_email_base():
    titulo = "Teste template"
    template = "produto_codae_suspende.html"
    hidden_email = None
    produto = baker.make(
        "Produto", nome="maça", marca=baker.make("Marca", nome="Turma da Mônica")
    )

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "produto": produto,
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
        f"Informo que o produto {produto.nome} - {produto.marca.nome} foi suspenso."
        in html
    )
