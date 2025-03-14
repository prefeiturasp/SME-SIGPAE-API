from unittest.mock import patch

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError

from sme_sigpae_api.eol_servico.utils import EOLException
from sme_sigpae_api.logistica.api.soup.models import SoapResponse
from sme_sigpae_api.logistica.api.soup.views import (
    SolicitacaoService,
    _method_return_string,
)

pytestmark = pytest.mark.django_db


def test_solicitacao_criacao(arq_solicitacao_mod, token_valido):
    _, _, model = token_valido
    resposta = SolicitacaoService.Solicitacao(None, model, arq_solicitacao_mod)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "true"
    assert resposta.StrMensagem == "Solicitação criada com sucesso."


def test_solicitacao_falha_autenticacao(arq_solicitacao_mod, token_valido):
    usuario, _, _ = token_valido
    resposta = SolicitacaoService.Solicitacao(None, usuario, arq_solicitacao_mod)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "false"
    assert resposta.StrMensagem == "Falha na autenticação. StrToken não foi informado."


def test_solicitacao_falha_objeto_inexistente(token_valido, soup_arq_solicitacao_mod):
    _, _, model = token_valido
    resposta = SolicitacaoService.Solicitacao(None, model, soup_arq_solicitacao_mod)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "false"
    assert resposta.StrMensagem == "Não existe distribuidor cadastrado com esse cnpj"


def test_solicitacao_falha_integridade(token_valido, arq_solicitacao_mod):
    _, _, model = token_valido
    SolicitacaoService.Solicitacao(None, model, arq_solicitacao_mod)
    resposta = SolicitacaoService.Solicitacao(None, model, arq_solicitacao_mod)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "false"
    assert "Solicitação duplicada" in resposta.StrMensagem


def test_solicitacao_exception(token_valido):
    _, _, model = token_valido
    resposta = SolicitacaoService.Solicitacao(None, model, "arq_solicitacao_mod")
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "false"
    assert (
        "Houve um erro ao salvar a solicitação: 'str' object has no attribute 'create'"
    )


def test_cancelamento_sucesso(token_valido, arq_cancelamento_mod):
    _, _, model = token_valido
    resposta = SolicitacaoService.Cancelamento(None, model, arq_cancelamento_mod)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "canc"
    assert resposta.StrMensagem == "Cancelamento realizado com sucesso"


def test_cancelamento_falha_autenticacao(token_valido, arq_cancelamento_mod):
    usuario, _, _ = token_valido
    resposta = SolicitacaoService.Cancelamento(None, usuario, arq_cancelamento_mod)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "false"
    assert resposta.StrMensagem == "Falha na autenticação. StrToken não foi informado."


def test_cancelamento_falha_objeto_inexistente(token_valido, soup_arq_cancelamento):
    _, _, model = token_valido
    resposta = SolicitacaoService.Cancelamento(None, model, soup_arq_cancelamento)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "false"
    assert (
        resposta.StrMensagem
        == f"Solicitacão {soup_arq_cancelamento.StrNumSol} não encontrada."
    )


def test_cancelamento_pendente(token_valido, arq_cancelamento_mod):
    _, _, model = token_valido
    SolicitacaoService.Cancelamento(None, model, arq_cancelamento_mod)
    resposta = SolicitacaoService.Cancelamento(None, model, arq_cancelamento_mod)
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "pend"
    assert (
        resposta.StrMensagem
        == "Solicitação de cancelamento recebida com sucesso. Pendente de confirmação do distribuidor"
    )


def test_cancelamento_exception(token_valido):
    _, _, model = token_valido
    resposta = SolicitacaoService.Cancelamento(None, model, "arq_cancelamento_mod")
    assert isinstance(resposta, SoapResponse)
    assert resposta.StrStatus == "false"
    assert (
        resposta.StrMensagem
        == "Houve um erro ao receber a solicitação de cancelamento: 'str' object has no attribute 'cancel'"
    )


def test_method_return_string(mock_ctx):
    _method_return_string(mock_ctx)
    assert b"tns:" not in mock_ctx.out_string[0]
    assert b"soap11env" not in mock_ctx.out_string[0]
    assert b"soap" in mock_ctx.out_string[0]
    assert mock_ctx.out_string == [b"<Test>soap:Body</Test>"]
