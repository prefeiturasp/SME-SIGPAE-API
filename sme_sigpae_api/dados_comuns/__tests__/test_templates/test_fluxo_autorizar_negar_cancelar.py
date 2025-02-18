from django.template.loader import render_to_string

from sme_sigpae_api.dados_comuns.templatetags.email_templatetags import (
    traduz_movimentacao,
)


def test_template_email_base():
    titulo = "Teste template"
    template = "fluxo_autorizar_negar_cancelar.html"
    hidden_email = None
    tipo_solicitacao = "inclusao de alimentacao"
    movimentacao_realizada = "ESCOLA_CANCELOU"
    perfil_que_autorizou = "Codae"
    dados_template = {
        "titulo": titulo,
        "hidden_email": hidden_email,
        "tipo_solicitacao": tipo_solicitacao,
        "movimentacao_realizada": movimentacao_realizada,
        "perfil_que_autorizou": perfil_que_autorizou,
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
        f"A solicitação de {tipo_solicitacao} <strong>{traduz_movimentacao(movimentacao_realizada)}</strong> por {perfil_que_autorizou}"
        in html
    )
