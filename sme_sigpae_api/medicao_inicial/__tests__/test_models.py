import pytest

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
    assert solicitacao_medicao_inicial.assinatura_ue is None


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


def test_empenho_model(empenho):
    assert empenho.__str__() == "Empenho: 123456"


def test_parametrizacao_financeira(parametrizacao_financeira_emef):
    assert (
        parametrizacao_financeira_emef.__str__()
        == "Edital Edital de Pregão nº 78/SME/2024 | Lote 1 - DIRETORIA REGIONAL IPIRANGA | DRE DIRETORIA REGIONAL IPIRANGA | Tipos de Unidades CEU EMEF, CEU GESTAO, CIEJA, EMEF, EMEFM"
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
