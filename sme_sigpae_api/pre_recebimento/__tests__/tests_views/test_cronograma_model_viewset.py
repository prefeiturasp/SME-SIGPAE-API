import pytest
from django.urls import reverse
from rest_framework import status

from sme_sigpae_api.dados_comuns.constants import DJANGO_ADMIN_PASSWORD
from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
    Cronograma,
    SolicitacaoAlteracaoCronograma,
)
from sme_sigpae_api.terceirizada.models import Terceirizada

pytestmark = pytest.mark.django_db


def test_post_cronogramas(
    client_autenticado_vinculo_dilog_cronograma,
    contrato_factory,
    empresa_factory,
    ficha_tecnica_factory,
    unidade_medida_factory,
    tipo_embalagem_qld_factory,
):
    client, _ = client_autenticado_vinculo_dilog_cronograma
    empresa = empresa_factory(tipo_servico=Terceirizada.FORNECEDOR)
    contrato = contrato_factory(terceirizada=empresa)
    ficha_tecnica = ficha_tecnica_factory()
    armazem = empresa_factory(tipo_servico=Terceirizada.DISTRIBUIDOR_ARMAZEM)
    unidade_medida = unidade_medida_factory()
    tipo_embalagem_qld = tipo_embalagem_qld_factory()

    payload = {
        "cadastro_finalizado": True,
        "contrato": f"{contrato.uuid}",
        "empresa": f"{empresa.uuid}",
        "ficha_tecnica": f"{ficha_tecnica.uuid}",
        "armazem": f"{armazem.uuid}",
        "qtd_total_programada": "10",
        "unidade_medida": f"{unidade_medida.uuid}",
        "tipo_embalagem_secundaria": f"{tipo_embalagem_qld.uuid}",
        "custo_unitario_produto": 1.59,
        "etapas": [
            {
                "numero_empenho": "10",
                "qtd_total_empenho": 10,
                "etapa": 1,
                "data_programada": "2024-07-29",
                "quantidade": "10",
                "total_embalagens": "10",
            }
        ],
        "programacoes_de_recebimento": [{}],
        "password": DJANGO_ADMIN_PASSWORD,
    }
    response = client.post(f"/cronogramas/", payload)

    assert response.status_code == status.HTTP_201_CREATED


def test_fornecedor_ciente_nao_aplica_alteracoes_se_ja_assinado_codae(
    client_user_autenticado_fornecedor,
    solicitacao_alteracao_cronograma,
):
    client, user = client_user_autenticado_fornecedor
    solicitacao = solicitacao_alteracao_cronograma
    cronograma = solicitacao.cronograma

    cronograma.status = Cronograma.workflow_class.ASSINADO_CODAE
    cronograma.save(update_fields=["status"])

    solicitacao.status = (
        SolicitacaoAlteracaoCronograma.workflow_class.ALTERACAO_ENVIADA_FORNECEDOR
    )
    solicitacao.save(update_fields=["status"])

    qtd_antes = cronograma.qtd_total_programada
    etapas_antes = list(cronograma.etapas.values_list("id", flat=True))
    programacoes_antes = list(
        cronograma.programacoes_de_recebimento.values_list("id", flat=True)
    )

    url = reverse(
        "solicitacao-de-alteracao-de-cronograma-fornecedor-ciente",
        kwargs={"uuid": solicitacao.uuid},
    )

    response = client.patch(
        url,
        data={"password": DJANGO_ADMIN_PASSWORD},
    )

    assert response.status_code == status.HTTP_200_OK, response.data

    cronograma.refresh_from_db()

    assert cronograma.status == Cronograma.workflow_class.ASSINADO_CODAE
    assert cronograma.qtd_total_programada == qtd_antes
    assert list(cronograma.etapas.values_list("id", flat=True)) == etapas_antes
    assert (
        list(cronograma.programacoes_de_recebimento.values_list("id", flat=True))
        == programacoes_antes
    )


def test_fornecedor_ciente_aplica_alteracoes_se_nao_assinado_codae(
    client_user_autenticado_fornecedor,
    solicitacao_alteracao_cronograma,
    django_user_model,
):
    from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import (
        Cronograma,
        SolicitacaoAlteracaoCronograma,
    )

    client, user = client_user_autenticado_fornecedor
    solicitacao = solicitacao_alteracao_cronograma
    cronograma = solicitacao.cronograma

    cronograma.status = Cronograma.workflow_class.ALTERACAO_CODAE
    cronograma.save(update_fields=["status"])

    solicitacao.status = (
        SolicitacaoAlteracaoCronograma.workflow_class.ALTERACAO_ENVIADA_FORNECEDOR
    )
    solicitacao.save(update_fields=["status"])

    cronograma.salvar_log_transicao(
        status_evento=LogSolicitacoesUsuario.CODAE_ALTERA_CRONOGRAMA,
        usuario=user,
    )

    usuario_codae = django_user_model.objects.create_user(
        username="codae@test.com",
        password="adminadmin",
        email="codae@test.com",
    )
    cronograma.salvar_log_transicao(
        status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELA_CODAE,
        usuario=usuario_codae,
    )

    url = reverse(
        "solicitacao-de-alteracao-de-cronograma-fornecedor-ciente",
        kwargs={"uuid": solicitacao.uuid},
    )

    response = client.patch(
        url,
        data={"password": DJANGO_ADMIN_PASSWORD},
    )

    assert response.status_code == status.HTTP_200_OK, response.data

    cronograma.refresh_from_db()

    assert cronograma.status == Cronograma.workflow_class.ASSINADO_CODAE
    assert cronograma.qtd_total_programada == solicitacao.qtd_total_programada

    assert list(cronograma.etapas.values_list("id", flat=True)) == list(
        solicitacao.etapas_novas.values_list("id", flat=True)
    )

    assert list(
        cronograma.programacoes_de_recebimento.values_list("id", flat=True)
    ) == list(solicitacao.programacoes_novas.values_list("id", flat=True))
