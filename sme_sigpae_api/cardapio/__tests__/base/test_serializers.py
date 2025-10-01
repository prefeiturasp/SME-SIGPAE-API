import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.base.api.serializers import (
    TipoUnidadeEscolarAgrupadoSerializer,
)

pytestmark = pytest.mark.django_db


def test_tipo_unidade_escolar_agrupado_serializer_estrutura_padrao(
    vinculo_tipo_alimentacao,
):
    vinculos = [vinculo_tipo_alimentacao]
    dados_agrupados = TipoUnidadeEscolarAgrupadoSerializer.agrupar_vinculos_por_tipo_ue(
        vinculos
    )

    serializer = TipoUnidadeEscolarAgrupadoSerializer(dados_agrupados, many=True)
    data = serializer.data

    response_data = {"results": data}

    assert "results" in response_data
    assert len(response_data["results"]) == 1

    resultado = response_data["results"][0]

    campos_tipo_ue = [
        "uuid",
        "iniciais",
        "ativo",
        "tem_somente_integral_e_parcial",
        "pertence_relatorio_solicitacoes_alimentacao",
        "periodos_escolares",
    ]

    for campo in campos_tipo_ue:
        assert campo in resultado

    assert isinstance(resultado["iniciais"], str)
    assert isinstance(resultado["ativo"], bool)
    assert isinstance(resultado["periodos_escolares"], list)

    periodos = resultado["periodos_escolares"]
    assert len(periodos) == 1, "Deve ter exatamente 1 período escolar"

    periodo = periodos[0]
    campos_periodo = ["uuid", "nome", "tipos_alimentacao"]

    for campo in campos_periodo:
        assert campo in periodo

    assert isinstance(periodo["nome"], str)
    assert isinstance(periodo["tipos_alimentacao"], list)

    tipos_alimentacao = periodo["tipos_alimentacao"]
    assert len(tipos_alimentacao) == 5

    for tipo in tipos_alimentacao:
        assert "uuid" in tipo
        assert "nome" in tipo

    assert resultado["iniciais"] in ["EMEF", "CIEJA"]
    assert periodo["nome"] == "MANHA"


def test_tipo_unidade_escolar_agrupado_serializer_metodo_agrupar():
    # Testa o método estático agrupar_vinculos_por_tipo_ue com múltiplos vínculos

    vinculo1 = baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=baker.make("escola.TipoUnidadeEscolar", iniciais="EMEF"),
        periodo_escolar=baker.make("escola.PeriodoEscolar", nome="MANHA"),
        ativo=True,
    )

    vinculo2 = baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=baker.make("escola.TipoUnidadeEscolar", iniciais="EMEI"),
        periodo_escolar=baker.make("escola.PeriodoEscolar", nome="TARDE"),
        ativo=True,
    )

    vinculos = [vinculo1, vinculo2]
    resultado = TipoUnidadeEscolarAgrupadoSerializer.agrupar_vinculos_por_tipo_ue(
        vinculos
    )

    assert len(resultado) == 2

    iniciais_ordenadas = [item["iniciais"] for item in resultado]
    assert iniciais_ordenadas == sorted(iniciais_ordenadas)

    for item in resultado:
        assert "vinculos" in item
        assert len(item["vinculos"]) == 1


def test_tipo_unidade_escolar_agrupado_serializer_casos_extremos():
    # Teste com lista vazia
    resultado_vazio = TipoUnidadeEscolarAgrupadoSerializer.agrupar_vinculos_por_tipo_ue(
        []
    )
    assert resultado_vazio == []

    # Teste com vínculo sem tipo de UE
    vinculo_sem_tipo = baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=None,
        ativo=True,
    )

    resultado_sem_tipo = (
        TipoUnidadeEscolarAgrupadoSerializer.agrupar_vinculos_por_tipo_ue(
            [vinculo_sem_tipo]
        )
    )
    assert resultado_sem_tipo == []
