from sme_sigpae_api.recebimento.data.reposicao_cronograma import data_reposicao_cronograma
from sme_sigpae_api.recebimento.models import ReposicaoCronogramaFichaRecebimento
from utility.carga_dados.helper import ja_existe, progressbar


def cria_reposicao_cronograma_ficha_recebimento():
    for item in progressbar(
        data_reposicao_cronograma, "Reposicao Cronograma Ficha Recebimento"
    ):
        _, created = ReposicaoCronogramaFichaRecebimento.objects.get_or_create(
            tipo=item["tipo"],
            descricao=item["descricao"],
        )
        if not created:
            ja_existe("ReposicaoCronogramaFichaRecebimento", item)
