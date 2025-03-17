import datetime
import re
import logging
from requests.exceptions import Timeout

from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from sme_sigpae_api.dados_comuns.constants import ADMINISTRADOR_UE, DIRETOR_UE
from sme_sigpae_api.eol_servico.utils import EOLException, EOLServicoSGP
from sme_sigpae_api.escola.models import Escola
from sme_sigpae_api.escola.services import (
    NovoSGPServicoLogado,
    NovoSGPServicoLogadoException,
)
from sme_sigpae_api.perfil.models import Perfil, Vinculo
from sme_sigpae_api.perfil.services.autenticacao_service import AutenticacaoService
from utility.carga_dados.perfil.importa_dados import (
    ProcessaPlanilhaUsuarioServidorCoreSSO,
)
from utility.carga_dados.perfil.schemas import (
    ImportacaoPlanilhaUsuarioServidorCoreSSOSchema,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class LoginView(TokenObtainPairView):
    # Substitui o login feito por /api-token-auth/

    permission_classes = (permissions.AllowAny,)

    def checa_login_senha_coresso(self, login, senha):
        novo_sgp = NovoSGPServicoLogado(login, senha)
        response_login = novo_sgp.pegar_token_acesso(login, senha)
        if response_login.status_code != status.HTTP_200_OK or len(login) != 7:
            raise NovoSGPServicoLogadoException("Usuário não encontrado")

    def update_user(self, user_dict, senha):
        user = User.objects.get(username=user_dict["login"])
        if not user.is_active or not user.existe_vinculo_ativo:
            raise PermissionDenied(
                "Você está sem autorização de acesso à aplicação no momento. "
                "Entre em contato com o administrador do SIGPAE."
            )
        last_login = user.last_login
        user.name = user_dict["nome"]
        user.email = user_dict["email"]
        user.set_password(senha)
        user.save()
        return user, last_login

    def build_response_data(self, request, user_dict, senha, last_login, args, kwargs):
        request._full_data = {"username": user_dict["login"], "password": senha}
        resp = super().post(request, *args, **kwargs)
        user_dict["token"] = resp.data["access"]
        user_dict["refresh"] = resp.data["refresh"]
        data = {"last_login": last_login, **user_dict, **resp.data}
        return data

    def cria_usuario_no_django_e_no_coresso(self, dados_usuario, nome_perfil):
        if not dados_usuario["email"]:
            response_outros_dados_usuario = EOLServicoSGP.usuario_core_sso_or_none(
                login=dados_usuario["rf"]
            )
            if (
                not response_outros_dados_usuario
                or not response_outros_dados_usuario["email"]
            ):
                raise PermissionDenied(
                    "Usuário sem e-mail cadastrado. E-mail é obrigatório."
                )
            dados_usuario["email"] = response_outros_dados_usuario["email"]
        tupla_dados = (
            dados_usuario["cargos"][0]["codigoUnidade"],
            dados_usuario["nome"],
            dados_usuario["cargos"][0]["descricaoCargo"].strip(),
            dados_usuario["email"],
            dados_usuario["cpf"],
            dados_usuario["rf"],
            "escola",
            nome_perfil,
            "",
        )
        processador = ProcessaPlanilhaUsuarioServidorCoreSSO(None, None)
        dados_formatados = processador.monta_dicionario_de_dados(tupla_dados)
        usuario_schema = ImportacaoPlanilhaUsuarioServidorCoreSSOSchema(
            **dados_formatados
        )
        processador.cria_usuario_servidor(0, usuario_schema)

    def get_dados_usuario_json(self, login):
        response_dados_usuario = EOLServicoSGP.get_dados_usuario(login)
        dados_usuario = response_dados_usuario.json()
        if response_dados_usuario.status_code != status.HTTP_200_OK:
            raise EOLException("Usuário não encontrado")
        return dados_usuario

    def usuario_com_cargo_de_acesso_automatico(self, dados_usuario):
        return dados_usuario["cargos"][0]["codigoCargo"] in [
            cargo["codigo"]
            for cargo in Perfil.cargos_diretor() + Perfil.cargos_adm_escola()
        ]

    def usuario_com_cargo_diretor(self, dados_usuario):
        return dados_usuario["cargos"][0]["codigoCargo"] in [
            cargo["codigo"] for cargo in Perfil.cargos_diretor()
        ]

    def usuario_com_cargo_automatico_adm_escola(self, dados_usuario):
        return dados_usuario["cargos"][0]["codigoCargo"] in [
            cargo["codigo"] for cargo in Perfil.cargos_adm_escola()
        ]

    def checa_se_cria_usuario(self, dados_usuario):
        if not self.usuario_com_cargo_de_acesso_automatico(dados_usuario):
            raise NovoSGPServicoLogadoException(
                "Usuário não possui permissão de acesso ao SIGPAE"
            )
        if self.usuario_com_cargo_diretor(dados_usuario):
            self.cria_usuario_no_django_e_no_coresso(dados_usuario, DIRETOR_UE)
        elif self.usuario_com_cargo_automatico_adm_escola(dados_usuario):
            self.cria_usuario_no_django_e_no_coresso(dados_usuario, ADMINISTRADOR_UE)

    def eh_perfil_escola(self, vinculo_atual):
        return vinculo_atual.perfil.nome in [ADMINISTRADOR_UE, DIRETOR_UE]

    def cria_vinculo(self, user, hoje, dados_usuario, perfil):
        novo_vinculo = Vinculo(
            usuario=user,
            ativo=True,
            data_inicial=hoje,
            instituicao=Escola.objects.get(
                codigo_eol=dados_usuario["cargos"][0]["codigoUnidade"]
            ),
            perfil=perfil,
        )
        novo_vinculo.save()

    def checa_se_trocou_de_unidade(self, user, hoje, vinculo_atual, dados_usuario):
        unidade_atual = dados_usuario["cargos"][0]["codigoUnidade"]
        if (
            vinculo_atual.ativo
            and vinculo_atual.instituicao.codigo_eol != unidade_atual
        ):
            vinculo_atual.finalizar_vinculo()
            self.cria_vinculo(user, hoje, dados_usuario, vinculo_atual.perfil)

    def se_diretor(self, vinculo_atual, dados_usuario, user, hoje):
        if vinculo_atual.perfil.nome != DIRETOR_UE:
            return
        if self.usuario_com_cargo_diretor(dados_usuario):
            self.checa_se_trocou_de_unidade(user, hoje, vinculo_atual, dados_usuario)
            return
        vinculo_atual.finalizar_vinculo()
        if self.usuario_com_cargo_automatico_adm_escola(dados_usuario):
            perfil = Perfil.objects.get(nome=ADMINISTRADOR_UE)
            self.cria_vinculo(user, hoje, dados_usuario, perfil)

    def se_administrador(self, vinculo_atual, dados_usuario, user, hoje):
        if vinculo_atual.perfil.nome != ADMINISTRADOR_UE:
            return
        if self.usuario_com_cargo_automatico_adm_escola(dados_usuario):
            self.checa_se_trocou_de_unidade(user, hoje, vinculo_atual, dados_usuario)
            return
        elif self.usuario_com_cargo_diretor(dados_usuario):
            vinculo_atual.finalizar_vinculo()
            perfil = Perfil.objects.get(nome=DIRETOR_UE)
            self.cria_vinculo(user, hoje, dados_usuario, perfil)
        elif (
            dados_usuario["cargos"][0]["codigoUnidade"]
            != vinculo_atual.instituicao.codigo_eol
        ):
            vinculo_atual.finalizar_vinculo()

    def checa_vinculo_se_servidor(self, login):
        if len(login) != 7:
            return
        dados_usuario = self.get_dados_usuario_json(login)
        self.checa_se_mantem_acesso_e_ou_altera_dados(dados_usuario)

    def checa_se_mantem_acesso_e_ou_altera_dados(self, dados_usuario):
        hoje = datetime.date.today()
        user = User.objects.get(username=dados_usuario["rf"])
        if not user.existe_vinculo_ativo:
            if not self.usuario_com_cargo_de_acesso_automatico(dados_usuario):
                raise PermissionDenied(
                    "Usuário não possui permissão de acesso ao SIGPAE"
                )
            elif self.usuario_com_cargo_diretor(dados_usuario):
                perfil = Perfil.objects.get(nome=DIRETOR_UE)
                self.cria_vinculo(user, hoje, dados_usuario, perfil)
                return
            elif self.usuario_com_cargo_automatico_adm_escola(dados_usuario):
                perfil = Perfil.objects.get(nome=ADMINISTRADOR_UE)
                self.cria_vinculo(user, hoje, dados_usuario, perfil)
                return
        vinculo_atual = user.vinculo_atual
        if not self.eh_perfil_escola(vinculo_atual):
            return
        self.se_diretor(vinculo_atual, dados_usuario, user, hoje)
        self.se_administrador(vinculo_atual, dados_usuario, user, hoje)

    def validar_email(self, email):
        if not email:
            return False

        padrao = r"[^\@]+@\S+\.[^\@]+"
        return re.match(padrao, email) is not None

    def buscar_email_usuario_sigpae(self, login):
        email = None
        usuario_sigpae = User.objects.get(username=login)
        if usuario_sigpae:
            if self.validar_email(usuario_sigpae.email):
                email = usuario_sigpae.email

        return email

    def validar_email_usuario_coresso(self, email, login):
        if not self.validar_email(email):
            novo_email = self.buscar_email_usuario_sigpae(login)
            if novo_email:
                email = novo_email
                EOLServicoSGP.redefine_email(login, email)

        return email

    def post(self, request, *args, **kwargs):
        login = request.data.get("login", "")
        senha = request.data.get("password", "")
        try:
            response = AutenticacaoService.autentica(login, senha)
            user_dict = response.json()
            if "login" in user_dict.keys():
                user_dict["email"] = self.validar_email_usuario_coresso(
                    user_dict["email"], login
                )
                self.checa_vinculo_se_servidor(login)
                user, last_login = self.update_user(user_dict, senha)
                data = self.build_response_data(
                    request, user_dict, senha, last_login, args, kwargs
                )
                return Response(data)
            else:
                self.checa_login_senha_coresso(login, senha)
                dados_usuario = self.get_dados_usuario_json(login)
                dados_usuario["email"] = self.validar_email_usuario_coresso(
                    dados_usuario["email"], login
                )
                self.checa_se_cria_usuario(dados_usuario)
                user_dict = {"login": login, **dados_usuario}
                user, last_login = self.update_user(user_dict, senha)
                data = self.build_response_data(
                    request, user_dict, senha, last_login, args, kwargs
                )
                return Response(data)
        except User.DoesNotExist:
            logger.info("Usuário %s não encontrado.", login)
            return Response(
                {"detail": "Usuário não encontrado."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except (NovoSGPServicoLogadoException, PermissionDenied) as e:
            logger.info(f"{str(e)}, {login}")
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except EOLException as e:
            logger.info(f"{str(e)}, {login}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Timeout as e:
            logger.error(f"Timeout ao tentar autenticar usuário {login}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
