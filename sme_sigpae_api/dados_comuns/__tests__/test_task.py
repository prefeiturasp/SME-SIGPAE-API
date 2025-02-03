import uuid

from sme_sigpae_api.dados_comuns.tasks import envia_email_unico_task


def test_envia_email_unico_task(reclamacao_produto_codae_recusou, dados_html):
    _, reclamacao_produto = reclamacao_produto_codae_recusou

    assunto = "[SIGPAE] Reclamação Analisada"
    email = reclamacao_produto.criado_por.email
    corpo = ""

    resultado = envia_email_unico_task.delay(
        assunto=assunto,
        email=email,
        corpo=corpo,
        html=dados_html,
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True

    resultado = envia_email_unico_task(
        assunto=assunto,
        email=email,
        corpo=corpo,
        html=dados_html,
    )
    assert bool(resultado) is True


def test_envia_email_unico_task_erro(dados_html):
    assunto = "[SIGPAE] Reclamação Analisada"
    email = {}
    corpo = ""

    resultado = envia_email_unico_task.delay(
        assunto=assunto,
        email=email,
        corpo=corpo,
        html=dados_html,
    )
    assert resultado.status == "SUCCESS"
    assert resultado.id == resultado.task_id
    assert isinstance(resultado.task_id, str)
    assert isinstance(uuid.UUID(resultado.task_id), uuid.UUID)
    assert isinstance(resultado.id, str)
    assert isinstance(uuid.UUID(resultado.id), uuid.UUID)
    assert resultado.ready() is True
    assert resultado.successful() is True

    resultado = envia_email_unico_task(
        assunto=assunto,
        email=email,
        corpo=corpo,
        html=dados_html,
    )
    assert bool(resultado) is False
