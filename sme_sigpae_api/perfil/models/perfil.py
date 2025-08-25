import datetime

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import Length
from django.db.models.query import QuerySet
from django.db.utils import IntegrityError
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.dados_comuns.behaviors import (
    Ativavel,
    Descritivel,
    Nomeavel,
    TemChaveExterna,
)


class Perfil(
    ExportModelOperationsMixin("perfil"),
    Nomeavel,
    Descritivel,
    Ativavel,
    TemChaveExterna,
):
    """Perfil do usuário Ex: Cogestor, Nutricionista. Cada perfil tem uma série de permissoes."""

    # Visão Choices
    ESCOLA = "ESCOLA"
    DRE = "DRE"
    CODAE = "CODAE"
    EMPRESA = "EMPRESA"

    VISAO_CHOICES = (
        (ESCOLA, "Escola"),
        (DRE, "Diretoria Regional"),
        (CODAE, "CODAE"),
        (EMPRESA, "Empresa"),
    )

    super_usuario = models.BooleanField("Super usuario na instiuição?", default=False)
    visao = models.CharField(  # noqa
        "Visão",
        choices=VISAO_CHOICES,
        max_length=25,
        blank=True,
        null=True,
        default=None,
    )

    @classmethod
    def visoes_to_json(cls):
        result = []
        for visao in cls.VISAO_CHOICES:
            choice = {"id": visao[0], "nome": visao[1]}
            result.append(choice)
        return result

    @classmethod
    def by_nome(cls, nome):
        return Perfil.objects.get(nome__iexact=nome)

    @classmethod
    def cargos_diretor(cls):
        return [
            {"codigo": 3360, "cargo": "DIRETOR DE ESCOLA"},
            {"codigo": 3085, "cargo": "ASSISTENTE DE DIREÇÃO DE ESCOLA"},
            {"codigo": 43, "cargo": "COORDENADOR GERAL"},
            {"codigo": 515, "cargo": "GESTOR DE EQUIPAMENTO PÚBLICO II"},
            {"codigo": 3298, "cargo": "CIEJA COORDENADOR GERAL"},
            {"codigo": 3875, "cargo": "CIEJA ASSIST COORD GERAL"},
        ]

    @classmethod
    def cargos_adm_escola(cls):
        return [{"codigo": 3379, "cargo": "COORDENADOR PEDAGÓGICO"}]

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self):
        return self.nome


class VinculoQueryset(QuerySet):
    def filtrar_por_usernames_validos(self):
        """Definido que um usuário válido.

        - Não é e-mail
        - Tamanho >= 7 e Tamanho <= 11
        """
        queryset = self.annotate(username_len=Length("usuario__username"))
        queryset = queryset.exclude(usuario__username__icontains="@")
        queryset = queryset.exclude(username_len__gt=11)
        queryset = queryset.exclude(username_len__lt=7)

        return queryset


class Vinculo(ExportModelOperationsMixin("vinculo_perfil"), Ativavel, TemChaveExterna):
    """Para informar que tipo de funcao uma pessoa teve em um dado intervalo de tempo em uma instituição.

    Ex.: de jan a dez de 2018 (Intervalo) Ciclano (Usuário) foi Diretor (Perfil) na instituição ESCOLA (instituicao)
    """

    (STATUS_AGUARDANDO_ATIVACAO, STATUS_ATIVO, STATUS_FINALIZADO) = range(3)

    data_inicial = models.DateField("Data inicial", null=True, blank=True)
    data_final = models.DateField("Data final", null=True, blank=True)
    perfil = models.ForeignKey("Perfil", on_delete=models.PROTECT)
    usuario = models.ForeignKey(
        "Usuario", on_delete=models.PROTECT, related_name="vinculos"
    )

    limit = (
        models.Q(app_label="escola", model="escola")
        | models.Q(app_label="escola", model="diretoriaregional")  # noqa W504
        | models.Q(app_label="escola", model="codae")  # noqa W504
        | models.Q(app_label="terceirizada", model="terceirizada")  # noqa W504
    )

    # https://docs.djangoproject.com/en/2.2/ref/contrib/contenttypes/#generic-relations
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to=limit,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    instituicao = GenericForeignKey("content_type", "object_id")
    objects = VinculoQueryset.as_manager()

    @property
    def status(self):
        if (not self.data_inicial) and (not self.data_final) and self.ativo is False:
            status = self.STATUS_AGUARDANDO_ATIVACAO
        elif self.data_inicial and self.ativo and not self.data_final:
            status = self.STATUS_ATIVO
        elif self.data_inicial and self.data_final and self.ativo is False:
            status = self.STATUS_FINALIZADO
        else:
            raise IntegrityError("Status invalido")
        return status

    def finalizar_vinculo(self):
        self.ativo = False
        self.data_final = datetime.date.today()
        self.save()

    def ativar_vinculo(self):
        self.ativo = True
        self.data_inicial = datetime.date.today()
        self.save()

    @classmethod  # noqa
    def get_instituicao(cls, dados_usuario):
        from ...escola.models import Codae, DiretoriaRegional, Escola
        from ...terceirizada.models import Terceirizada

        if dados_usuario["visao"] == Perfil.ESCOLA:
            return Escola.objects.get(codigo_eol=dados_usuario["instituicao"])
        elif dados_usuario["visao"] == Perfil.DRE:
            return DiretoriaRegional.objects.get(
                codigo_eol=dados_usuario["instituicao"]
            )
        elif dados_usuario["visao"] == Perfil.EMPRESA:
            return Terceirizada.objects.get(cnpj=dados_usuario["instituicao"])
        elif dados_usuario["visao"] == Perfil.CODAE:
            return Codae.by_uuid(uuid=dados_usuario["subdivisao"])

    @classmethod
    def cria_vinculo(cls, usuario, dados_usuario):
        if usuario.existe_vinculo_ativo:
            vinculo = usuario.vinculo_atual
            vinculo.ativo = False
            vinculo.data_final = datetime.date.today()
            vinculo.save()
        Vinculo.objects.create(
            instituicao=cls.get_instituicao(dados_usuario),
            perfil=Perfil.by_nome(nome=dados_usuario["perfil"]),
            usuario=usuario,
            data_inicial=datetime.date.today(),
            ativo=True,
        )

    class Meta:
        verbose_name = "Vínculo"
        verbose_name_plural = "Vínculos"

    def __str__(self):
        return f"{self.usuario.username} - {self.usuario.nome} - de {self.data_inicial} até {self.data_final}"


class PerfisVinculados(models.Model):
    perfil_master = models.OneToOneField(
        Perfil, on_delete=models.PROTECT, primary_key=True
    )
    perfis_subordinados = models.ManyToManyField(
        Perfil,
        help_text="Perfis que serão subordinados ao perfil master especificado",
        related_name="perfis_subordinados",
    )

    class Meta:
        verbose_name = "Perfis Vinculados"
        verbose_name_plural = "Perfis Vinculados"

    def __str__(self):
        return self.perfil_master.nome
