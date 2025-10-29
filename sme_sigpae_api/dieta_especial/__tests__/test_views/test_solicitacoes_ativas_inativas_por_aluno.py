from unittest.mock import MagicMock

import pytest

from sme_sigpae_api.dieta_especial.api.viewsets import (
    SolicitacoesAtivasInativasPorAlunoView,
)

pytestmark = pytest.mark.django_db


def test_solicitacoes_ativas_inativas_por_aluno_viewset(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial_factory,
    aluno_factory,
    monkeypatch,
):
    aluno = aluno_factory.create(codigo_eol="1234567")
    solicitacao_dieta_especial_factory.create(
        aluno=aluno, status="CANCELADO_ALUNO_NAO_PERTENCE_REDE", ativo=False
    )
    solicitacao_dieta_especial_factory.create(
        aluno=aluno, status="CODAE_AUTORIZADO", ativo=True
    )

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": {"total_ativas": 1, "total_inativas": 1}
    }

    monkeypatch.setattr(
        client_autenticado_vinculo_codae_dieta,
        "get",
        lambda *args, **kwargs: mock_response,
    )

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?codigo_eol=1234567&nome_aluno=&page=1"
    )

    assert response.json()["results"]["total_ativas"] == 1
    assert response.json()["results"]["total_inativas"] == 1


def test_calculo_totais_solicitacoes(aluno_factory, solicitacao_dieta_especial_factory):
    aluno = aluno_factory.create(codigo_eol="1234567")
    # Ativo com status que deve ser contado
    solicitacao_dieta_especial_factory.create(
        aluno=aluno, status="CODAE_AUTORIZADO", ativo=True
    )
    # Ativos com status que NÃO devem ser contados
    status_nao_contabilizados = [
        "CANCELADO_ALUNO_NAO_PERTENCE_REDE",
        "TERMINADA_AUTOMATICAMENTE_SISTEMA",
    ]
    for status in status_nao_contabilizados:
        solicitacao_dieta_especial_factory.create(
            aluno=aluno, status=status, ativo=True
        )

    # Inativo (deve contar como inativo)
    solicitacao_dieta_especial_factory.create(
        aluno=aluno, status="CANCELADO_ALUNO_NAO_PERTENCE_REDE", ativo=False
    )

    queryset = [aluno]
    total_ativas, total_inativas = (
        SolicitacoesAtivasInativasPorAlunoView.calcular_totais(queryset)
    )

    assert total_ativas == 1
    assert total_inativas == 1


def test_filtro_por_serie_exata_7a(
    client_autenticado_vinculo_codae_dieta, aluno_factory, solicitacao_dieta_especial_factory
):
    aluno_7a = aluno_factory.create(codigo_eol="1001", serie="7A")
    aluno_7b = aluno_factory.create(codigo_eol="1002", serie="7B")
    aluno_7c = aluno_factory.create(codigo_eol="1003", serie="7C")

    for aluno in [aluno_7a, aluno_7b, aluno_7c]:
        solicitacao_dieta_especial_factory.create(aluno=aluno, status="CODAE_AUTORIZADO", ativo=True)

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?serie=7A"
    )
    series = [r["serie"] for r in response.json()["solicitacoes"]]

    assert series == ["7A"]


def test_filtro_por_numero_7(
    client_autenticado_vinculo_codae_dieta, aluno_factory, solicitacao_dieta_especial_factory
):
    aluno_7a = aluno_factory.create(codigo_eol="1001", serie="7A")
    aluno_7b = aluno_factory.create(codigo_eol="1002", serie="7B")
    aluno_8c = aluno_factory.create(codigo_eol="1003", serie="8C")

    for aluno in [aluno_7a, aluno_7b, aluno_8c]:
        solicitacao_dieta_especial_factory.create(aluno=aluno, status="CODAE_AUTORIZADO", ativo=True)

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?serie=7"
    )
    series = [r["serie"] for r in response.json()["solicitacoes"]]

    assert sorted(series) == ["7A", "7B"]


def test_filtro_por_letra_a(
    client_autenticado_vinculo_codae_dieta, aluno_factory, solicitacao_dieta_especial_factory
):
    aluno_6a = aluno_factory.create(codigo_eol="1001", serie="6A")
    aluno_7a = aluno_factory.create(codigo_eol="1002", serie="7A")
    aluno_8a = aluno_factory.create(codigo_eol="1003", serie="8A")
    aluno_7b = aluno_factory.create(codigo_eol="1004", serie="7B")

    for aluno in [aluno_6a, aluno_7a, aluno_8a, aluno_7b]:
        solicitacao_dieta_especial_factory.create(aluno=aluno, status="CODAE_AUTORIZADO", ativo=True)

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?serie=A"
    )
    series = [r["serie"] for r in response.json()["solicitacoes"]]

    assert sorted(series) == ["6A", "7A", "8A"]


def test_filtro_por_multiplas_series(
    client_autenticado_vinculo_codae_dieta, aluno_factory, solicitacao_dieta_especial_factory
):
    aluno_6a = aluno_factory.create(codigo_eol="1001", serie="6A")
    aluno_7b = aluno_factory.create(codigo_eol="1002", serie="7B")
    aluno_7c = aluno_factory.create(codigo_eol="1003", serie="7C")

    for aluno in [aluno_6a, aluno_7b, aluno_7c]:
        solicitacao_dieta_especial_factory.create(aluno=aluno, status="CODAE_AUTORIZADO", ativo=True)

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?serie=6A&serie=7B"
    )
    series = [r["serie"] for r in response.json()["solicitacoes"]]

    assert sorted(series) == ["6A", "7B"]


def test_get_queryset_filtra_por_escola_do_vinculo_quando_usuario_e_escola(
    client_autenticado_vinculo_escola,
    django_user_model,
    escola_factory,
    aluno_factory,
    solicitacao_dieta_especial_factory,
):
    client = client_autenticado_vinculo_escola

    user = django_user_model.objects.get(username="test@test.com")
    vinculo = user.vinculos.filter(ativo=True).latest("data_inicial")
    escola_a = vinculo.instituicao

    escola_b = escola_factory.create()

    aluno_a1 = aluno_factory.create(serie="7A")
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_a1,
        status="CODAE_AUTORIZADO",
        ativo=True,
        rastro_escola=escola_a,
        tipo_solicitacao="COMUM",
    )

    aluno_a2 = aluno_factory.create(serie="7B")
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_a2,
        status="CODAE_AUTORIZADO",
        ativo=True,
        rastro_escola=escola_a,
        tipo_solicitacao="COMUM",
    )

    aluno_b1 = aluno_factory.create(serie="7C")
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_b1,
        status="CODAE_AUTORIZADO",
        ativo=True,
        rastro_escola=escola_b,
        tipo_solicitacao="COMUM",
    )

    resp = client.get("/solicitacoes-dieta-especial-ativas-inativas/")
    assert resp.status_code == 200
    series = sorted([r["serie"] for r in resp.json()["solicitacoes"]])

    assert series == ["7A", "7B"]


def test_get_queryset_filtra_por_codigo_eol_escola_quando_nao_escola(
    client_autenticado_vinculo_codae_dieta,
    escola_factory,
    aluno_factory,
    solicitacao_dieta_especial_factory,
):
    escola_a = escola_factory.create(codigo_eol="111111")
    escola_b = escola_factory.create(codigo_eol="222222")

    aluno_a1 = aluno_factory.create(serie="6A")
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_a1,
        status="CODAE_AUTORIZADO",
        ativo=True,
        rastro_escola=escola_a,
        tipo_solicitacao="COMUM",
    )

    aluno_b1 = aluno_factory.create(serie="7A")
    solicitacao_dieta_especial_factory.create(
        aluno=aluno_b1,
        status="CODAE_AUTORIZADO",
        ativo=True,
        rastro_escola=escola_b,
        tipo_solicitacao="COMUM",
    )

    resp_sem_filtro = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/"
    )
    assert resp_sem_filtro.status_code == 200
    series_sem_filtro = sorted(r["serie"] for r in resp_sem_filtro.json()["solicitacoes"])
    assert "6A" in series_sem_filtro
    assert "7A" in series_sem_filtro

    resp_a = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?codigo_eol_escola=111111"
    )
    assert resp_a.status_code == 200
    series_a = sorted(r["serie"] for r in resp_a.json()["solicitacoes"])
    assert series_a == ["6A"]

    resp_b = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?codigo_eol_escola=222222"
    )
    assert resp_b.status_code == 200
    series_b = sorted(r["serie"] for r in resp_b.json()["solicitacoes"])
    assert series_b == ["7A"]
