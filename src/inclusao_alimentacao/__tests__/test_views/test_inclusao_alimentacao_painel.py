import datetime

import pytest
from rest_framework import status

from src.dados_comuns.constants import PEDIDOS_CODAE, PEDIDOS_DRE, SEM_FILTRO

pytestmark = pytest.mark.django_db


def _cria_pedidos(
    escola,
    grupo_inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_da_cei_factory,
    quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory,
    dias_motivos_inclusao_de_alimentacao_cei_factory,
    inclusao_alimentacao_continua_factory,
    inclusao_de_alimentacao_cemei_factory,
    dias_motivos_inclusao_de_alimentacao_cemei_factory,
    status_pedido,
    data,
):
    grupo = grupo_inclusao_alimentacao_normal_factory.create(
        escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        status=status_pedido,
    )
    inclusao_alimentacao_normal_factory.create(grupo_inclusao=grupo, data=data)

    cei = inclusao_alimentacao_da_cei_factory.create(
        escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        status=status_pedido,
    )
    quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory.create(
        inclusao_alimentacao_da_cei=cei,
    )
    dias_motivos_inclusao_de_alimentacao_cei_factory.create(inclusao_cei=cei, data=data)

    inclusao_alimentacao_continua_factory.create(
        escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        data_inicial=data,
        data_final=data,
        status=status_pedido,
    )

    cemei = inclusao_de_alimentacao_cemei_factory.create(
        escola=escola,
        rastro_lote=escola.lote,
        rastro_dre=escola.diretoria_regional,
        status=status_pedido,
    )
    dias_motivos_inclusao_de_alimentacao_cemei_factory.create(
        inclusao_alimentacao_cemei=cemei, data=data
    )


def test_solicitacoes_diretoria_regional_unificado(
    client_autenticado_vinculo_dre_inclusao,
    escola,
    eolservicosgp_get_lista_alunos,
    periodo_escolar,
    grupo_inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_da_cei_factory,
    quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory,
    dias_motivos_inclusao_de_alimentacao_cei_factory,
    inclusao_alimentacao_continua_factory,
    inclusao_de_alimentacao_cemei_factory,
    dias_motivos_inclusao_de_alimentacao_cemei_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    _cria_pedidos(
        escola,
        grupo_inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_da_cei_factory,
        quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory,
        dias_motivos_inclusao_de_alimentacao_cei_factory,
        inclusao_alimentacao_continua_factory,
        inclusao_de_alimentacao_cemei_factory,
        dias_motivos_inclusao_de_alimentacao_cemei_factory,
        status_pedido="DRE_A_VALIDAR",
        data=data,
    )

    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusao-alimentacao/{PEDIDOS_DRE}/{SEM_FILTRO}/?prazo=REGULAR"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert dados["count"] == 4
    assert len(dados["results"]) == 4
    assert dados["escolas_solicitantes"] == 1
    assert dados["totais"]["REGULAR"] == 4


def test_solicitacoes_diretoria_regional_unificado_busca(
    client_autenticado_vinculo_dre_inclusao,
    escola,
    eolservicosgp_get_lista_alunos,
    periodo_escolar,
    grupo_inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_da_cei_factory,
    quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory,
    dias_motivos_inclusao_de_alimentacao_cei_factory,
    inclusao_alimentacao_continua_factory,
    inclusao_de_alimentacao_cemei_factory,
    dias_motivos_inclusao_de_alimentacao_cemei_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    _cria_pedidos(
        escola,
        grupo_inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_da_cei_factory,
        quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory,
        dias_motivos_inclusao_de_alimentacao_cei_factory,
        inclusao_alimentacao_continua_factory,
        inclusao_de_alimentacao_cemei_factory,
        dias_motivos_inclusao_de_alimentacao_cemei_factory,
        status_pedido="DRE_A_VALIDAR",
        data=data,
    )

    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusao-alimentacao/{PEDIDOS_DRE}/{SEM_FILTRO}/"
        f"?prazo=REGULAR&busca={escola.codigo_eol}"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 4

    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusao-alimentacao/{PEDIDOS_DRE}/{SEM_FILTRO}/"
        f"?prazo=REGULAR&busca=zzzzzz"
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


def test_solicitacoes_codae_unificado(
    client_autenticado_vinculo_codae_inclusao,
    escola,
    eolservicosgp_get_lista_alunos,
    periodo_escolar,
    grupo_inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_normal_factory,
    inclusao_alimentacao_da_cei_factory,
    quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory,
    dias_motivos_inclusao_de_alimentacao_cei_factory,
    inclusao_alimentacao_continua_factory,
    inclusao_de_alimentacao_cemei_factory,
    dias_motivos_inclusao_de_alimentacao_cemei_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    _cria_pedidos(
        escola,
        grupo_inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_normal_factory,
        inclusao_alimentacao_da_cei_factory,
        quantidade_de_alunos_por_faixa_etaria_da_inclusao_de_alimentacao_da_cei_factory,
        dias_motivos_inclusao_de_alimentacao_cei_factory,
        inclusao_alimentacao_continua_factory,
        inclusao_de_alimentacao_cemei_factory,
        dias_motivos_inclusao_de_alimentacao_cemei_factory,
        status_pedido="DRE_VALIDADO",
        data=data,
    )

    response = client_autenticado_vinculo_codae_inclusao.get(
        f"/inclusao-alimentacao/{PEDIDOS_CODAE}/{SEM_FILTRO}/?prazo=REGULAR"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert dados["count"] == 4
    assert len(dados["results"]) == 4
    assert dados["escolas_solicitantes"] == 1


def test_solicitacoes_diretoria_regional_unificado_paginacao(
    client_autenticado_vinculo_dre_inclusao,
    escola,
    inclusao_alimentacao_continua_factory,
):
    data = datetime.date.today() + datetime.timedelta(days=30)
    for _ in range(15):
        inclusao_alimentacao_continua_factory.create(
            escola=escola,
            rastro_lote=escola.lote,
            rastro_dre=escola.diretoria_regional,
            data_inicial=data,
            data_final=data,
            status="DRE_A_VALIDAR",
        )

    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusao-alimentacao/{PEDIDOS_DRE}/{SEM_FILTRO}/?prazo=REGULAR"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert dados["count"] == 15
    assert len(dados["results"]) == 10

    response = client_autenticado_vinculo_dre_inclusao.get(
        f"/inclusao-alimentacao/{PEDIDOS_DRE}/{SEM_FILTRO}/?prazo=REGULAR&page=2"
    )
    assert response.status_code == status.HTTP_200_OK
    dados = response.json()
    assert len(dados["results"]) == 5
