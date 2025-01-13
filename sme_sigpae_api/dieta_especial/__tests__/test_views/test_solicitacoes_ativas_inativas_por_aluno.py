import pytest

pytestmark = pytest.mark.django_db


def test_solicitacoes_ativas_inativas_por_aluno_viewset(
    client_autenticado_vinculo_codae_dieta,
    solicitacao_dieta_especial_factory,
    aluno_factory,
):
    aluno = aluno_factory.create(codigo_eol="1234567")
    solicitacao_dieta_especial_factory.create(
        aluno=aluno, status="CANCELADO_ALUNO_NAO_PERTENCE_REDE", ativo=False
    )
    solicitacao_dieta_especial_factory.create(
        aluno=aluno, status="CODAE_AUTORIZADO", ativo=True
    )

    response = client_autenticado_vinculo_codae_dieta.get(
        "/solicitacoes-dieta-especial-ativas-inativas/?codigo_eol=1234567&nome_aluno=&page=1"
    )
    assert response.json()["results"]["total_ativas"] == 1
    assert response.json()["results"]["total_inativas"] == 1
