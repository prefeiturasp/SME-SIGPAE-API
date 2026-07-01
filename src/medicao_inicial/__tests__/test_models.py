import datetime
from unittest.mock import patch

import pytest
from django.db.utils import IntegrityError
from model_bakery import baker
from src.medicao_inicial.models import (
    SolicitacaoMedicaoInicial,
    DescontoFinanceiro,
)

pytestmark = pytest.mark.django_db


def test_dia_sobremesa_doce_model(dia_sobremesa_doce):
    assert (
        dia_sobremesa_doce.__str__()
        == "08/08/2022 - EMEF - Edital Edital de Pregão nº 13/SME/2020"
    )


def test_solicitacao_medicao_inicial_model(solicitacao_medicao_inicial):
    assert (
        solicitacao_medicao_inicial.__str__()
        == "Solicitação #BED4D -- Escola EMEF TESTE -- 12/2022"
    )


def test_anexo_ocorrencia_medicao_inicial_model(anexo_ocorrencia_medicao_inicial):
    uuid_ocorrencia = "1ace193a-6c2c-4686-b9ed-60a922ad0e1a"
    uuid_solicitacao = "bed4d779-2d57-4c5f-bf9c-9b93ddac54d9"
    str_model = f"Ocorrência {uuid_ocorrencia} da Solicitação de Medição Inicial {uuid_solicitacao}"
    assert anexo_ocorrencia_medicao_inicial.__str__() == str_model


def test_responsavel_model(responsavel):
    assert responsavel.__str__() == "Responsável tester - 1234567"


def test_tipo_contagem_alimentacao_model(tipo_contagem_alimentacao):
    assert tipo_contagem_alimentacao.__str__() == "Fichas"


def test_medicao_model(medicao):
    assert medicao.__str__() == "Medição #5A3A3 -- INTEGRAL -- 12/2022"


def test_categoria_medicao_model(categoria_medicao):
    assert categoria_medicao.__str__() == "ALIMENTAÇÃO"


def test_valor_medicao_model(valor_medicao):
    assert (
        valor_medicao.__str__()
        == "#FC2FB -- Categoria ALIMENTAÇÃO -- Campo observacoes -- Dia/Mês 13/12"
    )


def test_dia_para_corrigir_model(dia_para_corrigir):
    assert dia_para_corrigir.__str__() == (
        "# D5C33 - EMEF TESTE - INTEGRAL - 01/12/2022 - N/A"
    )


def test_solicitacao_medicao_todas_medicoes_e_ocorrencia_aprovados_por_medicao_false(
    anexo_ocorrencia_medicao_inicial,
):
    solicitacao_medicao_inicial = (
        anexo_ocorrencia_medicao_inicial.solicitacao_medicao_inicial
    )
    assert (
        solicitacao_medicao_inicial.todas_medicoes_e_ocorrencia_aprovados_por_medicao
        is False
    )


def test_solicitacao_medicao_todas_medicoes_e_ocorrencia_aprovados_por_medicao_true(
    solicitacao_com_anexo_e_medicoes_aprovadas,
):
    assert (
        solicitacao_com_anexo_e_medicoes_aprovadas.todas_medicoes_e_ocorrencia_aprovados_por_medicao
        is True
    )


def test_solicitacao_medicao_assinatura_escola_exception(solicitacao_medicao_inicial):
    assert solicitacao_medicao_inicial.assinatura_ue == ""


def test_solicitacao_medicao_assinatura_escola_sucesso(
    solicitacao_com_anexo_e_medicoes_aprovadas,
):
    assert (
        "Documento conferido e registrado eletronicamente por "
        in solicitacao_com_anexo_e_medicoes_aprovadas.assinatura_ue
    )


def test_solicitacao_medicao_assinatura_dre_sucesso(
    solicitacao_com_anexo_e_medicoes_aprovadas,
):
    assert (
        "Documento conferido e aprovado eletronicamente por "
        in solicitacao_com_anexo_e_medicoes_aprovadas.assinatura_dre
    )


def test_solicitacao_medicao_tem_lanche_emergencial_diario_true(
    solicitacao_medicao_inicial_factory,
    lanche_emergencial_diario_factory,
):
    solicitacao = solicitacao_medicao_inicial_factory(mes="03", ano="2024")

    lanche_emergencial_diario_factory(
        escola=solicitacao.escola,
        data_inicial=datetime.date(2024, 3, 1),
        data_final=datetime.date(2024, 3, 31),
    )

    assert solicitacao.tem_lanche_emergencial_diario is True


def test_solicitacao_medicao_tem_lanche_emergencial_diario_false(
    solicitacao_medicao_inicial_factory,
    lanche_emergencial_diario_factory,
):
    solicitacao = solicitacao_medicao_inicial_factory(mes="03", ano="2024")

    lanche_emergencial_diario_factory(
        escola=solicitacao.escola,
        data_inicial=datetime.date(2024, 4, 1),
        data_final=datetime.date(2024, 4, 30),
    )

    assert solicitacao.tem_lanche_emergencial_diario is False


def test_solicitacao_medicao_dias_lanche_emergencial_diario_retorna_apenas_dias_do_periodo_letivos(
    solicitacao_medicao_inicial_factory,
    lanche_emergencial_diario_factory,
    dia_calendario_factory,
):
    solicitacao = solicitacao_medicao_inicial_factory(mes="03", ano="2024")
    lanche = lanche_emergencial_diario_factory(
        escola=solicitacao.escola,
        data_inicial=datetime.date(2024, 3, 5),
        data_final=datetime.date(2024, 3, 7),
    )

    dias_letivos = {5, 7, 8}
    for dia in range(1, 32):
        dia_calendario_factory(
            escola=solicitacao.escola,
            data=datetime.date(2024, 3, dia),
            dia_letivo=dia in dias_letivos,
            periodo_escolar=None,
        )

    dias_retornados = solicitacao.dias_lanche_emergencial_diario

    assert dias_retornados == ["05", "07"]
    assert all(
        lanche.data_inicial.day <= int(dia) <= lanche.data_final.day
        for dia in dias_retornados
    )
    assert all(
        solicitacao.escola.calendario.get(
            data=datetime.date(2024, 3, int(dia)),
            periodo_escolar__isnull=True,
        ).dia_letivo
        is True
        for dia in dias_retornados
    )


def test_empenho_model(empenho):
    assert empenho.__str__() == "Empenho: 123456"


def test_parametrizacao_financeira(parametrizacao_financeira_emef):
    assert (
        parametrizacao_financeira_emef.__str__()
        == "Edital Edital de Pregão nº 78/SME/2024 | Lote 1 - DIRETORIA REGIONAL IPIRANGA | DRE DIRETORIA REGIONAL IPIRANGA | Tipos de Unidades CEU EMEF, CEU GESTAO, EMEF, EMEFM"
    )


def test_solicitacoes_sem_lancamentos(solicitacao_sem_lancamento):
    assert solicitacao_sem_lancamento.sem_lancamentos == True


def test_justificativa_sem_lancamentos_retorna_none(solicitacao_escola_emebs):
    assert solicitacao_escola_emebs.justificativa_sem_lancamentos is None


def test_justificativa_sem_lancamentos(solicitacao_sem_lancamento):
    assert (
        solicitacao_sem_lancamento.justificativa_sem_lancamentos
        == "Não houve aula no período"
    )


def test_justificativa_codae_correcao_sem_lancamentos(
    solicitacao_sem_lancamento_com_correcao,
):
    assert (
        solicitacao_sem_lancamento_com_correcao.justificativa_codae_correcao_sem_lancamentos
        == "Houve alimentação ofertadada nesse período"
    )


def test_justificativa_codae_correcao_sem_lancamentos_status_solicitacao_incorreto(
    solicitacao_sem_lancamento,
):
    assert (
        solicitacao_sem_lancamento.justificativa_codae_correcao_sem_lancamentos is None
    )


def test_justificativa_codae_correcao_sem_lancamentos_possui_logs_sem_lancamento(
    solicitacao_sem_lancamento_com_correcao,
):
    solicitacao_sem_lancamento_com_correcao.medicoes.all().delete()
    solicitacao_sem_lancamento_com_correcao.save()
    assert (
        solicitacao_sem_lancamento_com_correcao.justificativa_codae_correcao_sem_lancamentos
        is None
    )


def test_solicitacao_medicao_normaliza_grupo_legado_recreio_nas_ferias_para_cei(
    escola_cei,
    recreio_nas_ferias,
):
    grupo_recreio = baker.make("GrupoMedicao", nome="Recreio nas Férias")
    grupo_legado = baker.make(
        "GrupoMedicao",
        nome="Recreio nas Férias - de 0 a 3 anos e 11 meses",
    )
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes="12",
        ano="2025",
        escola=escola_cei,
        recreio_nas_ferias=recreio_nas_ferias,
    )
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        grupo=grupo_legado,
        periodo_escolar=None,
    )

    medicao_normalizada = solicitacao.get_medicao_por_periodo_e_ou_grupo(
        "Recreio nas Férias"
    )

    medicao.refresh_from_db()

    assert medicao_normalizada == medicao
    assert medicao.grupo == grupo_recreio
    assert medicao.nome_periodo_grupo == "Recreio nas Férias"


def test_medicao_mantem_grupo_recreio_com_faixa_etaria_para_cemei(
    escola_cemei,
    recreio_nas_ferias,
):
    grupo_legado = baker.make(
        "GrupoMedicao",
        nome="Recreio nas Férias - de 0 a 3 anos e 11 meses",
    )
    solicitacao = baker.make(
        "SolicitacaoMedicaoInicial",
        mes="12",
        ano="2025",
        escola=escola_cemei,
        recreio_nas_ferias=recreio_nas_ferias,
    )
    medicao = baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        grupo=grupo_legado,
        periodo_escolar=None,
    )

    assert medicao.nome_periodo_grupo == "Recreio nas Férias - de 0 a 3 anos e 11 meses"


def test_unique_constraint_sem_recreio(escola):
    """Não deve permitir duas solicitações sem recreio para a mesma escola/mes/ano."""
    SolicitacaoMedicaoInicial.objects.create(
        escola=escola, mes="06", ano="2024",
    )
    with pytest.raises(IntegrityError):
        SolicitacaoMedicaoInicial.objects.create(
            escola=escola, mes="06", ano="2024",
        )


def test_cria_medicoes_dos_periodos_passa_mes_para_periodos_escolares(
    solicitacao_medicao_inicial_factory,
):
    """Verifica que cria_medicoes_dos_periodos chama periodos_escolares com ano e mes."""
    solicitacao = solicitacao_medicao_inicial_factory(mes="03", ano="2024")

    periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
    periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")

    with patch.object(
        solicitacao.escola,
        "periodos_escolares",
        return_value=[periodo_manha, periodo_tarde],
    ) as mock_periodos:
        solicitacao.cria_medicoes_dos_periodos()

        # Deve chamar periodos_escolares com o mes como inteiro
        mock_periodos.assert_called_once_with("2024", 3)

        # Deve criar Medicao para cada periodo retornado
        assert solicitacao.medicoes.count() == 2


def test_cria_medicoes_dos_periodos_nao_cria_quando_sem_periodos(
    solicitacao_medicao_inicial_factory,
):
    """Verifica que cria_medicoes_dos_periodos nao cria medicoes quando nao ha periodos."""
    solicitacao = solicitacao_medicao_inicial_factory(mes="03", ano="2024")

    with patch.object(
        solicitacao.escola,
        "periodos_escolares",
        return_value=[],
    ) as mock_periodos:
        solicitacao.cria_medicoes_dos_periodos()

        mock_periodos.assert_called_once_with("2024", 3)
        assert solicitacao.medicoes.count() == 0


def test_cria_desconto_financeiro_emei(
    relatorio_financeiro_emei,
    clausula_desconto,
    tipo_alimentacao_lanche,
):
    desconto = baker.make(
        DescontoFinanceiro,
        relatorio_financeiro=relatorio_financeiro_emei,
        clausula_desconto=clausula_desconto,
        quantidade=10,
        tipo_lancamento="ALIMENTACOES",
        tipo_alimentacao=tipo_alimentacao_lanche,
    )

    assert desconto.relatorio_financeiro == relatorio_financeiro_emei
    assert desconto.clausula_desconto == clausula_desconto
    assert desconto.quantidade == 10
    assert desconto.tipo_lancamento == "ALIMENTACOES"
    assert desconto.tipo_alimentacao == tipo_alimentacao_lanche
    assert desconto.faixa_etaria is None

    assert str(desconto) == "Alimentação - Lanche"
