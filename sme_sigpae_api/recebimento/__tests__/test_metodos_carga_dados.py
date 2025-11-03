import pytest

from sme_sigpae_api.recebimento.models import ReposicaoCronogramaFichaRecebimento
from utility.carga_dados.recebimento.importa_dados import (
    cria_reposicao_cronograma_ficha_recebimento,
)


@pytest.mark.django_db
def test_cria_reposicao_cronograma_ficha_recebimento():
    ReposicaoCronogramaFichaRecebimento.objects.all().delete()
    assert ReposicaoCronogramaFichaRecebimento.objects.count() == 0
    cria_reposicao_cronograma_ficha_recebimento()
    assert ReposicaoCronogramaFichaRecebimento.objects.count() == 2
