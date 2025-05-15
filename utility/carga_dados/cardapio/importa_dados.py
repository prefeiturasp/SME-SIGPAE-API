from random import randint, sample

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.base.models import (
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE,
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.cardapio.suspensao_alimentacao.models import MotivoSuspensao
from sme_sigpae_api.escola.models import PeriodoEscolar, TipoUnidadeEscolar
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


def cria_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue():
    ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all().delete()
    vinculos = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.all()
    tipos_alimentacoes = list(TipoAlimentacao.objects.all())
    for vinculo in progressbar(vinculos, "ComboDoVinculoTipoAlimentacaoPeriodoTipoUE"):
        # Cria vários combos para cada vinculo.
        for _ in range(randint(5, 10)):
            obj = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.create(
                vinculo=vinculo
            )
            tipos_amostra = sample(tipos_alimentacoes, randint(1, 3))
            for item in tipos_amostra:
                obj.tipos_alimentacao.add(item)
        # Cria um combo específico para lanche e outro para refeição.
        tipos_alimentacoes2 = list(
            TipoAlimentacao.objects.filter(nome__in=("lanche", "refeição"))
        )
        for tipo in tipos_alimentacoes2:
            obj = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.create(
                vinculo=vinculo
            )
            obj.tipos_alimentacao.add(tipo)


def cria_substituicao_do_combo_do_vinculo_tipo_alimentacao_periodo_tipo_ue():
    SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all().delete()
    combos = ComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.all()
    tipos_alimentacoes = list(
        TipoAlimentacao.objects.exclude(nome__in=("lanche", "refeição"))
    )
    for combo in progressbar(
        combos, "SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE"
    ):
        obj = SubstituicaoDoComboDoVinculoTipoAlimentacaoPeriodoTipoUE.objects.create(
            combo=combo
        )
        tipos_amostra = sample(tipos_alimentacoes, randint(1, 3))
        tipos_alimentacao_list = [
            item[1] for item in combo.tipos_alimentacao.values_list()
        ]
        for item in tipos_amostra:
            if len(tipos_alimentacao_list) == 1 and "lanche" in tipos_alimentacao_list:
                refeicao = TipoAlimentacao.objects.filter(nome="refeição").first()
                obj.tipos_alimentacao.add(refeicao)
            elif (
                len(tipos_alimentacao_list) == 1
                and "refeição" in tipos_alimentacao_list
            ):
                lanche = TipoAlimentacao.objects.filter(nome="lanche").first()
                obj.tipos_alimentacao.add(lanche)
            else:
                obj.tipos_alimentacao.add(item)
