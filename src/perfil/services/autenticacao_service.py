import logging

import httpx

from src.dados_comuns.constants import (
    DJANGO_AUTENTICA_CORESSO_API_TOKEN,
    DJANGO_AUTENTICA_CORESSO_API_URL,
)
from src.dados_comuns.http_client import (
    AUTENTICA_CORESSO_CLIENT,
    executar_chamada,
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
            response = executar_chamada(
                AUTENTICA_CORESSO_CLIENT,
                "post",
                f"{DJANGO_AUTENTICA_CORESSO_API_URL}/autenticacao/",
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.DEFAULT_TIMEOUT,
                json=payload,
            )
            return response
        except httpx.TimeoutException:
            LOG.info("Erro de timeout ao tentar autenticar o usuário %s", login)
            raise httpx.TimeoutException(
                "Erro de timeout: o servidor demorou demais para responder."
            )
        except Exception as e:
            LOG.info("ERROR - %s", str(e))
            raise e

    @classmethod
    def get_perfis_do_sistema(
        cls,
    ):
        try:
            LOG.info("Buscando perfis do sistema no CoreSSO.")
            response = executar_chamada(
                AUTENTICA_CORESSO_CLIENT,
                "get",
                f"{DJANGO_AUTENTICA_CORESSO_API_URL}/perfis/",
                headers=cls.DEFAULT_HEADERS,
                timeout=cls.DEFAULT_TIMEOUT,
            )
            return response.json()

        except Exception as e:
            LOG.info("ERROR - %s", str(e))
            raise e
