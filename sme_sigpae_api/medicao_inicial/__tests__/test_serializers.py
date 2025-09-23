from datetime import date

import pytest
from model_bakery import baker

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.medicao_inicial.api.serializers_create import (
    SolicitacaoMedicaoInicialCreateSerializer,
)
from sme_sigpae_api.medicao_inicial.models import Medicao, ValorMedicao

pytestmark = pytest.mark.django_db


def test_nao_cria_valores_medicao_cei_sem_faixa_etaria(
    solicitacao_medicao_inicial_sem_valores,
    escola,
    periodo_escolar,
    categoria_dieta_b,
    categoria_dieta_a,
):
    baker.make("Aluno", escola=escola, periodo_escolar=periodo_escolar)
    baker.make(
        "CategoriaMedicao",
        nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
    )

    medicao = Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao_medicao_inicial_sem_valores,
        periodo_escolar=periodo_escolar,
    )

    classificacao = ClassificacaoDieta.objects.create(
        nome="DIETA ESPECIAL - TIPO B - Sem lactose"
    )

    LogQuantidadeDietasAutorizadasCEI.objects.create(
        escola=escola,
        periodo_escolar=periodo_escolar,
        classificacao=classificacao,
        quantidade=10,
        faixa_etaria=None,
        data=date(2022, 12, 1),
    )

    serializer = SolicitacaoMedicaoInicialCreateSerializer()
    serializer.cria_valores_medicao_logs_dietas_autorizadas_cei(
        solicitacao_medicao_inicial_sem_valores
    )

    valores = ValorMedicao.objects.filter(
        medicao=medicao,
        categoria_medicao=categoria_dieta_b,
        nome_campo="dietas_autorizadas",
    )

    assert valores.count() == 0


def test_cria_valores_medicao_cei_com_faixa_etaria(
    solicitacao_medicao_inicial_sem_valores,
    escola,
    periodo_escolar,
    faixa_etaria,
    categoria_dieta_b,
    categoria_dieta_a,
):
    baker.make("Aluno", escola=escola, periodo_escolar=periodo_escolar)
    baker.make(
        "CategoriaMedicao",
        nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS",
    )

    medicao = Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao_medicao_inicial_sem_valores,
        periodo_escolar=periodo_escolar,
    )

    classificacao = ClassificacaoDieta.objects.create(
        nome="DIETA ESPECIAL - TIPO B - Apenas fruta"
    )

    LogQuantidadeDietasAutorizadasCEI.objects.create(
        escola=escola,
        periodo_escolar=periodo_escolar,
        classificacao=classificacao,
        quantidade=7,
        faixa_etaria=faixa_etaria,
        data=date(2022, 12, 1),
    )

    serializer = SolicitacaoMedicaoInicialCreateSerializer()
    serializer.cria_valores_medicao_logs_dietas_autorizadas_cei(
        solicitacao_medicao_inicial_sem_valores
    )

    valores = ValorMedicao.objects.filter(
        medicao=medicao,
        categoria_medicao=categoria_dieta_b,
        nome_campo="dietas_autorizadas",
    )
    assert valores.count() == 1
    assert valores.first().valor == "7"
    assert valores.first().faixa_etaria == faixa_etaria
