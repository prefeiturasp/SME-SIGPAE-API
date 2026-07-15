from src.inclusao_alimentacao.data.motivo_inclusao_continua import (
    data_motivo_inclusao_continua,
)
from src.inclusao_alimentacao.data.motivo_inclusao_normal import (
    data_motivo_inclusao_normal,
)
from src.inclusao_alimentacao.models import (
    MotivoInclusaoContinua,
    MotivoInclusaoNormal,
)
from utility.carga_dados.helper import ja_existe, progressbar


def cria_motivo_inclusao_continua():
    for item in progressbar(
        data_motivo_inclusao_continua, "Motivo Inclusao Continua"
    ):  # noqa
        _, created = MotivoInclusaoContinua.objects.get_or_create(nome=item)
        if not created:
            ja_existe("MotivoInclusaoContinua", item)


def cria_motivo_inclusao_normal():
    for item in progressbar(
        data_motivo_inclusao_normal, "Motivo Inclusao Normal"
    ):  # noqa
        _, created = MotivoInclusaoNormal.objects.get_or_create(nome=item)
        if not created:
            ja_existe("MotivoInclusaoNormal", item)
