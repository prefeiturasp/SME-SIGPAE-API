import datetime

import pytest
from model_bakery import baker


@pytest.fixture
def log_dietas_ativas_canceladas_automaticamente(
    solicitacao_dieta_especial_autorizada_ativa,
):
    return baker.make(
        "LogDietasAtivasCanceladasAutomaticamente",
        dieta=solicitacao_dieta_especial_autorizada_ativa,
        codigo_eol_aluno="6595803",
        nome_aluno="GUILHERME RODRIGUES DA HORA",
        codigo_eol_escola_origem="019871",
        nome_escola_origem="EMEF PERICLES EUGENIO DA SILVA RAMOS",
        codigo_eol_escola_destino="018210",
        nome_escola_destino="EMEFM DARCY RIBEIRO",
    )


@pytest.fixture
def logs_dieta_recreio_nas_ferias(escola, classificacoes_dietas):

    data = datetime.date(2025, 12, 22)
    for classificacao in classificacoes_dietas:
        baker.make(
            "LogQuantidadeDietasAutorizadasRecreioNasFerias",
            escola=escola,
            quantidade=5,
            classificacao=classificacao,
            data=data,
        )
