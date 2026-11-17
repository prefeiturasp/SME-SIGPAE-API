import pytest

from ....dados_comuns.constants import (
    DAQUI_A_SETE_DIAS,
    DAQUI_A_TRINTA_DIAS,
    SEM_FILTRO,
)

pytestmark = pytest.mark.django_db


def test_diretoria_regional(diretoria_regional, escola):
    assert isinstance(str(diretoria_regional), str)
    assert diretoria_regional.nome is not None
    assert diretoria_regional.escolas is not None
    assert escola in diretoria_regional.escolas.all()

    assert diretoria_regional.inclusoes_normais_autorizadas is not None
    assert diretoria_regional.inclusoes_continuas_reprovadas is not None
    assert diretoria_regional.inclusoes_normais_reprovadas is not None
    assert (
        diretoria_regional.alteracoes_cardapio_pendentes_das_minhas_escolas is not None
    )
    assert diretoria_regional.alteracoes_cardapio_autorizadas is not None
    assert diretoria_regional.solicitacao_kit_lanche_avulsa_autorizadas is not None
    assert diretoria_regional.solicitacao_kit_lanche_avulsa_reprovados is not None
    assert diretoria_regional.alteracoes_cardapio_reprovadas is not None
    assert diretoria_regional.inversoes_cardapio_autorizadas is not None
    assert diretoria_regional.inversoes_cardapio_reprovados is not None
    assert diretoria_regional.inclusoes_continuas_autorizadas is not None

    for filtro in [DAQUI_A_TRINTA_DIAS, DAQUI_A_SETE_DIAS, SEM_FILTRO]:
        assert (
            diretoria_regional.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(
                filtro
            )
            is not None
        )
        assert (
            diretoria_regional.solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(
                filtro
            )
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_das_minhas_escolas_a_validar(filtro)
            is not None
        )
        assert (
            diretoria_regional.inclusoes_alimentacao_continua_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.inclusoes_alimentacao_cemei_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_cei_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.alteracoes_cardapio_cemei_das_minhas_escolas(filtro)
            is not None
        )
        assert (
            diretoria_regional.inversoes_cardapio_das_minhas_escolas(filtro) is not None
        )
