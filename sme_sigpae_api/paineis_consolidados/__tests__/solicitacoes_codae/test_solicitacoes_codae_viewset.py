from freezegun.api import freeze_time
from rest_framework import status

from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario
from sme_sigpae_api.inclusao_alimentacao.models import GrupoInclusaoAlimentacaoNormal


@freeze_time("2025-01-13")
def test_pendentes_autorizacao_secao_pendencias(
    client_autenticado_codae_paineis_consolidados,
    grupo_inclusao_alimentacao_normal_factory,
    quantidade_por_periodo_factory,
    inclusao_alimentacao_normal_factory,
    log_solicitacoes_usuario_factory,
    escola,
):
    client, usuario = client_autenticado_codae_paineis_consolidados

    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.diretoria_regional,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_VALIDADO,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14", grupo_inclusao=grupo_inclusao_alimentacao_normal
    )
    quantidade_por_periodo_factory.create(
        grupo_inclusao_normal=grupo_inclusao_alimentacao_normal
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
        usuario=usuario,
    )

    response = client.get(
        "/codae-solicitacoes/pendentes-autorizacao/sem_filtro/tipo_solicitacao/?limit=6&offset=0"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": {
            "Inclusão de Alimentação": {
                "LIMITE": 0,
                "PRIORITARIO": 1,
                "REGULAR": 0,
                "TOTAL": 1,
            }
        }
    }


@freeze_time("2025-01-13")
def test_pendentes_autorizacao_sem_filtro(
    client_autenticado_codae_paineis_consolidados,
    grupo_inclusao_alimentacao_normal_factory,
    quantidade_por_periodo_factory,
    inclusao_alimentacao_normal_factory,
    log_solicitacoes_usuario_factory,
    escola,
):
    client, usuario = client_autenticado_codae_paineis_consolidados

    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.diretoria_regional,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.DRE_VALIDADO,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14", grupo_inclusao=grupo_inclusao_alimentacao_normal
    )
    quantidade_por_periodo_factory.create(
        grupo_inclusao_normal=grupo_inclusao_alimentacao_normal
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.DRE_VALIDOU,
        usuario=usuario,
    )

    response = client.get("/codae-solicitacoes/pendentes-autorizacao/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1


@freeze_time("2025-01-13")
def test_questionamentos(
    client_autenticado_codae_paineis_consolidados,
    grupo_inclusao_alimentacao_normal_factory,
    quantidade_por_periodo_factory,
    inclusao_alimentacao_normal_factory,
    log_solicitacoes_usuario_factory,
    escola,
):
    client, usuario = client_autenticado_codae_paineis_consolidados

    grupo_inclusao_alimentacao_normal = (
        grupo_inclusao_alimentacao_normal_factory.create(
            escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.diretoria_regional,
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_QUESTIONADO,
        )
    )
    inclusao_alimentacao_normal_factory.create(
        data="2025-01-14", grupo_inclusao=grupo_inclusao_alimentacao_normal
    )
    quantidade_por_periodo_factory.create(
        grupo_inclusao_normal=grupo_inclusao_alimentacao_normal
    )
    log_solicitacoes_usuario_factory.create(
        uuid_original=grupo_inclusao_alimentacao_normal.uuid,
        status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU,
        usuario=usuario,
    )

    response = client.get("/codae-solicitacoes/questionamentos/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
