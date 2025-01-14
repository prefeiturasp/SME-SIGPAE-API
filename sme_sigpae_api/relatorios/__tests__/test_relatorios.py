import pytest

from ..relatorios import relatorio_dieta_especial_protocolo


@pytest.mark.django_db
def test_relatorio_dieta_especial_protocolo(solicitacao_dieta_especial_autorizada):
    html_string = relatorio_dieta_especial_protocolo(
        None, solicitacao_dieta_especial_autorizada
    )

    assert ("Orientações Gerais" in html_string) is True
    assert (
        solicitacao_dieta_especial_autorizada.orientacoes_gerais in html_string
    ) is True
