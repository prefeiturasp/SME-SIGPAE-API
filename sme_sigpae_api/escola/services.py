import requests
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
            raise Exception(f"Erro: {str(response)}, Status: {response.status_code}")


class NovoSGPServicoLogadoException(Exception):
    pass


class NovoSGPServicoLogado:
    headers = {"Content-Type": "application/json"}

    def pegar_token_acesso(self, login=None, senha=None):
        data = {
            "login": login or DJANGO_NOVO_SGP_API_LOGIN,
            "senha": senha or DJANGO_NOVO_SGP_API_PASSWORD,
        }
        response = requests.post(
            f"{DJANGO_NOVO_SGP_API_URL}/v1/autenticacao",
            json=data,
            headers=self.headers,
            timeout=120,
        )
        return response

    def __init__(self, login=None, senha=None):
        """Retorna um objeto para requisições no novosgp com token de acesso."""
        response = self.pegar_token_acesso(login, senha)
        if response.status_code != status.HTTP_200_OK:
            raise NovoSGPServicoLogadoException("Não foi possível logar no sistema")
        self.access_token = f'Bearer {response.json()["token"]}'

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
        self.headers["Authorization"] = self.access_token
        response = requests.get(
            f"{DJANGO_NOVO_SGP_API_URL}/v1/estudante/{codigo_eol_aluno}/foto",
            headers=self.headers,
            timeout=120,
        )
        return response

    def atualizar_foto_aluno(self, codigo_eol_aluno, foto):
        headers = {"Authorization": self.access_token}
        files = {"File": (foto.name, foto.file, foto.content_type)}
        response = requests.post(
            f"{DJANGO_NOVO_SGP_API_URL}/v1/estudante/{codigo_eol_aluno}/foto",
            files=files,
            headers=headers,
            timeout=120,
        )
        return response

    def deletar_foto_aluno(self, codigo_eol_aluno):
        self.headers["Authorization"] = self.access_token
        response = requests.delete(
            f"{DJANGO_NOVO_SGP_API_URL}/v1/estudante/{codigo_eol_aluno}/foto",
            headers=self.headers,
            timeout=120,
        )
        return response
