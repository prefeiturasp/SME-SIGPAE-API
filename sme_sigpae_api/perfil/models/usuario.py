import datetime
import logging

import environ
from django.contrib.auth import authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_prometheus.models import ExportModelOperationsMixin
from rest_framework.status import HTTP_200_OK
from simple_email_confirmation.models import SimpleEmailConfirmationUserMixin

from ...dados_comuns.behaviors import (
    ArquivoCargaBase,
    Ativavel,
    Nomeavel,
    TemChaveExterna,
)
from ...dados_comuns.constants import (
    ADMINISTRADOR_CODAE_DILOG_CONTABIL,
    ADMINISTRADOR_CODAE_DILOG_JURIDICO,
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_DICAE,
    ADMINISTRADOR_EMPRESA,
    ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    ADMINISTRADOR_GESTAO_PRODUTO,
    ADMINISTRADOR_MEDICAO,
    ADMINISTRADOR_REPRESENTANTE_CODAE,
    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_LOGISTICA,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
    DINUTRE_DIRETORIA,
    ORGAO_FISCALIZADOR,
    USUARIO_EMPRESA,
    USUARIO_GTIC_CODAE,
    USUARIO_RELATORIOS,
)
from ...dados_comuns.tasks import envia_email_unico_task
from ...dados_comuns.utils import url_configs
from ...eol_servico.utils import EOLServicoSGP
from ..models import Perfil, Vinculo
from ..utils import get_cargo_eol

log = logging.getLogger("sigpae.usuario")

env = environ.Env()
base_url = f'{env("REACT_APP_URL")}'
senha_provisoria = f'{env("SENHA_PROVISORIA")}'


# Thanks to https://github.com/jmfederico/django-use-email-as-username


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomAbstractUser(AbstractBaseUser, PermissionsMixin):
    """An abstract base class implementing a fully featured User model with admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """

    email = models.EmailField(_("email address"), blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."
        ),  # noqa
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = CustomUserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        abstract = True

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(
        self,
        subject,
        message,
        from_email=None,
        template=None,
        dados_template=None,
        html=None,
        **kwargs,
    ):
        """Send an email to this user."""
        envia_email_unico_task.delay(
            assunto=subject,
            corpo="",
            email=self.email,
            template=template,
            dados_template=dados_template,
            html=html,
        )


# TODO: Refatorar classe Usuário para comportar classes Pessoa, Usuário,
# Nutricionista
class Usuario(
    ExportModelOperationsMixin("usuario"),
    SimpleEmailConfirmationUserMixin,
    CustomAbstractUser,
    TemChaveExterna,
):
    """Classe de autenticacao do django, ela tem muitos perfis."""

    SME = 0
    PREFEITURA = 1

    TIPOS_EMAIL = (
        (SME, "@sme.prefeitura.sp.gov.br"),
        (PREFEITURA, "@prefeitura.sp.gov.br"),
    )
    nome = models.CharField(_("name"), max_length=150)
    email = models.EmailField(_("email address"), unique=True)
    tipo_email = models.PositiveSmallIntegerField(
        choices=TIPOS_EMAIL, null=True, blank=True
    )
    username = models.CharField(max_length=100, unique=True)

    registro_funcional = models.CharField(
        _("RF"),
        max_length=7,
        blank=True,
        null=True,
        unique=True,  # noqa DJ01
        validators=[MinLengthValidator(7)],
    )
    cargo = models.CharField(max_length=50, blank=True)

    # TODO: essew atributow deve pertencer somente a um model Pessoa
    cpf = models.CharField(
        _("CPF"),
        max_length=11,
        blank=True,
        null=True,
        unique=True,  # noqa DJ01
        validators=[MinLengthValidator(11)],
    )
    contatos = models.ManyToManyField("dados_comuns.Contato", blank=True)

    # TODO: esses atributos devem pertencer somente a um model Nutricionista
    super_admin_terceirizadas = models.BooleanField(
        "É Administrador por parte das Terceirizadas?", default=False
    )  # noqa
    crn_numero = models.CharField(
        "Nutricionista crn", max_length=160, blank=True, null=True
    )  # noqa DJ01

    aceitou_termos = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []  # type: ignore

    def atualizar_cargo(self):
        cargo = self.cargos.filter(ativo=True).last()
        self.cargo = cargo.nome
        self.save()

    def desativa_cargo(self):
        cargo = self.cargos.last()
        if cargo is not None:
            cargo.finalizar_cargo()

    @property
    def vinculos(self):
        return self.vinculos

    @property
    def vinculo_atual(self):
        if self.vinculos.filter(
            Q(data_inicial=None, data_final=None, ativo=False)
            | Q(  # noqa W504 esperando ativacao
                data_inicial__isnull=False, data_final=None, ativo=True
            )
        ).exists():
            return self.vinculos.get(
                Q(data_inicial=None, data_final=None, ativo=False)
                | Q(  # noqa W504 esperando ativacao
                    data_inicial__isnull=False, data_final=None, ativo=True
                )
            )
        return None

    @property
    def existe_vinculo_ativo(self):
        return self.vinculos.filter(
            Q(data_inicial__isnull=False, data_final=None, ativo=True)
        ).exists()

    @property
    def tipo_usuario(self):  # noqa C901
        tipo_usuario = "indefinido"
        if self.vinculo_atual:
            tipo_usuario = self.vinculo_atual.content_type.model
            if tipo_usuario == "codae":
                if self.vinculo_atual.perfil.nome in [
                    COORDENADOR_LOGISTICA,
                    COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ADMINISTRADOR_CODAE_DILOG_JURIDICO,
                    ADMINISTRADOR_CODAE_DILOG_CONTABIL,
                    ADMINISTRADOR_REPRESENTANTE_CODAE,
                ]:
                    tipo_usuario = "logistica_abastecimento"
                elif self.vinculo_atual.perfil.nome in [
                    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                    ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ]:
                    tipo_usuario = "gestao_alimentacao_terceirizada"
                elif self.vinculo_atual.perfil.nome in [
                    COORDENADOR_GESTAO_PRODUTO,
                    ADMINISTRADOR_GESTAO_PRODUTO,
                ]:
                    tipo_usuario = "gestao_produto"
                elif self.vinculo_atual.perfil.nome in [
                    COORDENADOR_SUPERVISAO_NUTRICAO,
                    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
                ]:
                    tipo_usuario = "supervisao_nutricao"
                elif self.vinculo_atual.perfil.nome in [
                    COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO
                ]:
                    tipo_usuario = "nutricao_manifestacao"
                elif self.vinculo_atual.perfil.nome in [ADMINISTRADOR_MEDICAO]:
                    tipo_usuario = "medicao"
                elif self.vinculo_atual.perfil.nome in [ADMINISTRADOR_CODAE_GABINETE]:
                    tipo_usuario = "codae_gabinete"
                elif self.vinculo_atual.perfil.nome in [
                    DILOG_CRONOGRAMA,
                    DILOG_QUALIDADE,
                    DILOG_DIRETORIA,
                    DINUTRE_DIRETORIA,
                    DILOG_ABASTECIMENTO,
                ]:
                    tipo_usuario = "pre_recebimento"
                elif self.vinculo_atual.perfil.nome in [ORGAO_FISCALIZADOR]:
                    tipo_usuario = "orgao_fiscalizador"
                elif self.vinculo_atual.perfil.nome in [USUARIO_RELATORIOS]:
                    tipo_usuario = "usuario_relatorios"
                elif self.vinculo_atual.perfil.nome in [USUARIO_GTIC_CODAE]:
                    tipo_usuario = "usuario_gtic"
                elif self.vinculo_atual.perfil.nome in [ADMINISTRADOR_DICAE]:
                    tipo_usuario = "administrador_dicae"
                else:
                    tipo_usuario = "dieta_especial"
        return tipo_usuario

    @property
    def eh_parceira(self):
        return (
            self.tipo_usuario == "escola" and self.vinculo_atual.instituicao.eh_parceira
        )

    @property
    def eh_empresa(self):
        return (
            self.vinculo_atual
            and self.vinculo_atual.content_type.app_label == "terceirizada"
            and self.vinculo_atual.perfil.nome
            in [ADMINISTRADOR_EMPRESA, USUARIO_EMPRESA]
        )

    @property
    def eh_distribuidor(self):
        return self.eh_empresa and self.vinculo_atual.instituicao.eh_distribuidor

    @property
    def eh_fornecedor(self):
        return self.eh_empresa and self.vinculo_atual.instituicao.eh_fornecedor

    @property
    def eh_terceirizada(self):
        return self.eh_empresa and self.vinculo_atual.instituicao.eh_terceirizada

    @property
    def pode_efetuar_cadastro(self):
        response = EOLServicoSGP.get_dados_usuario(self.registro_funcional)
        if response.status_code != HTTP_200_OK:
            return False
        nome_cargo = get_cargo_eol(response)
        diretor_de_escola = False
        if nome_cargo["cargo"] == "DIRETOR DE ESCOLA":
            diretor_de_escola = True
        vinculo_aguardando_ativacao = (
            self.vinculo_atual.status == Vinculo.STATUS_AGUARDANDO_ATIVACAO
        )
        return diretor_de_escola or vinculo_aguardando_ativacao

    @property
    def cpf_formatado(self):
        return (
            f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
            if self.cpf is not None
            else None
        )

    @property
    def cpf_formatado_e_censurado(self):
        return (
            f"{self.cpf[:3]}.***.***-{self.cpf[9:]}" if self.cpf is not None else None
        )

    @property
    def registro_funcional_censurado(self):
        return (
            self.registro_funcional[:2] + "****" + self.registro_funcional[-1]
            if self.registro_funcional
            else None
        )

    def enviar_email_confirmacao(self):
        self.add_email_if_not_exists(self.email)
        content = {"uuid": self.uuid, "confirmation_key": self.confirmation_key}
        titulo = "Confirmação de E-mail"
        template = "email_cadastro_funcionario.html"
        dados_template = {
            "titulo": titulo,
            "link_cadastro": url_configs("CONFIRMAR_EMAIL", content),
            "nome": self.nome,
        }
        html = render_to_string(template, dados_template)
        self.email_user(
            subject="Confirme seu e-mail - SIGPAE",
            message="",
            template=template,
            dados_template=dados_template,
            html=html,
        )

    def enviar_email_recuperacao_senha(self):
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(self)
        visao_perfil = self.vinculo_atual.perfil.visao
        content = {"uuid": self.uuid, "confirmation_key": token, "visao": visao_perfil}
        titulo = "Recuperação de senha"
        template = "recuperar_senha.html"
        dados_template = {
            "titulo": titulo,
            "link_recuperar_senha": url_configs("RECUPERAR_SENHA", content),
        }
        html = render_to_string(template, context=dados_template)
        self.email_user(
            subject="Email de recuperação de senha - SIGPAE",
            message="",
            template=template,
            dados_template=dados_template,
            html=html,
        )

    def enviar_email_administrador(self):
        self.add_email_if_not_exists(self.email)
        titulo = "[SIGPAE] Novo cadastro de empresa"
        template = "email_cadastro_terceirizada.html"
        dados_template = {
            "titulo": titulo,
            "link_cadastro": url_configs("LOGIN_TERCEIRIZADAS", {}),
            "nome": self.nome,
        }
        html = render_to_string(template, dados_template)
        self.email_user(
            subject="[SIGPAE] Novo cadastro de empresa",
            message="",
            template=template,
            dados_template=dados_template,
            html=html,
        )

    @transaction.atomic
    def atualiza_senha(self, senha, token):
        token_generator = PasswordResetTokenGenerator()
        if token_generator.check_token(self, token):
            self.set_password(senha)
            self.save()
            EOLServicoSGP.redefine_senha(self.username, senha)
            return True
        return False

    @transaction.atomic
    def atualiza_senha_sem_token(self, senha):
        EOLServicoSGP.redefine_senha(self.username, senha)
        self.set_password(senha)
        self.save()

    @transaction.atomic
    def atualiza_email(self, email):
        self.email = email
        self.save()
        EOLServicoSGP.redefine_email(self.username, email)

    def criar_vinculo_administrador(self, instituicao, nome_perfil):
        perfil = Perfil.objects.get(nome=nome_perfil)
        Vinculo.objects.create(
            instituicao=instituicao, perfil=perfil, usuario=self, ativo=False
        )

    @classmethod
    def cria_ou_atualiza_usuario_sigpae(
        cls, dados_usuario, eh_servidor, existe_core_sso=False
    ):
        if eh_servidor:
            usuario, criado = Usuario.objects.update_or_create(
                username=dados_usuario.get("login"),
                cpf=dados_usuario.get("cpf"),
                defaults={
                    "email": dados_usuario.get("email"),
                    "registro_funcional": dados_usuario.get("login"),
                    "cargo": dados_usuario.get("cargo", ""),
                    "nome": dados_usuario.get("nome"),
                    "last_login": datetime.datetime.now() if existe_core_sso else None,
                },
            )
            return usuario
        else:
            usuario, criado = Usuario.objects.update_or_create(
                username=dados_usuario["cpf"],
                cpf=dados_usuario.get("cpf"),
                defaults={
                    "email": dados_usuario.get("email"),
                    "nome": dados_usuario["nome"],
                },
            )
            return usuario

    def verificar_autenticidade(self, password):
        usuario = authenticate(username=self.username, password=password)
        return usuario is not None

    def envia_email_primeiro_acesso_usuario_empresa(self):
        titulo = "Credenciais de Primeiro Acesso"
        template = "email_primeiro_acesso_usuario_empresa.html"
        dados_template = {
            "titulo": titulo,
            "url": f"{base_url}/login",
            "nome": self.nome,
            "senha_provisoria": senha_provisoria + self.cpf[-4:],
        }
        html = render_to_string(template, dados_template)
        self.email_user(
            subject="[SIGPAE] Credenciais de Acesso ao SIGPAE",
            message="",
            template=template,
            dados_template=dados_template,
            html=html,
        )

    def envia_email_primeiro_acesso_usuario_servidor(self):
        titulo = "Credenciais de Primeiro Acesso"
        template = "email_primeiro_acesso_usuario_servidor.html"
        dados_template = {
            "titulo": titulo,
            "url": f"{base_url}/login",
            "nome": self.nome,
            "senha": f"{senha_provisoria}{self.registro_funcional[-4:]}",
        }
        html = render_to_string(template, dados_template)
        self.email_user(
            subject="[SIGPAE] Credenciais de Acesso ao SIGPAE",
            message="",
            template=template,
            dados_template=dados_template,
            html=html,
        )

    class Meta:
        ordering = ("-super_admin_terceirizadas",)


class Cargo(TemChaveExterna, Nomeavel, Ativavel):
    data_inicial = models.DateField("Data inicial", null=True, blank=True)
    data_final = models.DateField("Data final", null=True, blank=True)
    usuario = models.ForeignKey(
        Usuario, related_name="cargos", on_delete=models.CASCADE
    )

    def finalizar_cargo(self):
        self.ativo = False
        self.data_final = datetime.date.today()
        self.save()

    def ativar_cargo(self):
        self.ativo = True
        self.data_inicial = datetime.date.today()
        self.save()

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return f"{self.usuario} de {self.data_inicial} até {self.data_final}"


class PlanilhaDiretorCogestor(models.Model):  # noqa D204
    """
    Importa dados de planilha específica de Diretores e Cogestores.
    No momento apenas DRE Ipiranga.
    """

    arquivo = models.FileField(blank=True, null=True)  # noqa DJ01
    criado_em = models.DateTimeField("criado em", auto_now_add=True, auto_now=False)

    def __str__(self):
        return str(self.arquivo)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Planilha Diretor Cogestor"
        verbose_name_plural = "Planilhas Diretores Cogestores"


class ImportacaoPlanilhaUsuarioPerfilEscola(ArquivoCargaBase):
    """Importa dados de planilha de usuários com perfil Escola."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = "Arquivo para importação de usuário perfil Escola"
        verbose_name_plural = "Arquivos para importação de usuários perfil Escola"

    def __str__(self) -> str:
        return str(self.conteudo)


class ImportacaoPlanilhaUsuarioPerfilCodae(ArquivoCargaBase):
    """Importa dados de planilha de usuários com perfil Escola."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = "Arquivo para importação de usuário perfil Codae"
        verbose_name_plural = "Arquivos para importação de usuários perfil Codae"

    def __str__(self) -> str:
        return str(self.conteudo)


class ImportacaoPlanilhaUsuarioPerfilDre(ArquivoCargaBase):
    """Importa dados de planilha de usuários com perfil Dre."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = "Arquivo para importação de usuário perfil Dre"
        verbose_name_plural = "Arquivos para importação de usuários perfil Dre"

    def __str__(self) -> str:
        return str(self.conteudo)


class ImportacaoPlanilhaUsuarioServidorCoreSSO(ArquivoCargaBase):
    """Importa dados de planilha de usuários com perfil servidor."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = (
            "Arquivo para importação/atualização de usuários servidores no CoreSSO"
        )
        verbose_name_plural = (
            "Arquivos para importação/atualização de usuários servidores no CoreSSO"
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class ImportacaoPlanilhaUsuarioExternoCoreSSO(ArquivoCargaBase):
    """Importa dados de planilha de usuários com perfil externo."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = (
            "Arquivo para importação/atualização de usuários externos no CoreSSO"
        )
        verbose_name_plural = (
            "Arquivos para importação/atualização de usuários externos no CoreSSO"
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class ImportacaoPlanilhaUsuarioUEParceiraCoreSSO(ArquivoCargaBase):
    """Importa dados de planilha de usuários com perfil UE parceira."""

    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = (
            "Arquivo para importação/atualização de usuários UEs parceiras no CoreSSO"
        )
        verbose_name_plural = (
            "Arquivos para importação/atualização de usuários UEs parceiras no CoreSSO"
        )

    def __str__(self) -> str:
        return str(self.conteudo)
