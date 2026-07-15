import datetime

from django.template.loader import render_to_string


def test_template_email_codae_assinatura_cronograma():
    titulo = "Teste template"
    template = "pre_recebimento_email_assinatura_cronograma_codae.html"
    hidden_email = None
    numero_cronograma = "323232/2026"
    nome_produto = "Arroz"
    nome_usual_fornecedor = "AMcom"
    razao_social_fornecedor = "AMcom LTDA"
    data_assinatura = datetime.datetime(2026, 3, 24, 11, 0, 0)

    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "numero_cronograma": numero_cronograma,
        "nome_produto": nome_produto,
        "nome_usual_fornecedor": nome_usual_fornecedor,
        "razao_social_fornecedor": razao_social_fornecedor,
        "data_assinatura": data_assinatura,
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
        f"A <strong>CODAE</strong> assinou o cronograma n° <strong>{numero_cronograma}</strong> de <strong>{nome_produto}</strong> em 24/03/26, "
        f"do fornecedor <strong>{nome_usual_fornecedor} - {razao_social_fornecedor}</strong>"
        in html
    )
