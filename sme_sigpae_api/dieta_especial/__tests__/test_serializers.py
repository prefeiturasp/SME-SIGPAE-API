def test_unidade_educacional_serializer(unidade_educacional):
    assert unidade_educacional.data is not None
    assert "lote" in unidade_educacional.data
    assert "unidade_educacional" in unidade_educacional.data
    assert "tipo_unidade" in unidade_educacional.data
    assert "classificacao" in unidade_educacional.data
    assert "total" in unidade_educacional.data
    assert "data" in unidade_educacional.data
    assert "periodos" in unidade_educacional.data
