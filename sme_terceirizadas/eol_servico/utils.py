import json
from datetime import date

import environ
import requests
from rest_framework import status

from ..dados_comuns.constants import (
    DJANGO_EOL_API_TOKEN,
    DJANGO_EOL_API_URL,
    DJANGO_EOL_PAPA_API_SENHA_CANCELAMENTO,
    DJANGO_EOL_PAPA_API_SENHA_ENVIO,
    DJANGO_EOL_PAPA_API_URL,
    DJANGO_EOL_PAPA_API_USUARIO,
    DJANGO_EOL_SGP_API_TOKEN,
    DJANGO_EOL_SGP_API_URL
)
from ..perfil.services.autenticacao_service import AutenticacaoService

env = environ.Env()


class EOLException(Exception):
    pass


class EOLService(object):
    DEFAULT_HEADERS = {'Authorization': f'Token {DJANGO_EOL_API_TOKEN}'}
    DEFAULT_TIMEOUT = 20

    @classmethod
    def get_informacoes_usuario(cls, registro_funcional):
        """Retorna detalhes de vínculo de um RF.

        mostra todos os vínculos desse RF. EX: fulano é diretor em AAAA e ciclano é professor em BBBB.
            {
        "results": [
            {
                "nm_pessoa": "XXXXXXXX",
                "cd_cpf_pessoa": "000.000.000-00",
                "cargo": "ANALISTA DE SAUDE NIVEL I",
                "divisao": "NUCLEO DE SUPERVISAO DA ALIMENT ESCOLAR - CODAE-DINUTRE-NSAE",
                "coord": null
            }
            ]
            }
        """
        response = requests.get(f'{DJANGO_EOL_API_URL}/cargos/{registro_funcional}',
                                headers=cls.DEFAULT_HEADERS,
                                timeout=cls.DEFAULT_TIMEOUT)
        if response.status_code == status.HTTP_200_OK:
            results = response.json()['results']
            if len(results) >= 1:
                return results
            raise EOLException(f'API do EOL não retornou nada para o RF: {registro_funcional}')
        else:
            raise EOLException(f'API EOL com erro. Status: {response.status_code}')

    @classmethod
    def get_informacoes_aluno(cls, codigo_eol):
        """Retorna detalhes do aluno.

        A api do EOL retorna assim:
        {
            'cd_aluno': 0001234,
            'nm_aluno': 'XXXXXX',
            'nm_social_aluno': None,
            'dt_nascimento_aluno': '1973-08-14T00:00:00',
            'cd_sexo_aluno': 'M',
            'nm_mae_aluno': 'XXXXX',
            'nm_pai_aluno': 'XXXX',
            "cd_escola": "017981",
            "dc_turma_escola": "4C",
            "dc_tipo_turno": "Manhã               "
        }
        """
        response = requests.get(f'{DJANGO_EOL_API_URL}/alunos/{codigo_eol}',
                                headers=cls.DEFAULT_HEADERS,
                                timeout=cls.DEFAULT_TIMEOUT)

        if response.status_code == status.HTTP_200_OK:
            results = response.json()['results']
            if len(results) > 0:
                return results[0]
            raise EOLException(f'Resultados para o código: {codigo_eol} vazios')
        else:
            raise EOLException(f'API EOL com erro. Status: {response.status_code}')

    @classmethod
    def get_informacoes_escola_turma_aluno(cls, codigo_eol):
        """Retorna uma lista de alunos da escola.

        Exemplo de retorno:
        [
            {
                "cod_dre": "109300",
                "sg_dre": "DRE - MP",
                "dre": "DIRETORIA REGIONAL DE EDUCACAO SAO MIGUEL",
                "cd_turma_escola": 2115958,
                "dc_turma_escola": "1A",
                "dc_serie_ensino": "1º Ano",
                "dc_tipo_turno": "Manhã               ",
                "cd_aluno": 6116689,
                "dt_nascimento_aluno": "2013-06-18T00:00:00"
            },
            {...dados de outro aluno},
            {...dados de outro aluno},
            ...
        ]
        """
        response = requests.get(f'{DJANGO_EOL_API_URL}/escola_turma_aluno/{codigo_eol}',
                                headers=cls.DEFAULT_HEADERS,
                                timeout=cls.DEFAULT_TIMEOUT)

        if response.status_code == status.HTTP_200_OK:
            results = response.json()['results']
            if len(results) == 0:
                raise EOLException(f'Resultados para o código: {codigo_eol} vazios')
            return results
        else:
            raise EOLException(f'API EOL com erro. Status: {response.status_code}')


class EOLServicoSGP:
    HEADER = {
        'accept': 'application/json',
        'x-api-eol-key': f'{DJANGO_EOL_SGP_API_TOKEN}'
    }
    TIMEOUT = 30

    @classmethod
    def matricula_por_escola(cls, codigo_eol: str, data: str, tipo_turma: int = 1):
        """Consulta a quantidade de matriculados na API do sgp."""
        response = requests.get(f'{DJANGO_EOL_SGP_API_URL}/matriculas/escolas/dre/{codigo_eol}/quantidades/',
                                headers=cls.HEADER, timeout=cls.TIMEOUT, params={'data': data, 'tipoTurma': tipo_turma})
        if response.status_code == status.HTTP_200_OK:
            resultado = response.json()
            return resultado
        else:
            raise EOLException(f'API EOL do SGP está com erro. Erro: {str(response)}, Status: {response.status_code}')

    @classmethod
    def usuario_core_sso_or_none(cls, login):
        from utility.carga_dados.perfil.importa_dados import logger

        logger.info('Consultando informação de %s.', login)
        try:
            response = requests.get(f'{DJANGO_EOL_SGP_API_URL}/AutenticacaoSgp/{login}/dados',
                                    headers=cls.HEADER)
            if response.status_code == status.HTTP_200_OK:
                logger.info(f'Usuário {login} encontrado no CoreSSO.')
                return response.json()
            else:
                logger.info(f'Usuário {login} não encontrado no CoreSSO: {response}')
                return None
        except Exception as err:
            logger.info(f'Erro ao procurar usuário {login} no CoreSSO: {str(err)}')
            raise EOLException(str(err))

    @classmethod
    def atribuir_perfil_coresso(cls, login, perfil):
        from utility.carga_dados.perfil.importa_dados import logger
        """ Atribuição de Perfil:

        /api/perfis/servidores/{codigoRF}/perfil/{perfil}/atribuirPerfil - GET

        """
        logger.info(f'Atribuindo perfil {perfil} ao usuário {login}.')

        sys_grupo_ids = AutenticacaoService.get_perfis_do_sistema()
        try:
            grupo_id = next(el['id'] for el in sys_grupo_ids if el['nome'] == perfil)
            url = f'{DJANGO_EOL_SGP_API_URL}/perfis/servidores/{login}/perfil/{grupo_id}/atribuirPerfil'
            response = requests.get(url, headers=cls.HEADER)
            if response.status_code == status.HTTP_200_OK:
                return ''
            else:
                logger.info('Falha ao tentar fazer atribuição de perfil: %s', response)
                raise EOLException('Falha ao fazer atribuição de perfil.')
        except Exception as err:
            logger.info('Erro ao tentar fazer atribuição de perfil: %s', str(err))
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_criar_usuario_coresso(cls, headers, payload):
        return requests.request('POST', f'{DJANGO_EOL_SGP_API_URL}/v1/usuarios/coresso', headers=headers, data=payload)

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
            'accept': 'application/json',
            'x-api-eol-key': f'{DJANGO_EOL_SGP_API_TOKEN}',
            'Content-Type': 'application/json-patch+json'
        }

        logger.info('Criando usuário no CoreSSO.')

        try:
            payload = json.dumps({
                'nome': nome,
                'documento': login if not e_servidor else '',
                'codigoRf': login if e_servidor else '',
                'email': email
            })

            response = cls.chamada_externa_criar_usuario_coresso(headers, payload)
            if response.status_code == status.HTTP_200_OK:
                result = 'OK'
                return result
            else:
                logger.info('Erro ao tentar criar o usuário: %s', response.json())
                raise EOLException(f'Erro ao tentar criar o usuário {nome}.')
        except Exception as err:
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_altera_email_coresso(cls, data):
        return requests.post(f'{DJANGO_EOL_SGP_API_URL}/AutenticacaoSgp/AlterarEmail', data=data,
                             headers=cls.HEADER)

    @classmethod
    def redefine_email(cls, registro_funcional, email):
        from utility.carga_dados.perfil.importa_dados import logger
        logger.info('Alterando email.')
        try:
            data = {
                'Usuario': registro_funcional,
                'Email': email
            }
            response = cls.chamada_externa_altera_email_coresso(data)
            if response.status_code == status.HTTP_200_OK:
                result = 'OK'
                return result
            else:
                logger.info('Erro ao redefinir email: %s', response.json())
                raise EOLException('Erro ao redefinir email')
        except Exception as err:
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_altera_senha(cls, data):
        return requests.post(f'{DJANGO_EOL_SGP_API_URL}/AutenticacaoSgp/AlterarSenha', data=data,
                             headers=cls.HEADER)

    @classmethod
    def redefine_senha(cls, registro_funcional, senha):
        from utility.carga_dados.perfil.importa_dados import logger
        """Se a nova senha for uma das senhas padões, a API do SME INTEGRAÇÃO
        não deixa fazer a atualização.
        Para resetar para a senha padrão é preciso usar o endpoint ReiniciarSenha da API SME INTEGRAÇÃO"""
        logger.info('Alterando senha.')

        try:
            data = {
                'Usuario': registro_funcional,
                'Senha': senha
            }
            response = cls.chamada_externa_altera_senha(data)
            if response.status_code == status.HTTP_200_OK:
                result = 'OK'
                return result
            else:
                logger.info('Erro ao redefinir senha: %s', response.content.decode('utf-8'))
                raise EOLException(f"Erro ao redefinir senha: {response.content.decode('utf-8')}")
        except Exception as err:
            raise EOLException(str(err))

    @classmethod
    def chamada_externa_dados_usuario(cls, registro_funcional):
        return requests.get(f'{DJANGO_EOL_SGP_API_URL}/funcionarios/DadosSigpae/{registro_funcional}',
                            headers=cls.HEADER)

    @classmethod
    def get_dados_usuario(cls, registro_funcional):
        from utility.carga_dados.perfil.importa_dados import logger
        logger.info('Checa dados do usuário no CoreSSO.')
        response = cls.chamada_externa_dados_usuario(registro_funcional)
        return response


class EOLPapaService:
    TIMEOUT = 90

    @classmethod
    def confirmacao_de_cancelamento(cls, cnpj, numero_solicitacao, sequencia_envio):
        payload = {
            'CNPJ_PREST': cnpj,
            'NUM_SOL': numero_solicitacao,
            'SEQ_ENVIO': sequencia_envio,
            'USUARIO': DJANGO_EOL_PAPA_API_USUARIO,
            'SENHA': DJANGO_EOL_PAPA_API_SENHA_CANCELAMENTO,

        }

        response = requests.post(f'{DJANGO_EOL_PAPA_API_URL}/confirmarcancelamentosolicitacao/',
                                 timeout=cls.TIMEOUT, json=payload)
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            if result['RETORNO'] != 'TRUE':
                raise EOLException(
                    f'API EOL do PAPA não confirmou cancelamento. MSG: {str(result)}')
        else:
            raise EOLException(f'API EOL do PAPA está com erro. Erro: {str(response)}, Status: {response.status_code}')

    @classmethod
    def confirmacao_de_envio(cls, cnpj, numero_solicitacao, sequencia_envio):
        if sequencia_envio is None:
            sequencia_envio = 0
        payload = {
            'CNPJ_PREST': cnpj,
            'NUM_SOL': numero_solicitacao,
            'SEQ_ENVIO': sequencia_envio,
            'USUARIO': DJANGO_EOL_PAPA_API_USUARIO,
            'SENHA': DJANGO_EOL_PAPA_API_SENHA_ENVIO,

        }
        response = requests.post(f'{DJANGO_EOL_PAPA_API_URL}/confirmarenviosolicitacao/',
                                 timeout=cls.TIMEOUT, json=payload)
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            if result['RETORNO'] != 'TRUE':
                raise EOLException(
                    f'API EOL do PAPA não confirmou o envio. MSG: {str(result)}')
        else:
            raise EOLException(f'API EOL do PAPA está com erro. Erro: {str(response)}, Status: {response.status_code}')


def dt_nascimento_from_api(string_dt_nascimento):
    (ano, mes, dia) = string_dt_nascimento.split('T')[0].split('-')
    return date(int(ano), int(mes), int(dia))
