import logging
import requests
from requests.exceptions import Timeout

from sme_sigpae_api.dados_comuns.constants import (
    DJANGO_AUTENTICA_CORESSO_API_TOKEN,
    DJANGO_AUTENTICA_CORESSO_API_URL,
)

LOG = logging.getLogger(__name__)


class AutenticacaoService:
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Token {DJANGO_AUTENTICA_CORESSO_API_TOKEN}",
    }
    DEFAULT_TIMEOUT = 10

    @classmethod
    def autentica(cls, login, senha):
        payload = {"login": login, "senha": senha}
        try:
            LOG.info("Autenticando no sme-autentica. Login: %s", login)
            response = requests.post(
                f"{DJANGO_AUTENTICA_CORESSO_API_URL}/autenticacao/",
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.DEFAULT_TIMEOUT,
                json=payload,
            )
            return response
        except Timeout as e:
            LOG.info("Erro de timeout ao tentar autenticar o usuário %s", login)
            raise Timeout("Erro de timeout: o servidor demorou demais para responder.")
        except Exception as e:
            LOG.info("ERROR - %s", str(e))
            raise e

    @classmethod
    def get_perfis_do_sistema(
        cls,
    ):
        try:
            LOG.info("Buscando perfis do sistema no CoreSSO.")
            response = requests.get(
                f"{DJANGO_AUTENTICA_CORESSO_API_URL}/perfis/",
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.DEFAULT_TIMEOUT,
            )
            return response.json()

        except Exception as e:
            LOG.info("ERROR - %s", str(e))
            raise e
