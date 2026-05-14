from src.cardapio.alteracao_tipo_alimentacao.models import (
    MotivoAlteracaoCardapio,
)
from src.cardapio.base.models import (
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from src.escola.models import PeriodoEscolar, TipoUnidadeEscolar
from utility.carga_dados.cardapio.data.motivos_alteracao_cardapio import (
    data_motivoalteracaocardapio,
)
from utility.carga_dados.cardapio.data.motivos_suspensao_alimentacao import (
    data_motivosuspensao,
)
from utility.carga_dados.cardapio.data.tipo_alimentacao import data_tipo_alimentacao
from utility.carga_dados.helper import ja_existe, progressbar


def cria_motivoalteracaocardapio():
    for item in progressbar(
        data_motivoalteracaocardapio, "Motivo Alteracao Cardapio"
    ):  # noqa
        _, created = MotivoAlteracaoCardapio.objects.get_or_create(nome=item)
        if not created:
            ja_existe("MotivoAlteracaoCardapio", item)


def cria_motivosuspensao():
    for item in progressbar(data_motivosuspensao, "Motivo Suspensao"):
        _, created = MotivoSuspensao.objects.get_or_create(nome=item)
        if not created:
            ja_existe("MotivoSuspensao", item)


def cria_tipo_alimentacao():
    for item in progressbar(data_tipo_alimentacao, "Tipo Alimentacao"):
        _, created = TipoAlimentacao.objects.get_or_create(nome=item)
        if not created:
            ja_existe("TipoAlimentacao", item)


def cria_vinculo_tipo_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar():
    # Percorre todos os tipos de unidade escolar e todos os periodos escolares.
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.all().delete()  # noqa
    tipo_unidade_escolares = TipoUnidadeEscolar.objects.all()
    periodo_escolares = PeriodoEscolar.objects.all()
    aux = []
    for tipo_unidade_escolar in progressbar(
        tipo_unidade_escolares,
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
    ):  # noqa
        for periodo_escolar in periodo_escolares:
            obj = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar(
                tipo_unidade_escolar=tipo_unidade_escolar,
                periodo_escolar=periodo_escolar,
            )
            aux.append(obj)
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.bulk_create(
        aux
    )  # noqa
