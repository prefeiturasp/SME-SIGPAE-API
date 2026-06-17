from datetime import date, timedelta
from unittest.mock import patch

import pytest
from model_bakery import baker
from rest_framework import serializers

from src.dieta_especial.logs_models.models import (
    LogQuantidadeDietasAutorizadasCEI,
)
from src.dieta_especial.solicitacao_dieta_especial.models import (
    ClassificacaoDieta,
)
from src.escola.fixtures.factories.escola_factory import (
    AlunosMatriculadosPeriodoEscolaFactory,
    LogAlunosMatriculadosPeriodoEscolaFactory,
    PeriodoEscolarFactory,
)
from src.medicao_inicial.api.serializers import (
    DadosLiquidacaoSerializer,
    RelatorioFinanceiroSerializer,
)
from src.medicao_inicial.api.serializers_create import (
    DadosLiquidacaoUpdateSerializer,
    SolicitacaoMedicaoInicialCreateSerializer,
)
from src.medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    MedicaoFactory,
    SolicitacaoMedicaoInicialFactory,
)
from src.medicao_inicial.models import Medicao, RelatorioFinanceiro, ValorMedicao, CategoriaMedicao
from src.medicao_inicial.recreio_nas_ferias.fixtures.factories.base_factory import (
    RecreioNasFeriasFactory,
)
from src.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)

pytestmark = pytest.mark.django_db


def _serializer_recreio_context(usuario, finaliza_medicao=True):
    class FakeRequest:
        user = usuario
        data = {"finaliza_medicao": finaliza_medicao}

    return {"request": FakeRequest}


def _cria_solicitacao_com_medicoes_para_recreio(data_fim):
    recreio_nas_ferias = RecreioNasFeriasFactory.create(
        data_inicio=data_fim - timedelta(days=5),
        data_fim=data_fim,
    )
    solicitacao = SolicitacaoMedicaoInicialFactory.create(
        recreio_nas_ferias=recreio_nas_ferias,
    )
    solicitacao.status = (
        solicitacao.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    solicitacao.save(update_fields=["status"])

    medicao_manha = MedicaoFactory.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=PeriodoEscolarFactory.create(nome="MANHA"),
    )
    medicao_tarde = MedicaoFactory.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=PeriodoEscolarFactory.create(nome="TARDE"),
    )
    for medicao in [medicao_manha, medicao_tarde]:
        medicao.status = medicao.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        medicao.save(update_fields=["status"])

    return solicitacao, [medicao_manha, medicao_tarde]


def _cria_usuario_com_vinculo_escola(escola):
    usuario = UsuarioFactory.create()
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=escola,
        perfil__nome="DIRETOR_UE",
        ativo=True,
        data_inicial=date.today(),
    )
    return usuario


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


def test_cria_dados_liquidacao(relatorio_financeiro, escola_cei):
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


def test_finaliza_recreio_nas_ferias_retorna_erro_quando_ainda_nao_pode_finalizar():
    solicitacao, medicoes = _cria_solicitacao_com_medicoes_para_recreio(
        data_fim=date(2026, 1, 31)
    )
    usuario = _cria_usuario_com_vinculo_escola(solicitacao.escola)
    serializer = SolicitacaoMedicaoInicialCreateSerializer(
        context=_serializer_recreio_context(usuario)
    )

    with patch.object(
        serializer, "_process_anexos", return_value=[]
    ) as processa_anexos:
        with patch("src.medicao_inicial.api.serializers_create.date") as mock_date:
            mock_date.today.return_value = solicitacao.recreio_nas_ferias.data_fim

            with pytest.raises(serializers.ValidationError) as exc_info:
                serializer._finaliza_recreio_nas_ferias(
                    solicitacao,
                    {"com_ocorrencias": False},
                )

    solicitacao.refresh_from_db()
    for medicao in medicoes:
        medicao.refresh_from_db()

    assert (
        str(exc_info.value.detail[0])
        == "A medição só pode ser finalizada 1 dia após a data fim do Recreio nas Férias."
    )
    assert (
        solicitacao.status
        == solicitacao.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    )
    assert all(
        medicao.status == medicao.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        for medicao in medicoes
    )
    processa_anexos.assert_not_called()


def test_finaliza_recreio_nas_ferias_envia_solicitacao_e_medicoes():
    solicitacao, medicoes = _cria_solicitacao_com_medicoes_para_recreio(
        data_fim=date(2026, 1, 31)
    )
    usuario = _cria_usuario_com_vinculo_escola(solicitacao.escola)
    serializer = SolicitacaoMedicaoInicialCreateSerializer(
        context=_serializer_recreio_context(usuario)
    )

    with patch.object(
        serializer, "_process_anexos", return_value=[]
    ) as processa_anexos:
        with patch("src.medicao_inicial.api.serializers_create.date") as mock_date:
            mock_date.today.return_value = (
                solicitacao.recreio_nas_ferias.data_fim + timedelta(days=1)
            )

            serializer._finaliza_recreio_nas_ferias(
                solicitacao,
                {"com_ocorrencias": False},
            )

    solicitacao.refresh_from_db()
    for medicao in medicoes:
        medicao.refresh_from_db()

    assert solicitacao.status == solicitacao.workflow_class.MEDICAO_ENVIADA_PELA_UE
    assert all(
        medicao.status == medicao.workflow_class.MEDICAO_ENVIADA_PELA_UE
        for medicao in medicoes
    )
    processa_anexos.assert_called_once_with(solicitacao)


@pytest.mark.django_db
def test_atualizar_status_relatorio_financeiro(
    relatorio_financeiro_cei,
):
    assert relatorio_financeiro_cei.status == "RELATORIO_FINANCEIRO_GERADO"

    payload = {
        "status": "EM_ANALISE",
    }

    serializer_update = RelatorioFinanceiroSerializer(
        instance=relatorio_financeiro_cei,
        data=payload,
        partial=True,
    )

    assert serializer_update.is_valid(), serializer_update.errors

    relatorio_atualizado = serializer_update.save()
    relatorio_atualizado.refresh_from_db()

    assert relatorio_atualizado.status == "EM_ANALISE"


def test_medicao_get_or_create_nao_duplica():
    """Verifica que get_or_create não cria Medicao duplicadas (regressão race condition)."""
    solicitacao = baker.make("SolicitacaoMedicaoInicial")
    periodo = baker.make("PeriodoEscolar", nome="MANHA")

    medicao1, created1 = Medicao.objects.get_or_create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo,
    )
    assert created1 is True
    assert Medicao.objects.count() == 1

    medicao2, created2 = Medicao.objects.get_or_create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo,
    )
    assert created2 is False
    assert Medicao.objects.count() == 1
    assert medicao2.pk == medicao1.pk


def test_cria_valores_medicao_logs_matriculados_emef_emei_nao_duplica(
    escola, periodo_escolar
):
    """Verifica que método EMEF/EMEI não duplica Medicao ao ser chamado 2x."""
    CategoriaMedicao.objects.get_or_create(nome="ALIMENTAÇÃO")

    AlunosMatriculadosPeriodoEscolaFactory(
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )
    log = LogAlunosMatriculadosPeriodoEscolaFactory(
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )
    log.criado_em = date(2022, 12, 1)
    log.save()

    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2022,
        escola=escola,
        rastro_lote=escola.lote,
    )

    serializer = SolicitacaoMedicaoInicialCreateSerializer()
    serializer.cria_valores_medicao_logs_alunos_matriculados_emef_emei(solicitacao)

    total = solicitacao.medicoes.count()
    assert total > 0

    serializer.cria_valores_medicao_logs_alunos_matriculados_emef_emei(solicitacao)

    assert solicitacao.medicoes.count() == total


def test_cria_valores_medicao_logs_matriculados_cei_nao_duplica(
    escola_cei, periodo_escolar
):
    """Verifica que método CEI não duplica Medicao ao ser chamado 2x."""
    CategoriaMedicao.objects.get_or_create(nome="ALIMENTAÇÃO")

    AlunosMatriculadosPeriodoEscolaFactory(
        escola=escola_cei,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )
    log = LogAlunosMatriculadosPeriodoEscolaFactory(
        escola=escola_cei,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar,
        quantidade_alunos=100,
    )
    log.criado_em = date(2022, 12, 1)
    log.save()

    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=12,
        ano=2022,
        escola=escola_cei,
        rastro_lote=escola_cei.lote,
    )

    serializer = SolicitacaoMedicaoInicialCreateSerializer()
    serializer.cria_valores_medicao_logs_alunos_matriculados_cei(solicitacao)

    total = solicitacao.medicoes.count()
    assert total > 0

    serializer.cria_valores_medicao_logs_alunos_matriculados_cei(solicitacao)

    assert solicitacao.medicoes.count() == total


def test_cria_valores_medicao_logs_matriculados_emef_emei_periodo_vigente(
    escola,
    periodo_escolar_manha,
    periodo_escolar_tarde,
    periodo_escolar_noite,
):
    """Verifica que método EMEF/EMEI não cria valores para período não vigente."""
    CategoriaMedicao.objects.get_or_create(nome="ALIMENTAÇÃO")

    for periodo in [periodo_escolar_manha, periodo_escolar_tarde]:
        AlunosMatriculadosPeriodoEscolaFactory(
            escola=escola,
            tipo_turma="REGULAR",
            periodo_escolar=periodo,
            quantidade_alunos=100,
        )
        log = LogAlunosMatriculadosPeriodoEscolaFactory(
            escola=escola,
            tipo_turma="REGULAR",
            periodo_escolar=periodo,
            quantidade_alunos=100,
        )
        log.criado_em = date(2026, 4, 1)
        log.save()

    AlunosMatriculadosPeriodoEscolaFactory(
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar_noite,
        quantidade_alunos=100,
    )
    log = LogAlunosMatriculadosPeriodoEscolaFactory(
        escola=escola,
        tipo_turma="REGULAR",
        periodo_escolar=periodo_escolar_noite,
        quantidade_alunos=100,
    )
    log.criado_em = date(2026, 3, 1)
    log.save()

    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2026,
        escola=escola,
        rastro_lote=escola.lote,
    )

    serializer = SolicitacaoMedicaoInicialCreateSerializer()
    serializer.cria_valores_medicao_logs_alunos_matriculados_emef_emei(solicitacao)

    total = solicitacao.medicoes.count()
    assert total == 2
    assert solicitacao.medicoes.count() == total


def test_cria_valores_medicao_logs_matriculados_cei_periodo_vigente(
    escola_cei,
    periodo_escolar_manha,
    periodo_escolar_tarde,
):
    """Verifica que método CEI não cria valores para período não vigente."""
    CategoriaMedicao.objects.get_or_create(nome="ALIMENTAÇÃO")

    for periodo in [
        (periodo_escolar_manha, date(2026, 4, 1)),
        (periodo_escolar_tarde, date(2026, 3, 1)),
    ]:
        AlunosMatriculadosPeriodoEscolaFactory(
            escola=escola_cei,
            tipo_turma="REGULAR",
            periodo_escolar=periodo[0],
            quantidade_alunos=100,
        )
        log = LogAlunosMatriculadosPeriodoEscolaFactory(
            escola=escola_cei,
            tipo_turma="REGULAR",
            periodo_escolar=periodo[0],
            quantidade_alunos=100,
        )
        log.criado_em = periodo[1]
        log.save()

    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes=4,
        ano=2026,
        escola=escola_cei,
        rastro_lote=escola_cei.lote,
    )

    serializer = SolicitacaoMedicaoInicialCreateSerializer()
    serializer.cria_valores_medicao_logs_alunos_matriculados_cei(solicitacao)

    total = solicitacao.medicoes.count()
    assert total == 1
    assert solicitacao.medicoes.count() == total
