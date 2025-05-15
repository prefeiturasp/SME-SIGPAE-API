from sme_sigpae_api.cardapio.base.models import (
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.escola.models import PeriodoEscolar, TipoUnidadeEscolar
from utility.carga_dados.escola.helper import printa_pontinhos


def vincula_tipo_alimentcao():
    tipos_alimentacao = TipoAlimentacao.objects.all()
    for periodo in PeriodoEscolar.objects.all():
        periodo.tipos_alimentacao.set(tipos_alimentacao)


def vincula_tipo_unidade_escolar_periodo_escolar_combo_vazio():
    tipos_unidade_escolar = TipoUnidadeEscolar.objects.all()
    for tipo_ue in tipos_unidade_escolar:
        for periodo_escolar in tipo_ue.periodos_escolares.all():
            (
                vinculo,
                created,
            ) = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get_or_create(
                tipo_unidade_escolar=tipo_ue, periodo_escolar=periodo_escolar
            )


vincula_tipo_alimentcao()
vincula_tipo_unidade_escolar_periodo_escolar_combo_vazio()
printa_pontinhos()
