from collections import Counter

import pytest
from freezegun import freeze_time

from sme_sigpae_api.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.dieta_especial.solicitacao_dieta_especial.models import (
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.dieta_especial.tasks.logs import (
    gera_logs_dietas_especiais_diariamente,
)
from sme_sigpae_api.escola.models import Aluno, Escola

pytestmark = pytest.mark.django_db


@freeze_time("2025-05-05")
def test_gera_logs_dietas_especiais_diariamente_sem_logs_gerados(
    solicitacoes_processa_dieta_especial,
    escola_cemei,
    escola_emebs,
    escola_cei,
    log_aluno_integral_cei,
    log_alunos_matriculados_integral_cei,
    escola_dre_guaianases,
):
    assert Escola.objects.filter(tipo_gestao__nome="TERC TOTAL").count() == 4
    gera_logs_dietas_especiais_diariamente()
    assert LogQuantidadeDietasAutorizadas.objects.all().count() == 0
    assert LogQuantidadeDietasAutorizadasCEI.objects.all().count() == 0


def set_up_faixas_etarias(faixa_etaria_factory):
    faixa_etaria_factory.create(inicio=0, fim=1)
    faixa_etaria_factory.create(inicio=1, fim=4)
    faixa_etaria_factory.create(inicio=4, fim=6)
    faixa_etaria_factory.create(inicio=6, fim=7)
    faixa_etaria_factory.create(inicio=7, fim=12)
    faixa_etaria_factory.create(inicio=12, fim=48)
    faixa_etaria_factory.create(inicio=48, fim=73)


def setup_dietas_especiais(
    escola_cemei,
    escola_emebs,
    escola_cei,
    make_periodo_escolar,
    classificacao_dieta_factory,
    solicitacao_dieta_especial_factory,
    aluno_factory,
):
    classificacao_tipo_a = classificacao_dieta_factory.create(nome="Tipo A")
    classificacao_tipo_b = classificacao_dieta_factory.create(nome="Tipo B")

    integral = make_periodo_escolar("INTEGRAL")
    manha = make_periodo_escolar("MANHA")

    aluno_cei = aluno_factory.create(
        escola=escola_cei,
        periodo_escolar=integral,
        data_nascimento="2021-08-02",
        ciclo=Aluno.CICLO_ALUNO_CEI,
    )
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_cei,
        rastro_escola=escola_cei,
        classificacao=classificacao_tipo_a,
        status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
    )

    aluno_emebs_infantil = aluno_factory.create(
        escola=escola_emebs,
        periodo_escolar=manha,
        data_nascimento="2016-08-02",
        etapa=Aluno.ETAPA_INFANTIL,
    )
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_emebs_infantil,
        rastro_escola=escola_emebs,
        classificacao=classificacao_tipo_b,
        status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
    )

    aluno_emebs_fundamental = aluno_factory.create(
        escola=escola_emebs,
        periodo_escolar=manha,
        data_nascimento="2015-08-02",
        etapa=Aluno.ETAPA_INFANTIL + 1,
    )
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_emebs_fundamental,
        rastro_escola=escola_emebs,
        classificacao=classificacao_tipo_a,
        status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
    )

    aluno_cemei_cei = aluno_factory.create(
        escola=escola_cemei,
        periodo_escolar=integral,
        data_nascimento="2024-08-06",
        ciclo=Aluno.CICLO_ALUNO_CEI,
    )
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_cemei_cei,
        rastro_escola=escola_cemei,
        classificacao=classificacao_tipo_a,
        status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
    )

    aluno_cemei_emei = aluno_factory.create(
        escola=escola_cemei,
        periodo_escolar=integral,
        data_nascimento="2018-08-06",
        ciclo=Aluno.CICLO_ALUNO_EMEI,
    )
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_cemei_emei,
        rastro_escola=escola_cemei,
        classificacao=classificacao_tipo_b,
        status=SolicitacaoDietaEspecial.workflow_class.CODAE_AUTORIZADO,
    )


@freeze_time("2025-02-02")
def test_gera_logs_dietas_especiais_diariamente_com_logs_gerados(
    escola_cemei,
    escola_emebs,
    escola_cei,
    make_periodo_escolar,
    solicitacao_dieta_especial_factory,
    faixa_etaria_factory,
    classificacao_dieta_factory,
    aluno_factory,
    monkeypatch,
):
    set_up_faixas_etarias(faixa_etaria_factory)
    setup_dietas_especiais(
        escola_cemei,
        escola_emebs,
        escola_cei,
        make_periodo_escolar,
        classificacao_dieta_factory,
        solicitacao_dieta_especial_factory,
        aluno_factory,
    )
    monkeypatch.setattr(
        Escola,
        "matriculados_por_periodo_e_faixa_etaria",
        lambda *args, **kwargs: {
            "MANHA": Counter({"uuid_fake": 125}),
            "TARDE": Counter({"uuid_fake": 154}),
            "INTEGRAL": Counter(
                {"uuid_fake1": 94, "uuid_fake2": 3, "uuid_fake3": 1, "uuid_fake4": 1}
            ),
        },
    )
    assert Aluno.objects.filter(dietas_especiais__isnull=False).count() == 5
    gera_logs_dietas_especiais_diariamente()
    assert LogQuantidadeDietasAutorizadas.objects.count() == 18
