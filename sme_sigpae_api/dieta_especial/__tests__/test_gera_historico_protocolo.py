import pytest

from sme_sigpae_api.dieta_especial.gera_historico_protocolo import (
    _compara_alergias,
    _compara_classificacao,
    _compara_data_de_termino,
    _compara_informacoes_adicionais,
    _compara_orientacoes,
    _compara_protocolo,
    _compara_substituicoes,
    atualiza_historico_protocolo,
    remove_tag_p,
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


def test_compara_informacoes_adicionais(solicitacao_historico_atualizacao_protocolo):
    orientacao = (
        "<p>Caso a criança insira chocolate, levar imediatamente ao hospital.</p>"
    )
    comparacao = _compara_informacoes_adicionais(
        solicitacao_historico_atualizacao_protocolo, orientacao
    )

    assert isinstance(comparacao, dict)
    assert comparacao["de"] == "Nenhuma informção a ser adicionada."
    assert (
        comparacao["para"]
        == "Caso a criança insira chocolate, levar imediatamente ao hospital."
    )


def test_compara_informacoes_adicionais_iguais(
    solicitacao_historico_atualizacao_protocolo,
):
    orientacao = solicitacao_historico_atualizacao_protocolo.informacoes_adicionais
    comparacao = _compara_informacoes_adicionais(
        solicitacao_historico_atualizacao_protocolo, orientacao
    )

    assert comparacao is None


def test_compara_informacoes_adicionais_nao_enviada(
    solicitacao_historico_atualizacao_protocolo,
):
    comparacao = _compara_informacoes_adicionais(
        solicitacao_historico_atualizacao_protocolo, None
    )

    assert comparacao is None


def test_atualiza_historico_protocolo_somente_informacoes_adicionais(
    solicitacao_historico_atualizacao_protocolo, mock_request_codae_atualiza_protocolo
):
    html = atualiza_historico_protocolo(
        solicitacao_historico_atualizacao_protocolo,
        mock_request_codae_atualiza_protocolo,
    )
    assert isinstance(html, str)
    assert "Informações adicionais" in html
    assert "Nenhuma informção a ser adicionada." in html
    assert "Caso a criança insira chocolate, levar imediatamente ao hospital." in html


def test_compara_data_de_termino(solicitacao_historico_atualizacao_protocolo):
    data_termino = "2026-10-25"
    comparacao = _compara_data_de_termino(
        solicitacao_historico_atualizacao_protocolo, data_termino
    )

    assert isinstance(comparacao, dict)
    assert comparacao["de"] == "Sem data término"
    assert comparacao["para"] == "Com data de término 25/10/2026"


def test_compara_data_de_termino_nao_enviada(
    solicitacao_historico_atualizacao_protocolo,
):
    comparacao = _compara_data_de_termino(
        solicitacao_historico_atualizacao_protocolo, None
    )

    assert comparacao is None


def test_atualiza_historico_protocolo_somente_data_termino(
    solicitacao_historico_atualizacao_protocolo, mock_request_codae_atualiza_protocolo
):
    html = atualiza_historico_protocolo(
        solicitacao_historico_atualizacao_protocolo,
        mock_request_codae_atualiza_protocolo,
    )
    assert isinstance(html, str)
    assert "Data de término" in html
    assert "Sem data término" in html
    assert "Com data de término 25/10/2026" in html


def test_compara_substituicoes(
    solicitacao_historico_atualizacao_protocolo,
    substituicao_alimento_dieta,
    adiciona_biscoitos_na_substituicao,
    altera_bolos_na_substituicao,
):
    substituicoes = [adiciona_biscoitos_na_substituicao, altera_bolos_na_substituicao]
    comparacao = _compara_substituicoes(
        solicitacao_historico_atualizacao_protocolo, substituicoes
    )

    assert isinstance(comparacao, dict)
    assert comparacao["incluidos"] == [
        {
            "tipo": "ITEM INCLUÍDO",
            "dados": {
                "alimento": "Biscoito de Chocolate",
                "substitutos": ["Biscoito de Leite com Coco", "Biscoito de Maizena"],
                "tipo": "SUBSTITUIR",
            },
        }
    ]
    assert comparacao["excluidos"] == [
        {
            "tipo": "ITEM EXCLUÍDO",
            "dados": {
                "alimento": "Achocolatado",
                "tipo": "SUBSTITUIR",
                "substitutos": ["Suco de Laranja", "Suco de Morango", "Suco de Uva"],
            },
        }
    ]
    assert comparacao["alterados"] == [
        {
            "tipo": "ITEM ALTERADO",
            "de": {
                "tipo": "ITEM ALTERADO DE",
                "dados": {
                    "alimento": "Bolo de Chocolate",
                    "tipo": "SUBSTITUIR",
                    "substitutos": ["Bolo de Fubá", "Bolo de Laranja"],
                },
            },
            "para": {
                "tipo": "ITEM ALTERADO PARA",
                "dados": {
                    "alimento": "Bolo de Chocolate",
                    "tipo": "SUBSTITUIR",
                    "substitutos": ["Bolo de Fubá", "Bolo de Laranja", "Bolo de Limão"],
                },
            },
        }
    ]


def test_compara_substituicoes_iguais(
    solicitacao_historico_atualizacao_protocolo, substituicao_alimento_dieta
):
    comparacao = _compara_substituicoes(
        solicitacao_historico_atualizacao_protocolo, substituicao_alimento_dieta
    )
    assert comparacao is None


def test_atualiza_historico_protocolo_somente_substituicoes(
    solicitacao_historico_atualizacao_protocolo,
    substituicao_alimento_dieta,
    mock_request_codae_atualiza_protocolo,
):
    html = atualiza_historico_protocolo(
        solicitacao_historico_atualizacao_protocolo,
        mock_request_codae_atualiza_protocolo,
    )

    assert isinstance(html, str)
    assert "Substituições de Alimentos" in html
    assert html.count("SUBSTITUIR") == 4
    assert html.count("ISENTO") == 0

    assert "ITEM EXCLUÍDO" in html
    assert "Achocolatado" in html
    assert "<li> Suco de Laranja</li>" in html
    assert "<li> Suco de Morango</li>" in html
    assert "<li> Suco de Uva</li>" in html

    assert "ITEM INCLUIDO" in html
    assert "Biscoito de Chocolate" in html
    assert "<li> Biscoito de Leite com Coco</li>" in html
    assert "<li> Biscoito de Maizena</li>" in html

    assert "ITEM ALTERADO DE" in html
    assert "ITEM ALTERADO PARA" in html
    assert "Bolo de Chocolate" in html
    assert html.count("<li> Bolo de Fubá</li>") == 2
    assert html.count("<li> Bolo de Laranja</li>") == 2
    assert html.count("<li> Bolo de Limão</li>") == 1


def test_remove_tag_p():
    html = "<p>A criança tem alergia ao cacau 70%.</p><p>Ao inserir esse alimento, a pele fica irritada.</p>"
    novo_html = remove_tag_p(html)
    assert (
        novo_html
        == "A criança tem alergia ao cacau 70%.<p>Ao inserir esse alimento, a pele fica irritada.</p>"
    )


def test_remove_tag_p_texto_sem_tag():
    html = "A criança tem alergia ao cacau 70%."
    novo_html = remove_tag_p(html)
    assert novo_html == "A criança tem alergia ao cacau 70%."


def test_remove_tag_p_texto_com_tag_de_lista():
    html = "<p>A criança tem alergia ao cacau 70%.</p><p>Ao inserir esse alimento, a pele fica irritada.</p><ul><li>Não passar nenhuma pomada sem ser recomendada pelo médico</li></ul>"
    novo_html = remove_tag_p(html)
    assert (
        novo_html
        == "<p>A criança tem alergia ao cacau 70%.</p><p>Ao inserir esse alimento, a pele fica irritada.</p><ul><li>Não passar nenhuma pomada sem ser recomendada pelo médico</li></ul>"
    )


def test_remove_tag_p_texto_com_tag_de_tabela():
    html = "<p>A criança tem alergia ao cacau 70%.</p><p>Ao inserir esse alimento, a pele fica irritada.</p><table><tr><td>Não passar nenhuma pomada sem ser recomendada pelo médico</td></tr></table>"
    novo_html = remove_tag_p(html)
    assert (
        novo_html
        == "<p>A criança tem alergia ao cacau 70%.</p><p>Ao inserir esse alimento, a pele fica irritada.</p><table><tr><td>Não passar nenhuma pomada sem ser recomendada pelo médico</td></tr></table>"
    )
