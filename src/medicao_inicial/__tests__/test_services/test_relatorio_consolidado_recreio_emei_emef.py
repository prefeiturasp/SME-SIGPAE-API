import pytest

from src.medicao_inicial.services.relatorio_consolidado_recreio_emei_emef import (
    get_alimentacoes_por_periodo,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(solicitacao_recreio_emei):
    colunas = get_alimentacoes_por_periodo([solicitacao_recreio_emei], {})
    assert isinstance(colunas, list)
    assert len(colunas) == 13
    assert sum(1 for tupla in colunas if tupla[0] == "Recreio nas Férias") == 6
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 1
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "Colaboradores") == 6

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 3
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 2
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 2
