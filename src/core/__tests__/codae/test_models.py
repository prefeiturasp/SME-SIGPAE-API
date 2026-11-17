import pytest

from ....dados_comuns.constants import (
    DAQUI_A_SETE_DIAS,
    DAQUI_A_TRINTA_DIAS,
    SEM_FILTRO,
)

pytestmark = pytest.mark.django_db


def test_codae(codae):
    assert isinstance(str(codae), str)
    assert codae.inversoes_cardapio_autorizadas is not None
    assert codae.inversoes_cardapio_reprovados is not None
    assert codae.solicitacoes_unificadas_autorizadas is not None
    assert codae.inclusoes_continuas_autorizadas is not None
    assert codae.inclusoes_normais_autorizadas is not None
    assert codae.inclusoes_continuas_reprovadas is not None
    assert codae.inclusoes_normais_reprovadas is not None
    assert codae.solicitacao_kit_lanche_avulsa_autorizadas is not None
    assert codae.solicitacao_kit_lanche_avulsa_reprovadas is not None
    assert codae.alteracoes_cardapio_autorizadas is not None
    assert codae.alteracoes_cardapio_reprovadas is not None

    for filtro in [DAQUI_A_TRINTA_DIAS, DAQUI_A_SETE_DIAS, SEM_FILTRO]:
        assert (
            codae.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(filtro)
            is not None
        )
        assert (
            codae.solicitacoes_kit_lanche_cemei_das_minhas_escolas_a_validar(filtro)
            is not None
        )
        assert codae.solicitacoes_unificadas(filtro) is not None
        assert codae.suspensoes_cardapio_das_minhas_escolas(filtro) is not None
        assert codae.alteracoes_cardapio_das_minhas(filtro) is not None
        assert codae.alteracoes_cardapio_cei_das_minhas(filtro) is not None
        assert codae.alteracoes_cardapio_cemei_das_minhas_escolas(filtro) is not None
        assert (
            codae.inclusoes_alimentacao_continua_das_minhas_escolas(filtro) is not None
        )
        assert codae.inclusoes_alimentacao_cemei_das_minhas_escolas(filtro) is not None
        assert (
            codae.grupos_inclusoes_alimentacao_normal_das_minhas_escolas(filtro)
            is not None
        )
        assert codae.inversoes_cardapio_das_minhas_escolas(filtro) is not None
