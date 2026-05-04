from brazilnum.cpf import validate_cpf

from src.eol_servico.utils import EOLException, EOLServicoSGP


class EOLUsuarioCoreSSO:
    def cria_ou_atualiza_usuario_core_sso(  # noqa: C901
        self, dados_usuario, login, eh_servidor, existe_core_sso
    ):
        """Verifica se usuário já existe no CoreSSO e cria se não existir.

        :param dados_usuario: {
                "login": "123456",
                "perfil": "DIRETOR",
                "email": "teste@teste.com",
                "nome": "Jose Testando",
                "servidor_s_n": "S",

            }
        """
        from requests import ConnectTimeout, ReadTimeout

        from utility.carga_dados.perfil.importa_dados import (
            ProcessaPlanilhaUsuarioServidorCoreSSOException,
            logger,
        )

        try:
            if not existe_core_sso:
                # Valida o nome
                if not dados_usuario.nome:
                    raise ProcessaPlanilhaUsuarioServidorCoreSSOException(
                        f"Nome é necessário para criação do usuário ({login})."
                    )

                # Valida login no caso de não servidor
                if eh_servidor == "N" and not validate_cpf(login):
                    raise ProcessaPlanilhaUsuarioServidorCoreSSOException(
                        f"Login de não servidor ({login}) não é um CPF válido."
                    )
                EOLServicoSGP.cria_usuario_core_sso(
                    login=login,
                    nome=dados_usuario.nome,
                    email=dados_usuario.email if dados_usuario.email else "",
                    e_servidor=eh_servidor == "S",
                )
                logger.info(f"Criado usuário no CoreSSO {login}.")

            info_user_core = EOLServicoSGP.usuario_core_sso_or_none(login=login)
            if (
                info_user_core
                and dados_usuario.email
                and info_user_core["email"] != dados_usuario.email
            ):
                EOLServicoSGP.redefine_email(login, dados_usuario.email)
                logger.info(
                    f"Atualizado e-mail do usuário no CoreSSO {login}, {dados_usuario.email}."
                )

            if dados_usuario.perfil:
                EOLServicoSGP.atribuir_perfil_coresso(
                    login=login, perfil=dados_usuario.perfil
                )
                logger.info(
                    f"Visão {dados_usuario.perfil} vinculada ao usuário {login} no CoreSSO."
                )

        except EOLException as e:
            raise ProcessaPlanilhaUsuarioServidorCoreSSOException(
                f"Erro {str(e)} ao criar/atualizar usuário {login} no CoreSSO."
            )

        except ReadTimeout:
            raise ProcessaPlanilhaUsuarioServidorCoreSSOException(
                f"Erro de ReadTimeout ao tentar criar/atualizar usuário {login} no CoreSSO."
            )

        except ConnectTimeout:
            raise ProcessaPlanilhaUsuarioServidorCoreSSOException(
                f"Erro de ConnectTimeout ao tentar criar/atualizar usuário {login} no CoreSSO."
            )
