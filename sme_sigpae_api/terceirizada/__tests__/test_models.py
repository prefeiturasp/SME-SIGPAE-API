import pytest

pytestmark = pytest.mark.django_db


def test_modelo_edital(edital):
    assert edital.uuid is not None
    assert edital.tipo_contratacao is not None
    assert edital.numero is not None
    assert edital.processo is not None
    assert edital.numero is not None
    assert edital.objeto is not None
    assert edital.contratos is not None
    assert hasattr(edital, "contratos")
    assert edital.__str__() == "1"


def test_modelo_contrato(contrato):
    assert contrato.__str__() == "Contrato:1 Processo: 12345"
    assert contrato.uuid is not None
    assert contrato.numero is not None
    assert contrato.processo is not None
    assert contrato.data_proposta is None
    assert contrato.lotes is not None
    assert contrato.terceirizada is None
    assert contrato.vigencias is not None
    assert contrato.diretorias_regionais is not None


def test_modelo_vigencia_contrato(vigencia_contrato):
    assert vigencia_contrato.__str__() == "Contrato:1 2019-01-01 a 2019-01-31"
    assert vigencia_contrato.uuid is not None
    assert vigencia_contrato.data_inicial is not None
    assert vigencia_contrato.data_final is not None


def test_terceirizada(terceirizada):
    assert terceirizada.__str__() == "Alimentos SA"
    assert terceirizada.nome is not None
    assert terceirizada.nutricionistas is not None
    assert terceirizada.inclusoes_continuas_autorizadas is not None
    assert terceirizada.inclusoes_normais_autorizadas is not None
    assert terceirizada.inclusoes_continuas_reprovadas is not None
    assert terceirizada.solicitacao_kit_lanche_avulsa_autorizadas is not None
    assert terceirizada.inclusoes_normais_reprovadas is not None
    assert terceirizada.alteracoes_cardapio_autorizadas is not None
    assert terceirizada.alteracoes_cardapio_reprovadas is not None
    assert terceirizada.inversoes_cardapio_autorizadas is not None
    assert terceirizada.solicitacoes_unificadas_autorizadas is not None
    assert terceirizada.quantidade_alunos is not None
    assert terceirizada.nutricionistas is not None

    filtro = "Hoje"
    assert (
        terceirizada.inclusoes_continuas_das_minhas_escolas_no_prazo_vencendo(filtro)
        is not None
    )
    assert (
        terceirizada.inclusoes_continuas_das_minhas_escolas_no_prazo_limite(filtro)
        is not None
    )
    assert (
        terceirizada.inclusoes_continuas_das_minhas_escolas_no_prazo_regular(filtro)
        is not None
    )
    assert (
        terceirizada.inclusoes_normais_das_minhas_escolas_no_prazo_vencendo(filtro)
        is not None
    )
    assert (
        terceirizada.inclusoes_normais_das_minhas_escolas_no_prazo_limite(filtro)
        is not None
    )
    assert (
        terceirizada.inclusoes_normais_das_minhas_escolas_no_prazo_regular(filtro)
        is not None
    )
    assert (
        terceirizada.alteracoes_cardapio_das_minhas_escolas_no_prazo_vencendo(filtro)
        is not None
    )
    assert (
        terceirizada.alteracoes_cardapio_das_minhas_escolas_no_prazo_limite(filtro)
        is not None
    )
    assert (
        terceirizada.alteracoes_cardapio_das_minhas_escolas_no_prazo_regular(filtro)
        is not None
    )
    assert terceirizada.alteracoes_cardapio_das_minhas(filtro) is not None
    assert (
        terceirizada.grupos_inclusoes_alimentacao_normal_das_minhas_escolas(filtro)
        is not None
    )
    assert (
        terceirizada.inclusoes_alimentacao_continua_das_minhas_escolas(filtro)
        is not None
    )
    assert terceirizada.suspensoes_alimentacao_das_minhas_escolas(filtro) is not None
    assert terceirizada.inversoes_cardapio_das_minhas_escolas(filtro) is not None
    assert terceirizada.solicitacoes_unificadas_das_minhas_escolas(filtro) is not None
    assert (
        terceirizada.solicitacoes_kit_lanche_das_minhas_escolas_a_validar(filtro)
        is not None
    )

    filtro = "daqui_a_7_dias"
    assert terceirizada.alteracoes_cardapio_das_minhas(filtro) is not None

    filtro = "daqui_a_30_dias"
    assert terceirizada.alteracoes_cardapio_das_minhas(filtro) is not None


def test_nutricionista(nutricionista):
    assert nutricionista.__str__() == "nutri"


def test_modelo_modulo(modulo):
    assert modulo.__str__() == "Dieta Especial"
    assert modulo.uuid is not None
    assert modulo.nome is not None


def test_modelo_emailterceirizadapormodulo(emailterceirizadapormodulo):
    assert (
        emailterceirizadapormodulo.__str__()
        == "teste@teste.com - Alimentos SA - Dieta Especial"
    )
    assert emailterceirizadapormodulo.uuid is not None
    assert emailterceirizadapormodulo.terceirizada is not None
    assert emailterceirizadapormodulo.modulo is not None
    assert emailterceirizadapormodulo.criado_em is not None
    assert emailterceirizadapormodulo.criado_por is not None


def test_inclusoes_continuas_das_minhas_escolas(terceirizada):
    inclusoes1 = terceirizada.inclusoes_continuas_das_minhas_escolas_no_prazo_vencendo(
        filtro_aplicado="hoje"
    )
    inclusoes2 = terceirizada.inclusoes_continuas_das_minhas_escolas_no_prazo_limite(
        filtro_aplicado="daqui_a_7_dias"
    )
    inclusoes3 = terceirizada.inclusoes_continuas_das_minhas_escolas_no_prazo_regular(
        filtro_aplicado="daqui_a_30_dias"
    )
    inclusoes4 = terceirizada.inclusoes_continuas_das_minhas_escolas_no_prazo_regular(
        filtro_aplicado="daqui_a_7_dias"
    )
    assert len(inclusoes1) == 0
    assert len(inclusoes2) == 0
    assert len(inclusoes3) == 0
    assert len(inclusoes4) == 0


def test_inclusoes_normais_das_minhas_escolas(terceirizada):
    inclusoes1 = terceirizada.inclusoes_normais_das_minhas_escolas_no_prazo_vencendo(
        filtro_aplicado="hoje"
    )
    inclusoes2 = terceirizada.inclusoes_normais_das_minhas_escolas_no_prazo_limite(
        filtro_aplicado="daqui_a_7_dias"
    )
    inclusoes3 = terceirizada.inclusoes_normais_das_minhas_escolas_no_prazo_regular(
        filtro_aplicado="daqui_a_30_dias"
    )
    inclusoes4 = terceirizada.inclusoes_normais_das_minhas_escolas_no_prazo_regular(
        filtro_aplicado="daqui_a_7_dias"
    )
    assert len(inclusoes1) == 0
    assert len(inclusoes2) == 0
    assert len(inclusoes3) == 0
    assert len(inclusoes4) == 0


def test_alteracoes_cardapio_das_minhas_escolas(terceirizada):
    alteracao1 = terceirizada.alteracoes_cardapio_das_minhas_escolas_no_prazo_vencendo(
        filtro_aplicado="hoje"
    )
    alteracao2 = terceirizada.alteracoes_cardapio_das_minhas_escolas_no_prazo_limite(
        filtro_aplicado="daqui_a_7_dias"
    )
    alteracao3 = terceirizada.alteracoes_cardapio_das_minhas_escolas_no_prazo_regular(
        filtro_aplicado="daqui_a_30_dias"
    )
    alteracao4 = terceirizada.alteracoes_cardapio_das_minhas_escolas_no_prazo_regular(
        filtro_aplicado="daqui_a_7_dias"
    )
    assert len(alteracao1) == 0
    assert len(alteracao2) == 0
    assert len(alteracao3) == 0
    assert len(alteracao4) == 0


def test_alteracoes_cardapio_das_minhas_escolas_cei(terceirizada):
    alteracao = terceirizada.alteracoes_cardapio_cei_das_minhas(filtro_aplicado="hoje")
    assert len(alteracao) == 0


def test_modelo_modalidade(modalidade):
    assert modalidade.__str__() == "Pregão Eletrônico"
    assert modalidade.uuid is not None
    assert modalidade.nome is not None
