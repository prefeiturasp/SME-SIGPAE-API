import pytest


@pytest.fixture
def payload_dias_letivos():
    """Retorna funcao que constroi payload valido com overrides opcionais."""

    def _payload(
        data_inicial="22/06/2026",
        data_final="26/06/2026",
        dias_semana=None,
        periodos_escolares=None,
        lotes=None,
        tipos_unidades=None,
        unidades_educacionais=None,
    ):
        return {
            "recorrencias": [
                {
                    "data_inicial": data_inicial,
                    "data_final": data_final,
                    "periodos_escolares": periodos_escolares or [],
                    "dias_semana": dias_semana or ["0", "1", "2", "3", "4"],
                }
            ],
            "lotes": lotes or [],
            "tipos_unidades": tipos_unidades or [],
            "unidades_educacionais": unidades_educacionais or [],
        }

    return _payload
