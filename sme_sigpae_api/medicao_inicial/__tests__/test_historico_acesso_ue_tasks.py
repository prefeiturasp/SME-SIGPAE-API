import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from model_bakery import baker

from sme_sigpae_api.medicao_inicial.historico_acesso_ue.models import (
    HistoricoAcessoMedicaoInicialUE,
)
from sme_sigpae_api.medicao_inicial.historico_acesso_ue.tasks import (
    cria_historico_acesso_ue,
    finaliza_historico_acesso_ue,
)

pytestmark = pytest.mark.django_db


def _cria_escola_elegivel(codigo_eol, lote, tipo_gestao):
    return baker.make(
        "Escola",
        codigo_eol=codigo_eol,
        ativo=True,
        lote=lote,
        acesso_modulo_medicao_inicial=True,
        tipo_gestao=tipo_gestao,
    )


@freeze_time("2026-04-15")
def test_cria_historico_acesso_ue_cria_apenas_historicos_para_escolas_elegiveis():
    hoje = datetime.date.today()
    usuario_sistema = baker.make("perfil.Usuario", id=1)
    tipo_gestao_terc_total = baker.make("TipoGestao", nome="TERC TOTAL")
    tipo_gestao_parceira = baker.make("TipoGestao", nome="PARCEIRA")
    lote = baker.make("Lote", nome="Lote 01", tipo_gestao=tipo_gestao_terc_total)

    escola_sem_historico = _cria_escola_elegivel("100001", lote, tipo_gestao_terc_total)
    escola_com_historico_hoje = _cria_escola_elegivel(
        "100002", lote, tipo_gestao_terc_total
    )
    escola_com_historico_futuro = _cria_escola_elegivel(
        "100003", lote, tipo_gestao_terc_total
    )

    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola_com_historico_hoje,
        lote=lote,
        data_inicial=hoje,
        data_final=None,
        criado_por=usuario_sistema,
    )
    baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola_com_historico_futuro,
        lote=lote,
        data_inicial=hoje + datetime.timedelta(days=1),
        data_final=None,
        criado_por=usuario_sistema,
    )

    baker.make(
        "Escola",
        codigo_eol="100004",
        ativo=False,
        lote=lote,
        acesso_modulo_medicao_inicial=True,
        tipo_gestao=tipo_gestao_terc_total,
    )
    baker.make(
        "Escola",
        codigo_eol="100005",
        ativo=True,
        lote=None,
        acesso_modulo_medicao_inicial=True,
        tipo_gestao=tipo_gestao_terc_total,
    )
    baker.make(
        "Escola",
        codigo_eol="100006",
        ativo=True,
        lote=lote,
        acesso_modulo_medicao_inicial=False,
        tipo_gestao=tipo_gestao_terc_total,
    )
    baker.make(
        "Escola",
        codigo_eol="100007",
        ativo=True,
        lote=lote,
        acesso_modulo_medicao_inicial=True,
        tipo_gestao=tipo_gestao_parceira,
    )

    with patch(
        "sme_sigpae_api.medicao_inicial.historico_acesso_ue.tasks.HistoricoAcessoMedicaoInicialUE.objects.bulk_create",
        wraps=HistoricoAcessoMedicaoInicialUE.objects.bulk_create,
    ) as mock_bulk_create:
        quantidade_criada = cria_historico_acesso_ue()

    assert quantidade_criada == 1
    mock_bulk_create.assert_called_once()
    assert len(mock_bulk_create.call_args.args[0]) == 1

    historico_criado = HistoricoAcessoMedicaoInicialUE.objects.get(
        escola=escola_sem_historico,
        data_inicial=hoje,
        data_final=None,
    )
    assert historico_criado.lote == lote
    assert historico_criado.criado_por_id == 1

    assert (
        HistoricoAcessoMedicaoInicialUE.objects.filter(
            escola__codigo_eol__in=["100004", "100005", "100006", "100007"],
            data_inicial=hoje,
            data_final=None,
        ).count()
        == 0
    )


@freeze_time("2026-04-15")
def test_finaliza_historico_acesso_ue_inativa_apenas_historicos_com_lote_diferente():
    hoje = datetime.date.today()
    usuario_sistema = baker.make("perfil.Usuario", id=1)
    tipo_gestao_terc_total = baker.make("TipoGestao", nome="TERC TOTAL")
    lote_atual = baker.make(
        "Lote", nome="Lote Atual", tipo_gestao=tipo_gestao_terc_total
    )
    lote_antigo = baker.make(
        "Lote", nome="Lote Antigo", tipo_gestao=tipo_gestao_terc_total
    )

    escola_sem_mudanca = _cria_escola_elegivel(
        "200001", lote_atual, tipo_gestao_terc_total
    )
    escola_com_mudanca = _cria_escola_elegivel(
        "200002", lote_atual, tipo_gestao_terc_total
    )
    escola_historico_antigo = _cria_escola_elegivel(
        "200003", lote_atual, tipo_gestao_terc_total
    )

    historico_sem_mudanca = baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola_sem_mudanca,
        lote=lote_atual,
        data_inicial=hoje,
        data_final=None,
        criado_por=usuario_sistema,
    )
    historico_com_mudanca = baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola_com_mudanca,
        lote=lote_antigo,
        data_inicial=hoje,
        data_final=None,
        criado_por=usuario_sistema,
    )
    historico_antigo = baker.make(
        HistoricoAcessoMedicaoInicialUE,
        escola=escola_historico_antigo,
        lote=lote_antigo,
        data_inicial=hoje - datetime.timedelta(days=1),
        data_final=None,
        criado_por=usuario_sistema,
    )

    with patch(
        "sme_sigpae_api.medicao_inicial.historico_acesso_ue.tasks.HistoricoAcessoMedicaoInicialUE.objects.bulk_update",
        wraps=HistoricoAcessoMedicaoInicialUE.objects.bulk_update,
    ) as mock_bulk_update:
        quantidade_atualizada = finaliza_historico_acesso_ue()

    assert quantidade_atualizada == 1
    mock_bulk_update.assert_called_once()
    assert len(mock_bulk_update.call_args.args[0]) == 1

    historico_sem_mudanca.refresh_from_db()
    historico_com_mudanca.refresh_from_db()
    historico_antigo.refresh_from_db()

    assert historico_sem_mudanca.data_final is None
    assert historico_com_mudanca.data_final == hoje
    assert historico_antigo.data_final is None
