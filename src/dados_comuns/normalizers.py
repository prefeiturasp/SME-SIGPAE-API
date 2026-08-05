
import unicodedata


def normalizar_nome_categoria(nome: str) -> str:
    nome_normalizado = unicodedata.normalize("NFKD", nome.strip())

    return "".join(
        caractere
        for caractere in nome_normalizado
        if not unicodedata.combining(caractere)
    ).casefold()