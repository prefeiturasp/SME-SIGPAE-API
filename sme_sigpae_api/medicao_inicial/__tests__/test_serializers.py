from datetime import date

import pytest
from model_bakery import baker

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadasCEI,
)
from sme_sigpae_api.escola.fixtures.factories.escola_factory import (
    AlunosMatriculadosPeriodoEscolaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
)
from sme_sigpae_api.medicao_inicial.api.serializers_create import (
    SolicitacaoMedicaoInicialCreateSerializer,
    DadosLiquidacaoUpdateSerializer,
)
from sme_sigpae_api.medicao_inicial.api.serializers import (
    DadosLiquidacaoSerializer,
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
    AlunosMatriculadosPeriodoEscolaFactory.create(
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )
    log = LogAlunosMatriculadosPeriodoEscolaFactory.create(
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )
    log.criado_em = date(2022, 12, 1)
    log.save()

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


def test_cria_dados_liquidacao(
    relatorio_financeiro,
    escola_cei
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro.uuid),
        "numero_empenho": "888/6598",
        "tipo_empenho": "PRINCIPAL",
        "unidades_educacionais": [escola_cei.uuid],
    }

    serializer = DadosLiquidacaoUpdateSerializer(data=payload)

    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()

    assert instance.relatorio_financeiro == relatorio_financeiro
    assert instance.numero_empenho == "888/6598"
    assert instance.unidades_educacionais.count() == 1


def test_retorna_dados_liquidacao(dados_liquidacao_cmct):
    serializer = DadosLiquidacaoSerializer(dados_liquidacao_cmct)

    data = serializer.data

    assert "relatorio_financeiro" in data
    assert isinstance(data["unidades_educacionais"], list)
    assert len(data["unidades_educacionais"]) == 1
    assert "uuid" in data["unidades_educacionais"][0]
