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


def test_calculo_totais_solicitacoes_sem_filtros(aluno_factory):
    from sme_sigpae_api.escola.models import Aluno

    aluno = aluno_factory.create(codigo_eol="1234567")

    view = SolicitacoesAtivasInativasPorAlunoView()

    mock_ativas = MagicMock()
    mock_ativas.filter.return_value = mock_ativas
    mock_ativas.values.return_value = mock_ativas
    mock_ativas.distinct.return_value = mock_ativas
    mock_ativas.count.return_value = 1

    mock_inativas = MagicMock()
    mock_inativas.filter.return_value = mock_inativas
    mock_inativas.values.return_value = mock_inativas
    mock_inativas.distinct.return_value = mock_inativas
    mock_inativas.count.return_value = 3

    view._qs_ativas_view = MagicMock(return_value=mock_ativas)
    view._qs_inativas_view = MagicMock(return_value=mock_inativas)
    view.aplicar_filtros_escola_view = MagicMock(side_effect=lambda qs, **kwargs: qs)

    alunos_qs = Aluno.objects.filter(codigo_eol="1234567")

    total_ativas, total_inativas = view.calcular_totais(alunos_qs=alunos_qs)

    assert total_ativas == 1
    assert total_inativas == 3


def test_calculo_totais_solicitacoes_aluno_especifico(aluno_factory):
    from django.db.models import Q

    from sme_sigpae_api.escola.models import Aluno

    aluno_factory.create(codigo_eol="1234567", nome="João Silva")
    aluno_factory.create(codigo_eol=None, nome="Maria Santos")

    view = SolicitacoesAtivasInativasPorAlunoView()

    mock_ativas = MagicMock()
    mock_ativas_filtered = MagicMock()
    mock_ativas_filtered.values.return_value = mock_ativas_filtered
    mock_ativas_filtered.distinct.return_value = mock_ativas_filtered
    mock_ativas_filtered.count.return_value = 1

    mock_ativas.filter.return_value = mock_ativas_filtered

    mock_inativas = MagicMock()
    mock_inativas_filtered = MagicMock()
    mock_inativas_filtered.values.return_value = mock_inativas_filtered
    mock_inativas_filtered.distinct.return_value = mock_inativas_filtered
    mock_inativas_filtered.count.return_value = 2

    mock_inativas.filter.return_value = mock_inativas_filtered

    view._qs_ativas_view = MagicMock(return_value=mock_ativas)
    view._qs_inativas_view = MagicMock(return_value=mock_inativas)
    view.aplicar_filtros_escola_view = MagicMock(side_effect=lambda qs, **kwargs: qs)

    alunos_query = Aluno.objects.filter(
        Q(codigo_eol="1234567") | Q(codigo_eol__isnull=True)
    )

    total_ativas, total_inativas = view.calcular_totais(alunos_qs=alunos_query)

    assert total_ativas == 1
    assert total_inativas == 2

    for mock_query, nome_query in [
        (mock_ativas, "ativas"),
        (mock_inativas, "inativas"),
    ]:
        mock_query.filter.assert_called_once()

        objeto_q = mock_query.filter.call_args[0][0]

        assert isinstance(objeto_q, Q)
        assert objeto_q.connector == Q.OR

        condicoes = objeto_q.children

        chave_primeira_condicao, valor_primeira_condicao = condicoes[0]
        assert chave_primeira_condicao == "codigo_eol_aluno__in"

        segunda_condicao = condicoes[1]
        assert isinstance(segunda_condicao, Q)
        assert segunda_condicao.connector == Q.AND

        dict_segunda_condicao = dict(segunda_condicao.children)
        assert dict_segunda_condicao["codigo_eol_aluno__isnull"] == True


def test_filtro_por_serie_exata_7a(
    client_autenticado_vinculo_codae_dieta,
    aluno_factory,
    solicitacao_dieta_especial_factory,
):
    aluno_7a = aluno_factory.create(codigo_eol="1001", serie="7A")
    aluno_7b = aluno_factory.create(codigo_eol="1002", serie="7B")
    aluno_7c = aluno_factory.create(codigo_eol="1003", serie="7C")

    for aluno in [aluno_7a, aluno_7b, aluno_7c]:
        solicitacao_dieta_especial_factory.create(
            aluno=aluno, status="CODAE_AUTORIZADO", ativo=True
        )

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?serie=7A"
    )
    series = [r["serie"] for r in response.json()["solicitacoes"]]

    assert series == ["7A"]


def test_filtro_por_numero_7(
    client_autenticado_vinculo_codae_dieta,
    aluno_factory,
    solicitacao_dieta_especial_factory,
):
    aluno_7a = aluno_factory.create(codigo_eol="1001", serie="7A")
    aluno_7b = aluno_factory.create(codigo_eol="1002", serie="7B")
    aluno_8c = aluno_factory.create(codigo_eol="1003", serie="8C")

    for aluno in [aluno_7a, aluno_7b, aluno_8c]:
        solicitacao_dieta_especial_factory.create(
            aluno=aluno, status="CODAE_AUTORIZADO", ativo=True
        )

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?serie=7"
    )
    series = [r["serie"] for r in response.json()["solicitacoes"]]

    assert sorted(series) == ["7A", "7B"]


def test_filtro_por_letra_a(
    client_autenticado_vinculo_codae_dieta,
    aluno_factory,
    solicitacao_dieta_especial_factory,
):
    aluno_6a = aluno_factory.create(codigo_eol="1001", serie="6A")
    aluno_7a = aluno_factory.create(codigo_eol="1002", serie="7A")
    aluno_8a = aluno_factory.create(codigo_eol="1003", serie="8A")
    aluno_7b = aluno_factory.create(codigo_eol="1004", serie="7B")

    for aluno in [aluno_6a, aluno_7a, aluno_8a, aluno_7b]:
        solicitacao_dieta_especial_factory.create(
            aluno=aluno, status="CODAE_AUTORIZADO", ativo=True
        )

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?serie=A"
    )
    series = [r["serie"] for r in response.json()["solicitacoes"]]

    assert sorted(series) == ["6A", "7A", "8A"]


def test_filtro_por_multiplas_series(
    client_autenticado_vinculo_codae_dieta,
    aluno_factory,
    solicitacao_dieta_especial_factory,
):
    aluno_6a = aluno_factory.create(codigo_eol="1001", serie="6A")
    aluno_7b = aluno_factory.create(codigo_eol="1002", serie="7B")
    aluno_7c = aluno_factory.create(codigo_eol="1003", serie="7C")

    for aluno in [aluno_6a, aluno_7b, aluno_7c]:
        solicitacao_dieta_especial_factory.create(
            aluno=aluno, status="CODAE_AUTORIZADO", ativo=True
        )

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
    series_sem_filtro = sorted(
        r["serie"] for r in resp_sem_filtro.json()["solicitacoes"]
    )
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
