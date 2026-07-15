import datetime

import pytest
from freezegun import freeze_time
from model_bakery import baker
from xworkflows import InvalidTransitionError

from ...dados_comuns.behaviors import TempoPasseio

pytestmark = pytest.mark.django_db


def test_kit_lanche(kit_lanche):
    assert isinstance(kit_lanche.nome, str)
    assert isinstance(kit_lanche.descricao, str)
    assert isinstance(kit_lanche.status, str)
    assert isinstance(kit_lanche.edital.numero, str)
    assert isinstance(kit_lanche.__str__(), str)
    assert kit_lanche._meta.verbose_name == "Kit lanche"
    assert kit_lanche._meta.verbose_name_plural == "Kit lanches"


def test_item_kit_lanche(item_kit_lanche):
    assert isinstance(item_kit_lanche.nome, str)
    assert isinstance(item_kit_lanche.__str__(), str)


def test_solicitacao_avulsa(solicitacao_avulsa):
    assert isinstance(solicitacao_avulsa.local, str)
    assert solicitacao_avulsa.quantidade_alunos == 300
    assert solicitacao_avulsa.quantidade_alimentacoes == 900
    assert solicitacao_avulsa.data == datetime.date(2000, 1, 1)
    assert "Solicitação" in solicitacao_avulsa._meta.verbose_name


def test_solicitacao_unificada(solicitacao_unificada_lista_igual):
    assert isinstance(solicitacao_unificada_lista_igual.local, str)
    assert solicitacao_unificada_lista_igual.lista_kit_lanche_igual is True
    assert solicitacao_unificada_lista_igual.total_kit_lanche == 3000


def test_solicitacao_unificada_lotes_diferentes(solicitacao_unificada_lotes_diferentes):
    assert solicitacao_unificada_lotes_diferentes.quantidade_de_lotes == 2
    solicitacoes_unificadas = solicitacao_unificada_lotes_diferentes.dividir_por_lote()
    assert solicitacoes_unificadas.__len__() == 2


def test_solicitacao_unificada_lotes_iguais(solicitacao_unificada_lotes_iguais):
    assert solicitacao_unificada_lotes_iguais.quantidade_de_lotes == 1
    solicitacoes_unificadas = solicitacao_unificada_lotes_iguais.dividir_por_lote()
    assert solicitacoes_unificadas.__len__() == 1


def test_solicitacao(solicitacao):
    assert solicitacao.tempo_passeio == TempoPasseio.CINCO_A_SETE
    assert solicitacao.kits.count() == 3
    assert "Solicitação kit lanche base" in solicitacao._meta.verbose_name


def test_solicitacao_avulsa_workflow_case_1_partindo_da_escola(solicitacao_avulsa):
    """RASCUNHO > DRE_A_VALIDAR > DRE_VALIDADO > CODAE_AUTORIZADO > TERCEIRIZADA_TOMOU_CIENCIA."""
    wc = solicitacao_avulsa.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_avulsa.status == wc.RASCUNHO

    solicitacao_avulsa.inicia_fluxo(user=user)
    assert solicitacao_avulsa.status == wc.DRE_A_VALIDAR

    solicitacao_avulsa.dre_valida(
        user=user,
    )
    assert solicitacao_avulsa.status == wc.DRE_VALIDADO

    solicitacao_avulsa.codae_autoriza(
        user=user,
    )
    assert solicitacao_avulsa.status == wc.CODAE_AUTORIZADO

    solicitacao_avulsa.terceirizada_toma_ciencia(
        user=user,
    )
    assert solicitacao_avulsa.status == wc.TERCEIRIZADA_TOMOU_CIENCIA


def test_solicitacao_avulsa_workflow_case_2_partindo_da_escola(solicitacao_avulsa):
    """RASCUNHO > DRE_A_VALIDAR > DRE_PEDIU_ESCOLA_REVISAR > DRE_A_VALIDAR."""
    wc = solicitacao_avulsa.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_avulsa.status == wc.RASCUNHO

    solicitacao_avulsa.inicia_fluxo(user=user)
    assert solicitacao_avulsa.status == wc.DRE_A_VALIDAR

    solicitacao_avulsa.dre_pede_revisao(
        user=user,
    )
    assert solicitacao_avulsa.status == wc.DRE_PEDIU_ESCOLA_REVISAR

    solicitacao_avulsa.escola_revisa(
        user=user,
    )
    assert solicitacao_avulsa.status == wc.DRE_A_VALIDAR


def test_solicitacao_avulsa_workflow_case_3_partindo_da_escola(solicitacao_avulsa):
    """RASCUNHO > DRE_A_VALIDAR > DRE_NAO_VALIDOU_PEDIDO_ESCOLA."""
    wc = solicitacao_avulsa.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_avulsa.status == wc.RASCUNHO

    solicitacao_avulsa.inicia_fluxo(user=user)
    assert solicitacao_avulsa.status == wc.DRE_A_VALIDAR

    solicitacao_avulsa.dre_nao_valida(user=user)
    assert solicitacao_avulsa.status == wc.DRE_NAO_VALIDOU_PEDIDO_ESCOLA


def test_solicitacao_avulsa_workflow_case_4_partindo_da_escola(solicitacao_avulsa):
    """RASCUNHO > DRE_A_VALIDAR > DRE_VALIDADO > CODAE_NEGOU_PEDIDO."""
    wc = solicitacao_avulsa.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_avulsa.status == wc.RASCUNHO

    solicitacao_avulsa.inicia_fluxo(user=user)
    assert solicitacao_avulsa.status == wc.DRE_A_VALIDAR

    solicitacao_avulsa.dre_valida(
        user=user,
    )
    assert solicitacao_avulsa.status == wc.DRE_VALIDADO

    solicitacao_avulsa.codae_nega(user=user)
    assert solicitacao_avulsa.status == wc.CODAE_NEGOU_PEDIDO


def test_solicitacao_avulsa_workflow_partindo_da_escola_with_error(solicitacao_avulsa):
    wc = solicitacao_avulsa.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_avulsa.status == wc.RASCUNHO

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'dre_valida' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_avulsa.dre_valida(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'dre_nao_valida' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_avulsa.dre_nao_valida(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'dre_pede_revisao' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_avulsa.dre_pede_revisao(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'codae_autoriza' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_avulsa.codae_autoriza(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'codae_nega' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_avulsa.codae_nega(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'terceirizada_toma_ciencia' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_avulsa.terceirizada_toma_ciencia(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'escola_revisa' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_avulsa.escola_revisa(user=user)


@freeze_time("2019-10-09")
def test_solicitacao_unificada_lista_igual_workflow_case_1_partindo_da_diretoria_regional(
    solicitacao_unificada_lista_igual, escola
):
    """RASCUNHO > CODAE_A_AUTORIZAR > CODAE_PEDIU_DRE_REVISAR > CODAE_A_AUTORIZAR."""
    wc = solicitacao_unificada_lista_igual.workflow_class
    user = baker.make("perfil.Usuario")
    perfil_diretor = baker.make("Perfil", nome="DIRETOR", ativo=True)
    hoje = datetime.date.today()
    baker.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    assert solicitacao_unificada_lista_igual.status == wc.RASCUNHO
    assert solicitacao_unificada_lista_igual.pode_excluir is True
    assert solicitacao_unificada_lista_igual.ta_na_dre is True
    solicitacao_unificada_lista_igual.inicia_fluxo(user=user)
    assert solicitacao_unificada_lista_igual.ta_na_codae is True
    assert solicitacao_unificada_lista_igual.status == wc.CODAE_A_AUTORIZAR
    solicitacao_unificada_lista_igual.codae_pede_revisao(user=user)
    assert solicitacao_unificada_lista_igual.ta_na_dre is True
    assert solicitacao_unificada_lista_igual.status == wc.CODAE_PEDIU_DRE_REVISAR
    solicitacao_unificada_lista_igual.dre_revisa(user=user)
    assert solicitacao_unificada_lista_igual.ta_na_codae is True
    assert solicitacao_unificada_lista_igual.status == wc.CODAE_A_AUTORIZAR
    solicitacao_unificada_lista_igual.cancelar_pedido(user=user, justificativa="TESTE")
    assert solicitacao_unificada_lista_igual.status == wc.DRE_CANCELOU


def test_solicitacao_unificada_lista_igual_workflow_case_2_partindo_da_diretoria_regional(
    solicitacao_unificada_lista_igual,
):
    """RASCUNHO > CODAE_A_AUTORIZAR > CODAE_AUTORIZADO > TERCEIRIZADA_TOMOU_CIENCIA."""
    wc = solicitacao_unificada_lista_igual.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_unificada_lista_igual.status == wc.RASCUNHO
    assert solicitacao_unificada_lista_igual.ta_na_dre is True

    solicitacao_unificada_lista_igual.inicia_fluxo(user=user)
    assert solicitacao_unificada_lista_igual.status == wc.CODAE_A_AUTORIZAR

    solicitacao_unificada_lista_igual.codae_autoriza(user=user)
    assert solicitacao_unificada_lista_igual.status == wc.CODAE_AUTORIZADO
    assert solicitacao_unificada_lista_igual.ta_na_terceirizada is True
    solicitacao_unificada_lista_igual.terceirizada_toma_ciencia(user=user)
    assert solicitacao_unificada_lista_igual.status == wc.TERCEIRIZADA_TOMOU_CIENCIA


def test_solicitacao_unificada_lista_igual_workflow_case_3_partindo_da_diretoria_regional(
    solicitacao_unificada_lista_igual,
):
    """RASCUNHO > CODAE_A_AUTORIZAR > CODAE_NEGOU_PEDIDO."""
    wc = solicitacao_unificada_lista_igual.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_unificada_lista_igual.status == wc.RASCUNHO

    solicitacao_unificada_lista_igual.inicia_fluxo(user=user)
    assert solicitacao_unificada_lista_igual.status == wc.CODAE_A_AUTORIZAR

    solicitacao_unificada_lista_igual.codae_nega(user=user)
    assert solicitacao_unificada_lista_igual.status == wc.CODAE_NEGOU_PEDIDO


def test_solicitacao_unificada_lista_igual_workflow_partindo_da_escola_with_error(
    solicitacao_unificada_lista_igual,
):
    wc = solicitacao_unificada_lista_igual.workflow_class
    user = baker.make("perfil.Usuario")
    assert solicitacao_unificada_lista_igual.status == wc.RASCUNHO

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'codae_pede_revisao' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_unificada_lista_igual.codae_pede_revisao(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'codae_nega' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_unificada_lista_igual.codae_nega(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'dre_revisa' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_unificada_lista_igual.dre_revisa(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'codae_autoriza' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_unificada_lista_igual.codae_autoriza(user=user)

    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'terceirizada_toma_ciencia' isn't available from state 'RASCUNHO'",
    ):
        solicitacao_unificada_lista_igual.terceirizada_toma_ciencia(user=user)


@freeze_time("2019-10-02")
def test_tageamento_prioridade(kits_avulsos_parametros, escola):
    data_tupla, esperado = kits_avulsos_parametros
    kit_lanche_base = baker.make("SolicitacaoKitLanche", data=data_tupla)
    kit_lanche_avulso = baker.make(
        "SolicitacaoKitLancheAvulsa",
        escola=escola,
        solicitacao_kit_lanche=kit_lanche_base,
    )
    assert kit_lanche_avulso.prioridade == esperado


@freeze_time("2019-12-20")
def test_tageamento_prioridade_caso2(kits_avulsos_parametros2, escola):
    data_tupla, esperado = kits_avulsos_parametros2
    kit_lanche_base = baker.make("SolicitacaoKitLanche", data=data_tupla)
    kit_lanche_avulso = baker.make(
        "SolicitacaoKitLancheAvulsa",
        escola=escola,
        solicitacao_kit_lanche=kit_lanche_base,
    )
    assert kit_lanche_avulso.prioridade == esperado


def test_escola_quantidade(escola_quantidade):
    kit_lanche_personalizado = bool(escola_quantidade.kits.count())
    tempo_passeio = escola_quantidade.get_tempo_passeio_display()
    assert escola_quantidade.__str__() == (
        f"{tempo_passeio} para {escola_quantidade.quantidade_alunos} "
        f"alunos, kits diferenciados? {kit_lanche_personalizado}"
    )


def test_kit_lanche_cemei(kit_lanche_cemei):
    assert kit_lanche_cemei.tem_solicitacao_cei is True
    assert kit_lanche_cemei.tem_solicitacao_emei is True
    assert kit_lanche_cemei.total_kits == 120
    assert kit_lanche_cemei.total_kits_medicao_inicial == 30

    solicitacao_cei = kit_lanche_cemei.solicitacao_cei
    assert solicitacao_cei.nomes_kits == "KIT 1, KIT 2, KIT 3"
    assert solicitacao_cei.tem_alunos_com_dieta is False
    assert solicitacao_cei.quantidade_alimentacoes == 90
    assert solicitacao_cei.quantidade_alunos == 30
    assert solicitacao_cei.quantidade_matriculados == 60

    solicitacao_emei = kit_lanche_cemei.solicitacao_emei
    assert solicitacao_emei.nomes_kits == "KIT 1, KIT 2, KIT 3"
    assert solicitacao_emei.quantidade_alimentacoes == 30
    assert solicitacao_emei.tem_alunos_com_dieta is False
