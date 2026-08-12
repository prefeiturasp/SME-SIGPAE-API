import requests
import sentry_sdk
from django.core.cache import cache
from django_redis import get_redis_connection
from rest_framework import status

from ..dados_comuns.constants import (
    DJANGO_NOVO_SGP_API_LOGIN,
    DJANGO_NOVO_SGP_API_PASSWORD,
    DJANGO_NOVO_SGP_API_TOKEN,
    DJANGO_NOVO_SGP_API_URL,
)


class NovoSGPServico:
    HEADER = {"x-sgp-api-key": f"{DJANGO_NOVO_SGP_API_TOKEN}"}
    TIMEOUT = 10

    @classmethod
    def dias_letivos(
        cls, codigo_eol: str, data_inicio: str, data_fim: str, tipo_turno: int = 1
    ):
        """Consulta os dias letivos para as escola na API do novo sgp.

        tipo_turno:
            1 Manhã
            2 Intermediário
            3 Tarde
            4 Vespertino
            5 Noite
            6 Integral
        """
        response = requests.get(
            f"{DJANGO_NOVO_SGP_API_URL}/v1/calendario/integracoes/ues/dias-letivos/",
            headers=cls.HEADER,
            timeout=cls.TIMEOUT,
            params={
                "UeCodigo": codigo_eol,
                "TipoTurno": tipo_turno,
                "DataInicio": data_inicio,
                "DataFim": data_fim,
            },
        )

        if response.status_code == status.HTTP_200_OK:
            resultado = response.json()
            return resultado
        else:
            raise Exception(
                f"Erro: {str(response.text)}, Status: {response.status_code}"
            )


class NovoSGPServicoLogadoException(Exception):
    pass


class NovoSGPServicoLogado:
    TOKEN_CACHE_KEY = "novo_sgp:access_token"  # nosec B105
    TOKEN_LOCK_KEY = "novo_sgp:access_token:lock"  # nosec B105

    # Token do novo SGP tem validade de ~3h; renova a cada 2h20 para não expirar.
    TOKEN_CACHE_TIMEOUT = 2 * 60 * 60 + 20 * 60

    def __init__(self, login=None, senha=None):
        self.login = login or DJANGO_NOVO_SGP_API_LOGIN
        self.senha = senha or DJANGO_NOVO_SGP_API_PASSWORD

        self.access_token = self._obter_token()

    def pegar_token_acesso(self, login=None, senha=None):
        data = {
            "login": login or self.login,
            "senha": senha or self.senha,
        }

        try:
            return requests.post(
                f"{DJANGO_NOVO_SGP_API_URL}/v1/autenticacao",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=120,
            )
        except Exception:
            raise NovoSGPServicoLogadoException(
                "Não foi possível logar no sistema. "
                "Verifique seu RF e sua senha e tente novamente."
            )

    def _obter_token(self):
        token = cache.get(self.TOKEN_CACHE_KEY)

        if token:
            return token

        return self._renovar_token()

    def _renovar_token(self):
        redis = get_redis_connection("default")

        lock = redis.lock(
            self.TOKEN_LOCK_KEY,
            timeout=30,
            blocking_timeout=10,
        )

        with lock:
            # IMPORTANTE:
            # pode ser que outro worker tenha renovado o token
            # enquanto este worker estava esperando o lock.
            token = cache.get(self.TOKEN_CACHE_KEY)

            if token:
                return token

            response = self.pegar_token_acesso()

            if response.status_code != status.HTTP_200_OK:
                self._registrar_erro_login(response)

                raise NovoSGPServicoLogadoException("Não foi possível logar no sistema")

            token = f'Bearer {response.json()["token"]}'

            cache.set(
                self.TOKEN_CACHE_KEY,
                token,
                timeout=self.TOKEN_CACHE_TIMEOUT,
            )

            return token

    def _invalidar_token(self):
        cache.delete(self.TOKEN_CACHE_KEY)

    def _registrar_erro_login(self, response):
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("status_code", response.status_code)
            scope.set_extra("response_body", response.text)

            if response.request:
                scope.set_extra("url", response.request.url)

            scope.set_extra(
                "request_body",
                {
                    "login": self.login,
                },
            )

            sentry_sdk.capture_exception(
                NovoSGPServicoLogadoException("Não foi possível logar no sistema")
            )

    def _request(self, method, url, **kwargs):
        headers = kwargs.pop("headers", {}).copy()
        headers["Authorization"] = self.access_token

        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=120,
            **kwargs,
        )

        if response.status_code != status.HTTP_401_UNAUTHORIZED:
            return response

        # Token expirou ou foi invalidado.
        self._invalidar_token()

        self.access_token = self._renovar_token()

        headers["Authorization"] = self.access_token

        return requests.request(
            method,
            url,
            headers=headers,
            timeout=120,
            **kwargs,
        )

    def pegar_foto_aluno(self, codigo_eol_aluno):
        """
        Retorna foto do aluno da api do novosgp.

        Retorna foto do aluno caso ela exista com status 200.
        Sem retorno com status 204 caso a foto não exista.
        Exemplo de retorno:
        {
            "codigo": "08289b89-0479-4e70-b236-b27fef93f537",
            "nome": "PngItem_5759580.png",
            "download": {
                "item1": "iVBORw0KGgoAAAANSUhEUgAAAFgAAABYCAYAAABxlTA0AAAABGdBT...=",
                "item2": "image/png",
                "item3": "PngItem_5759580.png"
            }
        }
        """
        return self._request(
            "GET",
            f"{DJANGO_NOVO_SGP_API_URL}/v1/estudante/" f"{codigo_eol_aluno}/foto",
        )

    def atualizar_foto_aluno(self, codigo_eol_aluno, foto):
        files = {
            "File": (
                foto.name,
                foto.file,
                foto.content_type,
            )
        }

        return self._request(
            "POST",
            f"{DJANGO_NOVO_SGP_API_URL}/v1/estudante/" f"{codigo_eol_aluno}/foto",
            files=files,
        )

    def deletar_foto_aluno(self, codigo_eol_aluno):
        return self._request(
            "DELETE",
            f"{DJANGO_NOVO_SGP_API_URL}/v1/estudante/" f"{codigo_eol_aluno}/foto",
        )
