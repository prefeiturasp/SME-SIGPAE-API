from django.template.loader import render_to_string


def test_template_email_base():
    numero_cronograma = "012/2541"
    nome_produto = "Manga"
    data_evento = "20/11/2025"
    template = "pre_recebimento_notificacao_criacao_cronograma_semanal.html"
    dados_template = {
        "numero_cronograma": numero_cronograma,
        "nome_produto": nome_produto,
        "data_evento": data_evento,
    }
    html = render_to_string(template, context=dados_template)
    assert isinstance(html, str)

    assert "Cronograma Ponto a Ponto 012/2541 - Manga" in html

    assert "foi criado pela CODAE em 20/11/2025" in html

    assert "<strong>" in html

