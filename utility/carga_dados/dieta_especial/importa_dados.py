from secrets import choice

from sme_sigpae_api.dieta_especial.data.alergia_intolerancia import (
    data_alergia_intolerancias,
)
from sme_sigpae_api.dieta_especial.data.alimentos import data_alimentos
from sme_sigpae_api.dieta_especial.data.alimentos_proprios_codae import (
    data_alimentos_proprios_codae,
)
from sme_sigpae_api.dieta_especial.data.classificacao_dieta import (
    data_classificacoes_dieta,
)
from sme_sigpae_api.dieta_especial.data.motivo_alteracao_ue import (
    data_motivo_alteracao_ue,
)
from sme_sigpae_api.dieta_especial.data.motivo_negacao import data_motivo_negacoes
from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    AlimentoProprio,
    ClassificacaoDieta,
    MotivoAlteracaoUE,
    MotivoNegacao,
)
from sme_sigpae_api.produto.models import Marca
from utility.carga_dados.escola.helper import bcolors
from utility.carga_dados.helper import ja_existe, progressbar


def cria_alimento():
    for item in progressbar(data_alimentos, "Alimento"):
        _, created = Alimento.objects.get_or_create(nome=item)
        if not created:
            ja_existe("Alimento", item)


def cria_alimento_proprio():
    marcas = Marca.objects.all()
    for item in progressbar(data_alimentos_proprios_codae, "Alimento próprio"):
        marca = choice(marcas)
        _, created = AlimentoProprio.objects.get_or_create(nome=item, marca=marca)
        if not created:
            ja_existe("Alimento próprio", item)


def cria_motivo_negacao():
    for item in progressbar(data_motivo_negacoes, "Motivo Negação"):
        _, created = MotivoNegacao.objects.get_or_create(descricao=item)
        if not created:
            ja_existe("MotivoNegacao", item)


def cria_motivo_alteracao_ue():
    for item in progressbar(data_motivo_alteracao_ue, "Motivo Alteração de UE"):
        _, created = MotivoAlteracaoUE.objects.get_or_create(
            nome=item, descricao="Lorem ipsum."
        )
        if not created:
            ja_existe("MotivoAlteracaoUE", item)


def cria_classificacoes_dieta():
    for item in progressbar(data_classificacoes_dieta, "Classificacao Dieta"):
        _, created = ClassificacaoDieta.objects.get_or_create(
            nome=item["nome"],
            descricao=item["descricao"],
        )
        if not created:
            ja_existe("ClassificacaoDieta", item)


def cria_alergia_intolerancias():
    for item in progressbar(data_alergia_intolerancias, "Alergia Intolerancia"):  # noqa
        obj = AlergiaIntolerancia.objects.filter(descricao=item).first()
        if not obj:
            AlergiaIntolerancia.objects.create(descricao=item)
        else:
            nome = item
            print(
                f'{bcolors.FAIL}Aviso: AlergiaIntolerancia: "{nome}" já existe!{bcolors.ENDC}'
            )  # noqa
