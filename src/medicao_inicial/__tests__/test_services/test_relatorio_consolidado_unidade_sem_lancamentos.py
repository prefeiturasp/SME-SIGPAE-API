import pytest

from src.medicao_inicial.services.relatorio_consolidado_emei_emef import (
    get_alimentacoes_por_periodo,
    get_valores_tabela,
)

pytestmark = pytest.mark.django_db


def test_get_alimentacoes_por_periodo(solicitacao_sem_lancamento):
    colunas = get_alimentacoes_por_periodo([solicitacao_sem_lancamento])
    assert isinstance(colunas, list)
    assert len(colunas) == 2
    assert sum(1 for tupla in colunas if tupla[0] == "MANHA") == 2
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO A") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "DIETA ESPECIAL - TIPO B") == 0
    assert sum(1 for tupla in colunas if tupla[0] == "Solicitações de Alimentação") == 0

    assert sum(1 for tupla in colunas if tupla[1] == "kit_lanche") ==0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_emergencial") ==0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "lanche_4h") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "refeicao") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "sobremesa") == 0
    assert sum(1 for tupla in colunas if tupla[1] == "total_refeicoes_pagamento") == 1
    assert sum(1 for tupla in colunas if tupla[1] == "total_sobremesas_pagamento") == 1


def test_get_valores_tabela_unidade_emei(
    solicitacao_sem_lancamento
):
    colunas    = [('MANHA', 'total_refeicoes_pagamento'), ('MANHA', 'total_sobremesas_pagamento')]
    tipos_unidade = ["EMEI"]
    linhas = get_valores_tabela(
        [solicitacao_sem_lancamento], colunas, tipos_unidade, {}
    )
    assert isinstance(linhas, list)
    assert len(linhas) == 1
    assert isinstance(linhas[0], list)
    assert len(linhas[0]) == 5
    assert linhas[0] == ['EMEF', '123456', 'EMEF TESTE', 'SL', 'SL']