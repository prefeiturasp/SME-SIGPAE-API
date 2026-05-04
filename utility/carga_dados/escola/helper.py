import json
from unicodedata import normalize

from django.conf import settings

from src.perfil.models import Vinculo


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def printa_pontinhos():
    pontos = "..." * 70
    print(f"{bcolors.OKBLUE}{pontos}{bcolors.ENDC}")


def normaliza_nome(nome):
    nome = nome.replace(" / ", "/")
    nome = normalize("NFKD", nome).encode("ASCII", "ignore").decode("ASCII")
    return nome


def maiuscula(palavra):
    return palavra.strip().upper()


def coloca_zero_a_esquerda(palavra, tam=6):
    palavra_str = str(palavra)
    tam_palavra = len(palavra_str)
    qtd_zeros = tam - tam_palavra
    zeros = "0" * qtd_zeros
    final = ""
    if tam_palavra < tam:
        final = zeros + palavra_str
    return final or palavra_str


def busca_sigla_lote(sigla):
    # Santo Amaro > Não tem escola associada a esse lote OBS: "SAM" eh nao existe
    # Pirituba > Não tem escola associada a esse lote OBS: "PIR" eh nao existe
    # Butanta > Não tem escola associada a esse lote OBS: "BTT" eh nao existe

    fixture_data = json.load(
        open("{0}/src/escola/fixtures/lotes.json".format(settings.ROOT_DIR))
    )

    def _get_id(data):
        try:
            return list(
                filter(
                    lambda item: item["fields"]["iniciais"] == data, fixture_data
                )  # noqa
            )[0]["id"]
        except (IndexError, TypeError) as ex:
            raise Exception(f"Siga do Lote Nao Encontrado, {ex}") from None

    if sigla.strip() == "MP":
        return _get_id("MP I")
    else:
        return _get_id(sigla.strip())


def cria_vinculo_de_perfil_usuario(perfil, usuario, instituicao):
    vinculo = Vinculo.objects.create(
        data_inicial=None,
        data_final=None,
        instituicao=instituicao,
        perfil=perfil,
        usuario=usuario,
        ativo=False,
    )
    return vinculo


def email_valido(email):
    """
    Verifica se email é válido.
    """
    if "@" in email:
        return True
    return False
