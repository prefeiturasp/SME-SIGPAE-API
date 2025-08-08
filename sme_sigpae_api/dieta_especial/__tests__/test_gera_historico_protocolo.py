import pytest

from sme_sigpae_api.dieta_especial.gera_historico_protocolo import (
    _compara_alergias,
    _compara_classificacao,
    atualiza_historico_protocolo,
)

pytestmark = pytest.mark.django_db


def test_compara_alergias(
    solicitacao_historico_atualizacao_protocolo, alergia_ao_trigo, alergia_a_chocolate
):
    novas_alergias = [str(alergia_ao_trigo.id)]
    comparacao = _compara_alergias(
        solicitacao_historico_atualizacao_protocolo, novas_alergias
    )

    assert isinstance(comparacao, dict)
    assert comparacao["de"] == alergia_a_chocolate.descricao
    assert comparacao["para"] == alergia_ao_trigo.descricao


def test_compara_alergias_iguais(
    solicitacao_historico_atualizacao_protocolo, alergia_a_chocolate
):
    novas_alergias = [str(alergia_a_chocolate.id)]
    comparacao = _compara_alergias(
        solicitacao_historico_atualizacao_protocolo, novas_alergias
    )
    assert comparacao is None


def test_compara_alergias_alergia_nao_enviada(
    solicitacao_historico_atualizacao_protocolo,
):
    comparacao = _compara_alergias(solicitacao_historico_atualizacao_protocolo, None)
    assert comparacao is None


def test_atualiza_historico_protocolo_somente_alergia(
    solicitacao_historico_atualizacao_protocolo, mock_request_codae_atualiza_protocolo
):
    html = atualiza_historico_protocolo(
        solicitacao_historico_atualizacao_protocolo,
        mock_request_codae_atualiza_protocolo,
    )
    assert isinstance(html, str)
    assert "Relação por Diagnóstico" in html
    assert "Alergia a chocolate" in html
    assert "Alergia a derivados do trigo" in html


def test_compara_classificacao(
    solicitacao_historico_atualizacao_protocolo,
    classificacao_tipo_b,
    classificacao_tipo_a,
):
    nova_classificacao = str(classificacao_tipo_b.id)
    comparacao = _compara_classificacao(
        solicitacao_historico_atualizacao_protocolo, nova_classificacao
    )

    assert isinstance(comparacao, dict)
    assert comparacao["de"] == classificacao_tipo_a.nome
    assert comparacao["para"] == classificacao_tipo_b.nome


def test_compara_classificacao(
    solicitacao_historico_atualizacao_protocolo, classificacao_tipo_a
):
    nova_classificacao = str(classificacao_tipo_a.id)
    comparacao = _compara_classificacao(
        solicitacao_historico_atualizacao_protocolo, nova_classificacao
    )

    assert comparacao is None


def test_compara_classificacao_nao_enviada(solicitacao_historico_atualizacao_protocolo):
    comparacao = _compara_classificacao(
        solicitacao_historico_atualizacao_protocolo, None
    )

    assert comparacao is None


def test_atualiza_historico_protocolo_somente_classificacao(
    solicitacao_historico_atualizacao_protocolo, mock_request_codae_atualiza_protocolo
):
    html = atualiza_historico_protocolo(
        solicitacao_historico_atualizacao_protocolo,
        mock_request_codae_atualiza_protocolo,
    )
    assert isinstance(html, str)
    assert "Classificação da Dieta" in html
    assert "Tipo A" in html
    assert "Tipo B" in html
