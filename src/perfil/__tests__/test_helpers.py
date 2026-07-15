from ..api.helpers import ofuscar_email


def test_hide_email(email_list):
    email, esperado = email_list
    assert ofuscar_email(email) == esperado
