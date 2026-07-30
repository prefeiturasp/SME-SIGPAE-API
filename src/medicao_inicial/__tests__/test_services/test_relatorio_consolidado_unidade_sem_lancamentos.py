import math
from io import BytesIO

import openpyxl
import pandas as pd
import pytest

from src.escola.models import PeriodoEscolar
from src.medicao_inicial.models import CategoriaMedicao
from src.medicao_inicial.services.relatorio_consolidado_emei_emef import (
    _calcula_soma_medicao,
    _define_filtro,
    _get_lista_alimentacoes,
    _get_lista_alimentacoes_dietas,
    _get_total_pagamento,
    _processa_periodo_campo,
    _sort_and_merge,
    _total_pagamento_emef,
    _total_pagamento_emei,
    _unificar_dietas_tipo_a,
    ajusta_layout_tabela,
    get_alimentacoes_por_periodo,
    get_solicitacoes_ordenadas,
    get_valores_tabela,
    insere_tabela_periodos_na_planilha,
    processa_dieta_especial,
    processa_periodo_regular,
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

