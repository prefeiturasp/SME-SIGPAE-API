from typing import Any, Callable

import pytest


@pytest.fixture
def payload_dias_letivos() -> Callable[..., dict[str, Any]]:
    """Retorna funcao que constroi payload valido com overrides opcionais."""

    def _payload(
        data_inicial: str = "22/06/2026",
        data_final: str = "26/06/2026",
        dias_semana: list[str] | None = None,
        periodos_escolares: list[str] | None = None,
        lotes: list[str] | None = None,
        tipos_unidades: list[str] | None = None,
        unidades_educacionais: list[str] | None = None,
    ) -> dict[str, Any]:
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
