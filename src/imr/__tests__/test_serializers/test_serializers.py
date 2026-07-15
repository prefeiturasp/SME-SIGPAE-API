import pytest

pytestmark = pytest.mark.django_db


def test_tipo_ocorrencia_serializer(tipo_ocorrencia_nutrisupervisor_com_parametrizacao):
    """
    Testa o TipoOcorrenciaSerializer para uma request GET.
    """

    from src.imr.api.serializers.serializers import TipoOcorrenciaSerializer

    serializer = TipoOcorrenciaSerializer(
        tipo_ocorrencia_nutrisupervisor_com_parametrizacao
    )

    assert serializer.data is not None

    assert serializer.data["uuid"] == str(
        tipo_ocorrencia_nutrisupervisor_com_parametrizacao.uuid
    )
    assert (
        serializer.data["titulo"]
        == tipo_ocorrencia_nutrisupervisor_com_parametrizacao.titulo
    )
    assert (
        serializer.data["descricao"]
        == tipo_ocorrencia_nutrisupervisor_com_parametrizacao.descricao
    )
    assert (
        serializer.data["posicao"]
        == tipo_ocorrencia_nutrisupervisor_com_parametrizacao.posicao
    )

    assert serializer.data["categoria"]["uuid"] == str(
        tipo_ocorrencia_nutrisupervisor_com_parametrizacao.categoria.uuid
    )
    assert (
        serializer.data["categoria"]["nome"]
        == tipo_ocorrencia_nutrisupervisor_com_parametrizacao.categoria.nome
    )
    assert (
        serializer.data["categoria"]["posicao"]
        == tipo_ocorrencia_nutrisupervisor_com_parametrizacao.categoria.posicao
    )

    parametrizacao = (
        tipo_ocorrencia_nutrisupervisor_com_parametrizacao.parametrizacoes.first()
    )
    assert serializer.data["parametrizacoes"][0]["uuid"] == str(parametrizacao.uuid)
    assert serializer.data["parametrizacoes"][0]["posicao"] == parametrizacao.posicao
    assert serializer.data["parametrizacoes"][0]["titulo"] == parametrizacao.titulo

    tipo_pergunta = parametrizacao.tipo_pergunta
    assert serializer.data["parametrizacoes"][0]["tipo_pergunta"]["uuid"] == str(
        tipo_pergunta.uuid
    )
    assert (
        serializer.data["parametrizacoes"][0]["tipo_pergunta"]["nome"]
        == tipo_pergunta.nome
    )

    penalidade = tipo_ocorrencia_nutrisupervisor_com_parametrizacao.penalidade
    assert serializer.data["penalidade"]["uuid"] == str(penalidade.uuid)
    assert serializer.data["penalidade"]["numero_clausula"] == str(
        penalidade.numero_clausula
    )
    assert serializer.data["penalidade"]["descricao"] == penalidade.descricao

    obrigacoes = [obrigacao.descricao for obrigacao in penalidade.obrigacoes.all()]
    assert serializer.data["penalidade"]["obrigacoes"] == obrigacoes
