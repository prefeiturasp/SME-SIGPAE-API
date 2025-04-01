def test_unidade_educacional_serializer(unidade_educacional):
    assert unidade_educacional.data is not None
    assert "lote" in unidade_educacional.data
    assert "unidade_educacional" in unidade_educacional.data
    assert "tipo_unidade" in unidade_educacional.data
    assert "classificacao_dieta" in unidade_educacional.data


def test_classificacoes_serializer(classificacoes):
    assert classificacoes.data is not None
    assert "tipo" in classificacoes.data
    assert "total" in classificacoes.data
    assert "periodos" in classificacoes.data
