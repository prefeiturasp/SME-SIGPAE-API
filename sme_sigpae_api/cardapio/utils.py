import datetime


def converter_data(formato: str) -> str:
    """
    Converte uma data do formato YYYY-MM-DD para o formato DD/MM/YYYY.
    """
    try:
        data_obj = datetime.datetime.strptime(formato, "%Y-%m-%d")
        return data_obj.strftime("%d/%m/%Y")
    except ValueError:
        raise ValueError(f"Data inválida: {formato}. Esperado no formato YYYY-MM-DD.")
