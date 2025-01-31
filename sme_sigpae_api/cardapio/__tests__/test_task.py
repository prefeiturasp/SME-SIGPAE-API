import pytest

from sme_sigpae_api.cardapio.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from sme_sigpae_api.cardapio.tasks import (
    ativa_desativa_vinculos_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar,
    bypass_ativa_vinculos,
)
from sme_sigpae_api.escola.models import (
    EscolaPeriodoEscolar,
    PeriodoEscolar,
    TipoUnidadeEscolar,
)

pytestmark = pytest.mark.django_db


def test_ativa_desativa_vinculos_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar(
    vinculos_alimentacao,
):
    assert TipoUnidadeEscolar.objects.count() == 4
    assert PeriodoEscolar.objects.count() == 1
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count() == 0
    )
    assert EscolaPeriodoEscolar.objects.count() == 1

    ativa_desativa_vinculos_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar()

    assert TipoUnidadeEscolar.objects.count() == 4
    assert PeriodoEscolar.objects.count() == 1
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count() == 4
    )
    assert EscolaPeriodoEscolar.objects.count() == 1


def test_bypass_ativa_vinculos(ativa_vinculo):
    tipo_unidade, _ = ativa_vinculo
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count() == 1
    )
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True
        ).count()
        == 0
    )
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=False
        ).count()
        == 1
    )

    bypass_ativa_vinculos(tipo_unidade, ["MANHA"])
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count() == 1
    )
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True
        ).count()
        == 0
    )
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=False
        ).count()
        == 1
    )

    bypass_ativa_vinculos(tipo_unidade, ["INTEGRAL"])
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.count() == 1
    )
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=True
        ).count()
        == 1
    )
    assert (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            ativo=False
        ).count()
        == 0
    )
