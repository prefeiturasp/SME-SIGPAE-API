import json
import logging
from datetime import date, datetime

import environ
import requests
from rest_framework import status

from ..dados_comuns.constants import (
    DJANGO_EOL_PAPA_API_SENHA_CANCELAMENTO,
    DJANGO_EOL_PAPA_API_SENHA_ENVIO,
    DJANGO_EOL_PAPA_API_URL,
    DJANGO_EOL_PAPA_API_USUARIO,
    DJANGO_EOL_SGP_API_TOKEN,
    DJANGO_EOL_SGP_API_URL,
)
from ..perfil.services.autenticacao_service import AutenticacaoService

env = environ.Env()
logger = logging.getLogger(__name__)


class EOLException(Exception):
    pass


class EOLServicoSGP:
    HEADER = {
        "accept": "application/json",
        "x-api-eol-key": f"{DJANGO_EOL_SGP_API_TOKEN}",
    }
    TIMEOUT = 30

    @classmethod
    def matricula_por_escola(cls, codigo_eol: str, data: str, tipo_turma: int = 1):
        """Consulta a quantidade de matriculados na API do sgp."""
        response = requests.get(
            f"{DJANGO_EOL_SGP_API_URL}/matriculas/escolas/dre/{codigo_eol}/quantidades/",
            headers=cls.HEADER,
            timeout=cls.TIMEOUT,
            params={"data": data, "tipoTurma": tipo_turma},
        )
        if response.status_code == status.HTTP_200_OK:
            resultado = response.json()
            return resultado
        else:
            raise EOLException(
                f"API EOL do SGP está com erro. Erro: {str(response)}, Status: {response.status_code}"
            )

    @classmethod
    def usuario_existe_core_sso(cls, login):
        from utility.carga_dados.perfil.importa_dados import logger

        logger.info("Consultando informação de %s.", login)
        try:
            response = requests.post(
                f"{DJANGO_EOL_SGP_API_URL}/AutenticacaoSgp/UsuarioExisteCoreSSO/",
                headers=cls.HEADER,
                data={"usuario": login},
                timeout=cls.TIMEOUT,
            )
            if response.status_code == status.HTTP_200_OK:
                logger.info(f"Usuário {login} existe no CoreSSO.")
                return True
            else:
                logger.info(f"Usuário {login} não existe no CoreSSO: {response}")
                return False
        except Exception as err:
            logger.info(f"Erro ao procurar usuário {login} no CoreSSO: {str(err)}")
            raise EOLException(str(err))

    @classmethod
    def usuario_core_sso_or_none(cls, login):
        from utility.carga_dados.perfil.importa_dados import logger

        logger.info("Consultando informação de %s.", login)
        try:
            response = requests.get(
                f"{DJANGO_EOL_SGP_API_URL}/AutenticacaoSgp/{login}/dados",
                headers=cls.HEADER,
                timeout=cls.TIMEOUT,
            )
            if response.status_code == status.HTTP_200_OK:
                logger.info(f"Usuário {login} encontrado no CoreSSO.")
                return response.json()
            else:
                logger.info(f"Usuário {login} não encontrado no CoreSSO: {response}")
                return None
        except Exception as err:
            logger.info(f"Erro ao procurar usuário {login} no CoreSSO: {str(err)}")
            raise EOLException(str(err))

    @classmethod
    def atribuir_perfil_coresso(cls, login, perfil):
        from utility.carga_dados.perfil.importa_dados import logger

        """ Atribuição de Perfil:

        /api/perfis/servidores/{codigoRF}/perfil/{perfil}/atribuirPerfil - GET

        """
        logger.info(f"Atribuindo perfil {perfil} ao usuário {login}.")

        sys_grupo_ids = AutenticacaoService.get_perfis_do_sistema()
        try:
            grupo_id = next(el["id"] for el in sys_grupo_ids if el["nome"] == perfil)
            url = f"{DJANGO_EOL_SGP_API_URL}/perfis/servidores/{login}/perfil/{grupo_id}/atribuirPerfil"
            response = requests.get(url, headers=cls.HEADER, timeout=cls.TIMEOUT)
            if response.status_code == status.HTTP_200_OK:
                return ""
            else:
                logger.info("Falha ao tentar fazer atribuição de perfil: %s", response)
                raise EOLException("Falha ao fazer atribuição de perfil.")
        except Exception as err:
            logger.info("Erro ao tentar fazer atribuição de perfil: %s", str(err))
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_criar_usuario_coresso(cls, headers, payload):
        return requests.request(
            "POST",
            f"{DJANGO_EOL_SGP_API_URL}/v1/usuarios/coresso",
            headers=headers,
            data=payload,
        )

    @classmethod
    def cria_usuario_core_sso(cls, login, nome, email, e_servidor=False):
        from utility.carga_dados.perfil.importa_dados import logger

        """ Cria um novo usuário no CoreSSO

        /api/v1/usuarios/coresso - POST

        Payload =
            {
              "nome": "Nome do Usuário",
              "documento": "CPF em caso de não funcionário, caso de funcionário, enviar vazio",
              "codigoRf": "Código RF do funcionário, caso não funcionario, enviar vazio",
              "email": "Email do usuário"
            }
        """

        headers = {
            "accept": "application/json",
            "x-api-eol-key": f"{DJANGO_EOL_SGP_API_TOKEN}",
            "Content-Type": "application/json-patch+json",
        }

        logger.info("Criando usuário no CoreSSO.")

        try:
            payload = json.dumps(
                {
                    "nome": nome,
                    "documento": login if not e_servidor else "",
                    "codigoRf": login if e_servidor else "",
                    "email": email,
                }
            )

            response = cls.chamada_externa_criar_usuario_coresso(headers, payload)
            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                logger.info("Erro ao tentar criar o usuário: %s", response.json())
                raise EOLException(f"Erro ao tentar criar o usuário {nome}.")
        except Exception as err:
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_altera_email_coresso(cls, data):
        return requests.post(
            f"{DJANGO_EOL_SGP_API_URL}/AutenticacaoSgp/AlterarEmail",
            data=data,
            headers=cls.HEADER,
            timeout=cls.TIMEOUT,
        )

    @classmethod
    def redefine_email(cls, registro_funcional, email):
        from utility.carga_dados.perfil.importa_dados import logger

        logger.info("Alterando email.")
        try:
            data = {"Usuario": registro_funcional, "Email": email}
            response = cls.chamada_externa_altera_email_coresso(data)
            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                logger.info("Erro ao redefinir email: %s", response.json())
                raise EOLException("Erro ao redefinir email")
        except Exception as err:
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_altera_senha(cls, data):
        return requests.post(
            f"{DJANGO_EOL_SGP_API_URL}/AutenticacaoSgp/AlterarSenha",
            data=data,
            headers=cls.HEADER,
            timeout=cls.TIMEOUT,
        )

    @classmethod
    def redefine_senha(cls, registro_funcional, senha):
        from utility.carga_dados.perfil.importa_dados import logger

        """Se a nova senha for uma das senhas padões, a API do SME INTEGRAÇÃO
        não deixa fazer a atualização.
        Para resetar para a senha padrão é preciso usar o endpoint ReiniciarSenha da API SME INTEGRAÇÃO"""
        logger.info("Alterando senha.")

        try:
            data = {"Usuario": registro_funcional, "Senha": senha}
            response = cls.chamada_externa_altera_senha(data)
            if response.status_code == status.HTTP_200_OK:
                result = "OK"
                return result
            else:
                logger.info(
                    "Erro ao redefinir senha: %s", response.content.decode("utf-8")
                )
                raise EOLException(
                    f"Erro ao redefinir senha: {response.content.decode('utf-8')}"
                )
        except Exception as err:
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_dados_usuario(cls, registro_funcional):
        return requests.get(
            f"{DJANGO_EOL_SGP_API_URL}/funcionarios/DadosSigpae/{registro_funcional}",
            headers=cls.HEADER,
            timeout=cls.TIMEOUT,
        )

    @classmethod
    def get_dados_usuario(cls, registro_funcional):
        from utility.carga_dados.perfil.importa_dados import logger

        logger.info("Checa dados do usuário no CoreSSO.")
        response = cls.chamada_externa_dados_usuario(registro_funcional)
        return response

    @classmethod
    def chamada_externa_alunos_por_escola_por_ano_letivo(
        cls, codigo_eol_ue, ano=datetime.today().year
    ):
        return requests.get(
            f"{DJANGO_EOL_SGP_API_URL}/alunos/ues/{codigo_eol_ue}/anosLetivos/{ano}",
            headers=cls.HEADER,
            timeout=cls.TIMEOUT,
        )

    @classmethod
    def get_alunos_por_escola_por_ano_letivo(
        cls, codigo_eol_ue, ano=datetime.today().year
    ):
        status_matricula_ativa = [1, 6, 10, 13]
        codigo_turma_regular = 1

        try:
            response = cls.chamada_externa_alunos_por_escola_por_ano_letivo(
                codigo_eol_ue, ano
            )
            if response.status_code == status.HTTP_200_OK:
                lista_alunos = response.json()
                lista_alunos_filtrada = [
                    aluno
                    for aluno in lista_alunos
                    if aluno["codigoSituacaoMatricula"] in status_matricula_ativa
                    and aluno["codigoTipoTurma"] == codigo_turma_regular
                ]
                unique_data = {
                    aluno["codigoAluno"]: aluno for aluno in lista_alunos_filtrada
                }.values()
                return list(unique_data)
            else:
                raise EOLException(
                    f"Erro ao consultar alunos para a escola {codigo_eol_ue}. Status: {response.status_code}"
                )
        except Exception as err:
            raise EOLException(str(err))

    @classmethod
    def get_alunos_ano_seguinte(self, codigo_eol):
        ano_seguinte = datetime.today().year + 1
        return EOLServicoSGP.get_alunos_por_escola_por_ano_letivo(
            codigo_eol, ano_seguinte
        )

    @classmethod
    def _tenta_ano_corrente(cls, codigo_eol):
        try:
            return EOLServicoSGP.get_alunos_por_escola_por_ano_letivo(codigo_eol)
        except EOLException as e:
            logger.warning(f"EOL ano corrente falhou para escola {codigo_eol}: {e}")
            return None

    @classmethod
    def _tenta_ano_seguinte(cls, codigo_eol):
        try:
            return cls.get_alunos_ano_seguinte(codigo_eol)
        except EOLException as e:
            logger.warning(f"EOL ano seguinte falhou para escola {codigo_eol}: {e}")
            return None

    @classmethod
    def get_lista_alunos_por_escola_ano_corrente_ou_seguinte(cls, codigo_eol):
        lista = cls._tenta_ano_corrente(codigo_eol)
        if lista is None or not lista:
            lista = cls._tenta_ano_seguinte(codigo_eol)

        return lista or []


class EOLPapaService:
    TIMEOUT = 120

    @classmethod
    def confirmacao_de_cancelamento(cls, cnpj, numero_solicitacao, sequencia_envio):
        payload = {
            "CNPJ_PREST": cnpj,
            "NUM_SOL": numero_solicitacao,
            "SEQ_ENVIO": sequencia_envio,
            "USUARIO": DJANGO_EOL_PAPA_API_USUARIO,
            "SENHA": DJANGO_EOL_PAPA_API_SENHA_CANCELAMENTO,
        }

        response = requests.post(
            f"{DJANGO_EOL_PAPA_API_URL}/confirmarcancelamentosolicitacao/",
            timeout=cls.TIMEOUT,
            json=payload,
        )
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            if result["RETORNO"] != "TRUE":
                raise EOLException(
                    f"API EOL do PAPA não confirmou cancelamento. MSG: {str(result)}"
                )
        else:
            raise EOLException(
                f"API EOL do PAPA está com erro. Erro: {str(response)}, Status: {response.status_code}"
            )

    @classmethod
    def confirmacao_de_envio(cls, cnpj, numero_solicitacao, sequencia_envio):
        if sequencia_envio is None:
            sequencia_envio = 0
        payload = {
            "CNPJ_PREST": cnpj,
            "NUM_SOL": numero_solicitacao,
            "SEQ_ENVIO": sequencia_envio,
            "USUARIO": DJANGO_EOL_PAPA_API_USUARIO,
            "SENHA": DJANGO_EOL_PAPA_API_SENHA_ENVIO,
        }
        response = requests.post(
            f"{DJANGO_EOL_PAPA_API_URL}/confirmarenviosolicitacao/",
            timeout=cls.TIMEOUT,
            json=payload,
        )
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            if result["RETORNO"] != "TRUE":
                raise EOLException(
                    f"API EOL do PAPA não confirmou o envio. MSG: {str(result)}"
                )
        else:
            raise EOLException(
                f"API EOL do PAPA está com erro. Erro: {str(response)}, Status: {response.status_code}"
            )


def dt_nascimento_from_api(string_dt_nascimento):
    (ano, mes, dia) = string_dt_nascimento.split("T")[0].split("-")
    return date(int(ano), int(mes), int(dia))
