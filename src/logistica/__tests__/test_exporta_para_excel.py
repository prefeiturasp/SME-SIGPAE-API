import pytest

from src.logistica.api.helpers import (
    retorna_dados_normalizados_excel_entregas_distribuidor,
    retorna_dados_normalizados_excel_visao_dilog,
)

from ...dados_comuns.fluxo_status import GuiaRemessaWorkFlow
from ..api.services.exporta_para_excel import RequisicoesExcelService
from ..models.solicitacao import SolicitacaoRemessa

pytestmark = pytest.mark.django_db


def test_exportar_entregas(solicitacao):
    perfil1 = "DILOG"
    perfil2 = "DISTRIBUIDOR"
    perfil3 = "DRE"
    tem_conferencia = True
    tem_insucesso = True
    queryset = SolicitacaoRemessa.objects.filter(uuid=str(solicitacao.uuid))

    queryset_insucesso = SolicitacaoRemessa.objects.filter(
        uuid=str(solicitacao.uuid),
        guias__status=GuiaRemessaWorkFlow.DISTRIBUIDOR_REGISTRA_INSUCESSO,
    )

    requisicoes_insucesso = (
        retorna_dados_normalizados_excel_entregas_distribuidor(queryset_insucesso)
        if tem_insucesso
        else None
    )
    requisicoes = retorna_dados_normalizados_excel_entregas_distribuidor(queryset)

    arquivo1 = RequisicoesExcelService.exportar_entregas(
        requisicoes,
        requisicoes_insucesso,
        perfil1,
        tem_conferencia,
        tem_insucesso,
        is_async=True,
    )
    arquivo2 = RequisicoesExcelService.exportar_entregas(
        requisicoes,
        requisicoes_insucesso,
        perfil2,
        tem_conferencia,
        tem_insucesso,
        is_async=True,
    )
    arquivo3 = RequisicoesExcelService.exportar_entregas(
        requisicoes,
        requisicoes_insucesso,
        perfil3,
        tem_conferencia,
        tem_insucesso,
        is_async=True,
    )
    assert arquivo1 != ""
    assert arquivo1 is not None
    assert len(arquivo1) > 0
    assert arquivo2 != ""
    assert arquivo2 is not None
    assert len(arquivo2) > 0
    assert arquivo3 != ""
    assert arquivo3 is not None
    assert len(arquivo3) > 0


def test_exportar_visao_dilog_e_distribuidor(
    solicitacao, guia, alimento, escola, lote, guia_com_escola_client_autenticado
):
    queryset = SolicitacaoRemessa.objects.filter(id__in=[solicitacao.id])

    requisicoes = retorna_dados_normalizados_excel_visao_dilog(queryset)
    arquivo = RequisicoesExcelService.exportar_visao_dilog(
        requisicoes=requisicoes, is_async=True
    )

    assert arquivo != ""
    assert arquivo is not None
    assert len(arquivo) > 0
