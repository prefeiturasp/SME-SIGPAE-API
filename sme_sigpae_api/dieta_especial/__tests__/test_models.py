import pytest
import xworkflows

from ...dados_comuns.models import LogSolicitacoesUsuario
from ..models import (
    LogDietasAtivasCanceladasAutomaticamente,
    ProtocoloPadraoDietaEspecial,
)

pytestmark = pytest.mark.django_db


def test_solicitacao_dieta_especial_obj(solicitacao_dieta_especial):
    assert solicitacao_dieta_especial.__str__() == "123456: Roberto Alves da Silva"
    assert solicitacao_dieta_especial.escola == solicitacao_dieta_especial.rastro_escola


def test_termina_dieta_especial_erro_status_invalido(
    solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas, usuario_admin
):
    for solicitacao in solicitacoes_dieta_especial_nao_autorizadas_e_nao_ativas:
        try:
            solicitacao.termina(usuario_admin)
        except xworkflows.InvalidTransitionError as e:
            assert str(e) == "Só é permitido terminar dietas autorizadas e ativas"


def test_termina_dieta_especial_erro_ativas_sem_dt_termino(
    solicitacao_dieta_especial_autorizada_ativa, usuario_admin
):
    try:
        solicitacao_dieta_especial_autorizada_ativa.termina(usuario_admin)
    except xworkflows.InvalidTransitionError as e:
        assert str(e) == "Não pode terminar uma dieta sem data de término"


def test_termina_dieta_especial_erro_dt_termino_posterior_hoje(
    solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior, usuario_admin
):
    for solicitacao in solicitacoes_dieta_especial_dt_termino_hoje_ou_posterior:
        try:
            solicitacao.termina(usuario_admin)
        except xworkflows.InvalidTransitionError as e:
            assert str(e) == "Não pode terminar uma dieta antes da data"


def test_termina_dieta_especial_erro_dieta_inativa(
    solicitacoes_dieta_especial_dt_termino_ontem_inativas, usuario_admin
):
    for solicitacao in solicitacoes_dieta_especial_dt_termino_ontem_inativas:
        try:
            solicitacao.termina(usuario_admin)
        except xworkflows.InvalidTransitionError as e:
            assert str(e) == "Só é permitido terminar dietas autorizadas e ativas"


def test_termina_dieta_especial(
    solicitacoes_dieta_especial_dt_termino_ontem_ativas, usuario_admin
):
    for solicitacao in solicitacoes_dieta_especial_dt_termino_ontem_ativas:
        solicitacao.termina(usuario_admin)
        ultimo_log = solicitacao.logs.last()
        assert ultimo_log.usuario_id == usuario_admin.id
        assert (
            ultimo_log.justificativa
            == "Atingiu data limite e foi terminada automaticamente"
        )


def test_solicitacao_dieta_especial_transicao_cancelar_automaticamente(
    solicitacao_dieta_especial_autorizada, usuario_admin
):
    solicitacao_dieta_especial_autorizada.cancelar_aluno_mudou_escola(
        user=usuario_admin
    )
    ultimo_log = solicitacao_dieta_especial_autorizada.logs.last()
    assert ultimo_log.usuario_id == usuario_admin.id
    assert (
        ultimo_log.status_evento == LogSolicitacoesUsuario.CANCELADO_ALUNO_MUDOU_ESCOLA
    )


def test_solicitacao_dieta_especial_transicao_cancelar_fora_da_rede(
    solicitacao_dieta_especial_autorizada, usuario_admin
):
    solicitacao_dieta_especial_autorizada.cancelar_aluno_nao_pertence_rede(
        user=usuario_admin
    )
    ultimo_log = solicitacao_dieta_especial_autorizada.logs.last()
    assert ultimo_log.usuario_id == usuario_admin.id
    assert (
        ultimo_log.status_evento
        == LogSolicitacoesUsuario.CANCELADO_ALUNO_NAO_PERTENCE_REDE
    )


def test_instance_model(log_dietas_ativas_canceladas_automaticamente):
    model = log_dietas_ativas_canceladas_automaticamente
    assert isinstance(model, LogDietasAtivasCanceladasAutomaticamente)
    assert model.dieta
    assert model.codigo_eol_aluno
    assert model.nome_aluno
    assert model.codigo_eol_escola_origem
    assert model.nome_escola_origem
    assert model.codigo_eol_escola_destino
    assert model.nome_escola_destino


def test_instance_model_protocolo_padrao(protocolo_padrao_dieta_especial):
    assert isinstance(protocolo_padrao_dieta_especial, ProtocoloPadraoDietaEspecial)
    assert protocolo_padrao_dieta_especial.nome_protocolo
    assert protocolo_padrao_dieta_especial.status


def test_srt_model(protocolo_padrao_dieta_especial):
    assert protocolo_padrao_dieta_especial.__str__() == "ALERGIA A AVEIA"


def test_meta_modelo(protocolo_padrao_dieta_especial):
    assert (
        protocolo_padrao_dieta_especial._meta.verbose_name
        == "Protocolo padrão de dieta especial"
    )
    assert (
        protocolo_padrao_dieta_especial._meta.verbose_name_plural
        == "Protocolos padrões de dieta especial"
    )
