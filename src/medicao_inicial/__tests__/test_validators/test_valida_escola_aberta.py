import datetime

import pytest
from model_bakery import baker

from src.dados_comuns import constants
from src.medicao_inicial.models import GrupoMedicao
from src.medicao_inicial.validators import (
    validate_lancamento_alimentacoes_escola_aberta,
)

pytestmark = pytest.mark.django_db


def _criar_cadastro_escola_aberta(escola, tipos_alimentacao):
    cadastro = baker.make(
        "EscolaAberta",
        data_inicial=datetime.date(2022, 12, 1),
        data_final=datetime.date(2022, 12, 1),
        dias_semana=["3"],
    )
    unidade = baker.make(
        "EscolaAbertaUnidadeParticipante",
        escola_aberta=cadastro,
        lote=escola.lote,
        unidade_educacional=escola,
        num_participantes=10,
    )
    unidade.tipos_alimentacao.set(tipos_alimentacao)
    return unidade


def _criar_medicao_escola_aberta(solicitacao):
    grupo, _ = GrupoMedicao.objects.get_or_create(
        nome=GrupoMedicao.ESCOLA_ABERTA,
        defaults={"ativo": True},
    )
    return baker.make(
        "Medicao",
        solicitacao_medicao_inicial=solicitacao,
        grupo=grupo,
    )


def _criar_valor(medicao, categoria_medicao, nome_campo, valor="10"):
    return baker.make(
        "ValorMedicao",
        medicao=medicao,
        dia="01",
        nome_campo=nome_campo,
        categoria_medicao=categoria_medicao,
        valor=valor,
    )


def test_nao_valida_quando_escola_nao_possui_cadastro(
    solicitacao_medicao_inicial,
):
    lista_erros = validate_lancamento_alimentacoes_escola_aberta(
        solicitacao_medicao_inicial, []
    )

    assert lista_erros == []


def test_valida_quando_bloco_existe_sem_medicao(
    solicitacao_medicao_inicial,
    tipo_alimentacao_lanche,
):
    _criar_cadastro_escola_aberta(
        solicitacao_medicao_inicial.escola, [tipo_alimentacao_lanche]
    )

    lista_erros = validate_lancamento_alimentacoes_escola_aberta(
        solicitacao_medicao_inicial, []
    )

    assert lista_erros == [
        {
            "periodo_escolar": GrupoMedicao.ESCOLA_ABERTA,
            "erro": constants.StringsValidationErrors.RESTAM_DIAS_A_SEREM_LANCADOS.value,
        }
    ]


def test_valida_quando_falta_preenchimento_de_tipo_cadastrado(
    solicitacao_medicao_inicial,
    categoria_medicao,
    tipo_alimentacao_lanche,
    tipo_alimentacao_refeicao,
):
    _criar_cadastro_escola_aberta(
        solicitacao_medicao_inicial.escola,
        [tipo_alimentacao_lanche, tipo_alimentacao_refeicao],
    )
    medicao = _criar_medicao_escola_aberta(solicitacao_medicao_inicial)
    _criar_valor(medicao, categoria_medicao, "lanche")

    lista_erros = validate_lancamento_alimentacoes_escola_aberta(
        solicitacao_medicao_inicial, []
    )

    assert lista_erros == [
        {
            "periodo_escolar": GrupoMedicao.ESCOLA_ABERTA,
            "erro": constants.StringsValidationErrors.RESTAM_DIAS_A_SEREM_LANCADOS.value,
        }
    ]


def test_nao_valida_quando_todos_os_valores_estao_preenchidos(
    solicitacao_medicao_inicial,
    categoria_medicao,
    tipo_alimentacao_lanche,
    tipo_alimentacao_refeicao,
):
    _criar_cadastro_escola_aberta(
        solicitacao_medicao_inicial.escola,
        [tipo_alimentacao_lanche, tipo_alimentacao_refeicao],
    )
    medicao = _criar_medicao_escola_aberta(solicitacao_medicao_inicial)

    for nome_campo in ["lanche", "refeicao", "repeticao_refeicao"]:
        _criar_valor(medicao, categoria_medicao, nome_campo)

    lista_erros = validate_lancamento_alimentacoes_escola_aberta(
        solicitacao_medicao_inicial, []
    )

    assert lista_erros == []


def test_valida_para_ceu_gestao(
    solicitacao_medicao_inicial,
    tipo_alimentacao_lanche,
):
    tipo_unidade_ceu_gestao = baker.make(
        "TipoUnidadeEscolar",
        iniciais=constants.TIPOS_UNIDADE_ESCOLAR.CEU_GESTAO.value,
    )
    solicitacao_medicao_inicial.escola.tipo_unidade = tipo_unidade_ceu_gestao
    solicitacao_medicao_inicial.escola.save()

    _criar_cadastro_escola_aberta(
        solicitacao_medicao_inicial.escola, [tipo_alimentacao_lanche]
    )

    lista_erros = validate_lancamento_alimentacoes_escola_aberta(
        solicitacao_medicao_inicial, []
    )

    assert lista_erros == [
        {
            "periodo_escolar": GrupoMedicao.ESCOLA_ABERTA,
            "erro": constants.StringsValidationErrors.RESTAM_DIAS_A_SEREM_LANCADOS.value,
        }
    ]


def test_nao_valida_para_tipo_de_escola_nao_permitido(
    solicitacao_medicao_inicial,
    tipo_alimentacao_lanche,
):
    tipo_unidade_cei = baker.make(
        "TipoUnidadeEscolar",
        iniciais=constants.TIPOS_UNIDADE_ESCOLAR.CEI.value,
    )
    solicitacao_medicao_inicial.escola.tipo_unidade = tipo_unidade_cei
    solicitacao_medicao_inicial.escola.save()

    _criar_cadastro_escola_aberta(
        solicitacao_medicao_inicial.escola, [tipo_alimentacao_lanche]
    )

    lista_erros = validate_lancamento_alimentacoes_escola_aberta(
        solicitacao_medicao_inicial, []
    )

    assert lista_erros == []
