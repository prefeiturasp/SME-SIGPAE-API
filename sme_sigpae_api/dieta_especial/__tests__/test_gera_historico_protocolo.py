import pytest

from sme_sigpae_api.dieta_especial.gera_historico_protocolo import (
    _compara_alergias,
    _compara_classificacao,
    _compara_orientacoes,
    _compara_protocolo,
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


def test_compara_classificacao_iguais(
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


def test_compara_protocolo(
    solicitacao_historico_atualizacao_protocolo,
    protocolo_padrao_dieta_especial,
    protocolo_padrao_dieta_especial_2,
):
    novo_protocolo = str(protocolo_padrao_dieta_especial_2.uuid)
    comparacao = _compara_protocolo(
        solicitacao_historico_atualizacao_protocolo, novo_protocolo
    )

    assert isinstance(comparacao, dict)
    assert comparacao["de"] == protocolo_padrao_dieta_especial.nome_protocolo
    assert comparacao["para"] == protocolo_padrao_dieta_especial_2.nome_protocolo


def test_compara_protocolo_iguais(
    solicitacao_historico_atualizacao_protocolo, protocolo_padrao_dieta_especial
):
    novo_protocolo = str(protocolo_padrao_dieta_especial.uuid)
    comparacao = _compara_protocolo(
        solicitacao_historico_atualizacao_protocolo, novo_protocolo
    )

    assert comparacao is None


def test_compara_protocolo_nao_enviado(solicitacao_historico_atualizacao_protocolo):
    comparacao = _compara_protocolo(solicitacao_historico_atualizacao_protocolo, None)

    assert comparacao is None


def test_atualiza_historico_protocolo_somente_protocolo(
    solicitacao_historico_atualizacao_protocolo, mock_request_codae_atualiza_protocolo
):
    html = atualiza_historico_protocolo(
        solicitacao_historico_atualizacao_protocolo,
        mock_request_codae_atualiza_protocolo,
    )
    assert isinstance(html, str)
    assert "Nome do Protocolo Padrão" in html
    assert "ALERGIA A AVEIA" in html
    assert "ALERGIA A ABACAXI" in html


def test_compara_orientacoes(solicitacao_historico_atualizacao_protocolo):
    orientacao = "<p>A criança tem alergia ao cacau 70%.</p>"
    comparacao = _compara_orientacoes(
        solicitacao_historico_atualizacao_protocolo, orientacao
    )

    assert isinstance(comparacao, dict)
    assert comparacao["de"] == "A criança tem alergia ao cacau"
    assert comparacao["para"] == "A criança tem alergia ao cacau 70%."


def test_compara_orientacoes_iguais(solicitacao_historico_atualizacao_protocolo):
    orientacao = solicitacao_historico_atualizacao_protocolo.orientacoes_gerais
    comparacao = _compara_orientacoes(
        solicitacao_historico_atualizacao_protocolo, orientacao
    )

    assert comparacao is None


def test_compara_orientacoes_nao_enviada(solicitacao_historico_atualizacao_protocolo):
    comparacao = _compara_orientacoes(solicitacao_historico_atualizacao_protocolo, None)

    assert comparacao is None


def test_atualiza_historico_protocolo_somente_orientacoes_gerais(
    solicitacao_historico_atualizacao_protocolo, mock_request_codae_atualiza_protocolo
):
    html = atualiza_historico_protocolo(
        solicitacao_historico_atualizacao_protocolo,
        mock_request_codae_atualiza_protocolo,
    )
    assert isinstance(html, str)
    assert "Orientações Gerais" in html
    assert "A criança tem alergia ao cacau" in html
    assert "A criança tem alergia ao cacau 70%." in html
