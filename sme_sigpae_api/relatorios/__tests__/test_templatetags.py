import pytest

from sme_sigpae_api.cardapio.api.serializers.serializers import (
    GrupoSuspensaoAlimentacaoSerializer,
)
from sme_sigpae_api.relatorios.templatetags.index import (
    existe_suspensoes_cancelada,
    suspensoes_canceladas,
)

from ...dados_comuns import constants
from ...dados_comuns.models import LogSolicitacoesUsuario


def test_aceita_nao_aceita_str():
    from ..templatetags.index import (  # XXX: bug no teste de template nao registrado
        aceita_nao_aceita_str,
    )

    assert aceita_nao_aceita_str(False) == "Não aceitou"
    assert aceita_nao_aceita_str(True) == "Aceitou"


def test_class_css():
    from ..templatetags.index import (  # XXX: bug no teste de template nao registrado
        class_css,
    )

    status_dic = dict((x, y) for x, y in LogSolicitacoesUsuario.STATUS_POSSIVEIS)

    class FakeSolicitacao:
        def __init__(self, status_evento_explicacao):
            self.status_evento_explicacao = status_evento_explicacao

    solicitacao_terc_quest = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO)
    )
    solicitacao_dre_revisou = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.DRE_REVISOU)
    )
    solicitacao_codae_aut = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.CODAE_AUTORIZOU)
    )
    solicitacao_codae_neg_intv = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.CODAE_NEGOU_INATIVACAO)
    )
    solicitacao_codae_neg = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.CODAE_NEGOU)
    )
    solicitacao_escola_canc = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.ESCOLA_CANCELOU)
    )
    solicitacao_codae_quest = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.CODAE_QUESTIONOU)
    )

    assert class_css(solicitacao_terc_quest) == "questioned"
    assert class_css(solicitacao_dre_revisou) == "active"
    assert class_css(solicitacao_codae_aut) == "active"
    assert class_css(solicitacao_codae_neg_intv) == "disapproved"
    assert class_css(solicitacao_codae_neg) == "disapproved"
    assert class_css(solicitacao_escola_canc) == "cancelled"
    assert class_css(solicitacao_codae_quest) == "questioned"


def test_fim_de_fluxo():
    from ..templatetags.index import (  # XXX: bug no teste de template nao registrado
        fim_de_fluxo,
    )

    status_dic = dict((x, y) for x, y in LogSolicitacoesUsuario.STATUS_POSSIVEIS)

    class FakeSolicitacao:
        def __init__(self, status_evento_explicacao):
            self.status_evento_explicacao = status_evento_explicacao

    solicitacao_codae_negado = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.CODAE_NEGOU)
    )
    solicitacao_dre_revisou = FakeSolicitacao(
        status_dic.get(LogSolicitacoesUsuario.DRE_REVISOU)
    )
    assert fim_de_fluxo([solicitacao_codae_negado]) is True
    assert fim_de_fluxo([solicitacao_dre_revisou]) is False


def test_obter_titulo_log_reclamacao():
    from ..templatetags.index import obter_titulo_log_reclamacao

    titulo_log = obter_titulo_log_reclamacao(
        constants.TERCEIRIZADA_RESPONDEU_RECLAMACAO
    )
    assert titulo_log == "Resposta terceirizada"
    titulo_log = obter_titulo_log_reclamacao(constants.CODAE_QUESTIONOU_TERCEIRIZADA)
    assert titulo_log == "Questionamento CODAE"
    titulo_log = obter_titulo_log_reclamacao(constants.CODAE_AUTORIZOU_RECLAMACAO)
    assert titulo_log == "Justificativa avaliação CODAE"
    titulo_log = obter_titulo_log_reclamacao(constants.CODAE_RECUSOU_RECLAMACAO)
    assert titulo_log == "Justificativa avaliação CODAE"
    titulo_log = obter_titulo_log_reclamacao(constants.CODAE_RESPONDEU_RECLAMACAO)
    assert titulo_log == "Resposta CODAE"


def test_obter_rotulo_data_log():
    from ..templatetags.index import obter_rotulo_data_log

    rotulo_data_log = obter_rotulo_data_log(constants.TERCEIRIZADA_RESPONDEU_RECLAMACAO)
    assert rotulo_data_log == "Data resposta terc."
    rotulo_data_log = obter_rotulo_data_log(constants.CODAE_QUESTIONOU_TERCEIRIZADA)
    assert rotulo_data_log == "Data quest. CODAE"
    rotulo_data_log = obter_rotulo_data_log(constants.CODAE_AUTORIZOU_RECLAMACAO)
    assert rotulo_data_log == "Data avaliação CODAE"
    rotulo_data_log = obter_rotulo_data_log(constants.CODAE_RECUSOU_RECLAMACAO)
    assert rotulo_data_log == "Data avaliação CODAE"
    rotulo_data_log = obter_rotulo_data_log(constants.CODAE_RESPONDEU_RECLAMACAO)
    assert rotulo_data_log == "Data resposta CODAE"


@pytest.mark.django_db
def test_existe_suspensoes_cancelada_status_escola_cancelou(
    grupo_suspensao_alimentacao_cancelamento_total,
):
    assert (
        existe_suspensoes_cancelada(grupo_suspensao_alimentacao_cancelamento_total)
        is True
    )


@pytest.mark.django_db
def test_existe_suspensoes_cancelada_com_justificativa(
    grupo_suspensao_alimentacao_cancelamento_parcial,
):
    assert (
        existe_suspensoes_cancelada(grupo_suspensao_alimentacao_cancelamento_parcial)
        is True
    )


@pytest.mark.django_db
def test_existe_suspensoes_cancelada_sem_cancelamentos(grupo_suspensao_alimentacao):
    assert existe_suspensoes_cancelada(grupo_suspensao_alimentacao) is False


@pytest.mark.django_db
def test_existe_suspensoes_cancelada_com_dicionario(
    grupo_suspensao_alimentacao_cancelamento_total,
):
    serializer = GrupoSuspensaoAlimentacaoSerializer(
        grupo_suspensao_alimentacao_cancelamento_total
    )
    assert existe_suspensoes_cancelada(serializer.data) is True


@pytest.mark.django_db
def test_suspensoes_canceladas_status_escola_cancelou(
    grupo_suspensao_alimentacao_cancelamento_total,
):
    resultado = suspensoes_canceladas(grupo_suspensao_alimentacao_cancelamento_total)

    assert len(resultado) == 5
    assert set(resultado) == set(
        grupo_suspensao_alimentacao_cancelamento_total.suspensoes_alimentacao.all()
    )


@pytest.mark.django_db
def test_suspensoes_canceladas_com_justificativa(
    grupo_suspensao_alimentacao_cancelamento_parcial,
):
    resultado = suspensoes_canceladas(grupo_suspensao_alimentacao_cancelamento_parcial)
    assert len(resultado) == 2


@pytest.mark.django_db
def test_suspensoes_canceladas_sem_cancelamentos(grupo_suspensao_alimentacao):
    resultado = suspensoes_canceladas(grupo_suspensao_alimentacao)
    assert len(resultado) == 0
