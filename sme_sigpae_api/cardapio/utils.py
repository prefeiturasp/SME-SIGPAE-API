import datetime

from sme_sigpae_api.escola.models import Escola


def converter_data(formato: str) -> str:
    """
    Converte uma data do formato YYYY-MM-DD para o formato DD/MM/YYYY.
    """
    try:
        data_obj = datetime.datetime.strptime(formato, "%Y-%m-%d")
        return data_obj.strftime("%d/%m/%Y")
    except ValueError:
        raise ValueError(f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD.")


def ordem_periodos(escola: Escola) -> dict[str, int]:
    """
    Retorna a ordem dos períodos de acordo com o tipo de escola.

    Args:
        escola (Escola): Objeto representando a escola

    Returns:
        dict[str, int]: Dicionário mapeando períodos (ex: "MANHA", "TARDE") para sua ordem correspondente.
    """
    periodos_por_escola = {
        "eh_emef": {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3, "NOITE": 4},
        "eh_ceu_gestao": {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3, "NOITE": 4},
        "eh_emei": {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3},
        "eh_cemei": {
            "CEI DIRET": {
                "INTEGRAL": 1,
                "PARCIAL": 2,
            },
            "EMEI": {
                "MANHA": 1,
                "TARDE": 2,
                "INTEGRAL": 3,
            },
        },
        "eh_cei": {"INTEGRAL": 1, "PARCIAL": 2, "MANHA": 3, "TARDE": 4},
        "eh_cieja": {
            "MANHA": 1,
            "INTERMEDIARIO": 2,
            "TARDE": 3,
            "VESPERINO": 4,
            "NOITE": 5,
        },
        "eh_emebs": {"MANHA": 1, "TARDE": 2, "INTEGRAL": 3, "NOITE": 4},
    }

    for attr, turnos in periodos_por_escola.items():
        if getattr(escola, attr, False):
            return turnos

    return {
        "MANHA": 1,
        "INTERMEDIARIO": 2,
        "TARDE": 3,
        "VESPERINO": 4,
        "INTEGRAL": 5,
        "NOITE": 6,
    }
