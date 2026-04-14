from django.core.validators import MinLengthValidator
from django.db import models

from sme_sigpae_api.dados_comuns.behaviors import (
    CriadoEm,
    TemChaveExterna,
    TemData,
)
from sme_sigpae_api.escola.constants import CEI_OU_EMEI, INFANTIL_OU_FUNDAMENTAL
from sme_sigpae_api.escola.models import Escola


class LogDietasAtivasCanceladasAutomaticamente(CriadoEm):
    dieta = models.ForeignKey(
        "SolicitacaoDietaEspecial",
        on_delete=models.CASCADE,
        related_name="dietas_especiais",
    )
    codigo_eol_aluno = models.CharField(  # noqa DJ01
        "Código EOL aluno",
        max_length=7,
        validators=[MinLengthValidator(7)],
        null=True,
        blank=True,
    )
    nome_aluno = models.CharField(
        "Nome do Aluno", max_length=100, null=True, blank=True
    )
    codigo_eol_escola_origem = models.CharField(
        "Código EOL escola origem",
        max_length=6,
        validators=[MinLengthValidator(6)],
        null=True,
        blank=True,
    )
    nome_escola_origem = models.CharField(
        "Nome da Escola origem", max_length=160, null=True, blank=True
    )
    codigo_eol_escola_destino = models.CharField(
        "Código EOL escola destino",
        max_length=6,
        validators=[MinLengthValidator(6)],
        null=True,
        blank=True,
    )
    nome_escola_destino = models.CharField(
        "Nome da Escola destino", max_length=160, null=True, blank=True
    )

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "log dietas ativas canceladas automaticamente"
        verbose_name_plural = "log dietas ativas canceladas automaticamente"

    def __str__(self):
        return str(self.pk)

    @property
    def escola_existe(self):
        escola_existe_no_sigpae = Escola.objects.filter(
            codigo_eol=self.codigo_eol_escola_destino
        ).first()
        if escola_existe_no_sigpae:
            return True
        return False


class LogQuantidadeDietasAutorizadas(TemChaveExterna, TemData, CriadoEm):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas",
    )
    quantidade = models.PositiveIntegerField()
    classificacao = models.ForeignKey(
        "ClassificacaoDieta",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="logs_dietas_autorizadas",
    )
    cei_ou_emei = models.CharField(max_length=4, choices=CEI_OU_EMEI, default="N/A")
    infantil_ou_fundamental = models.CharField(
        max_length=11, choices=INFANTIL_OU_FUNDAMENTAL, default="N/A"
    )

    def __str__(self) -> str:
        return (
            f'{self.escola.nome} - {self.data.strftime("%d/%m/%Y")} - {self.classificacao.nome}'
            f'{(" - " + self.periodo_escolar.nome) if self.periodo_escolar else ""}'
            f" - {self.quantidade} dieta(s)"
        )

    class Meta:
        verbose_name = "Log da quantidade de dietas autorizadas por unidade escolar"
        verbose_name_plural = (
            "Logs da quantidade de dietas autorizadas por unidade escolar"
        )
        ordering = ("-data", "escola__nome")


class LogQuantidadeDietasAutorizadasCEI(TemChaveExterna, TemData, CriadoEm):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_cei",
    )
    quantidade = models.PositiveIntegerField()
    classificacao = models.ForeignKey(
        "ClassificacaoDieta",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_cei",
    )
    periodo_escolar = models.ForeignKey(
        "escola.PeriodoEscolar",
        related_name="logs_dietas_autorizadas_cei",
        on_delete=models.CASCADE,
    )
    faixa_etaria = models.ForeignKey(
        "escola.FaixaEtaria", null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        return (
            f'{self.escola.nome} - {self.data.strftime("%d/%m/%Y")} - {self.periodo_escolar.nome} - '
            f"{self.classificacao.nome} - {self.quantidade} dieta(s) -- {self.faixa_etaria}"
        )

    class Meta:
        verbose_name = "Log da quantidade de dietas autorizadas por unidade escolar CEI"
        verbose_name_plural = (
            "Logs da quantidade de dietas autorizadas por unidade escolar CEI"
        )
        ordering = ("-data", "escola__nome")


class LogQuantidadeDietasAutorizadasRecreioNasFerias(
    TemChaveExterna, TemData, CriadoEm
):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_recreio_ferias",
    )
    quantidade = models.PositiveIntegerField()
    classificacao = models.ForeignKey(
        "ClassificacaoDieta",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_recreio_ferias",
    )

    def __str__(self) -> str:
        return (
            f'{self.escola.nome} - {self.data.strftime("%d/%m/%Y")} - '
            f"{self.classificacao.nome} - {self.quantidade} dieta(s)"
        )

    class Meta:
        verbose_name = "Log da quantidade de dietas autorizadas por unidade escolar - Recreio nas Férias"
        verbose_name_plural = "Logs da quantidade de dietas autorizadas por unidade escolar - Recreio nas Férias"
        ordering = ("-data", "escola__nome")


class LogQuantidadeDietasAutorizadasRecreioNasFeriasCEI(
    TemChaveExterna, TemData, CriadoEm
):
    escola = models.ForeignKey(
        "escola.Escola",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_recreio_ferias_cei",
    )
    quantidade = models.PositiveIntegerField()
    classificacao = models.ForeignKey(
        "ClassificacaoDieta",
        on_delete=models.CASCADE,
        related_name="logs_dietas_autorizadas_recreio_ferias_cei",
    )
    faixa_etaria = models.ForeignKey(
        "escola.FaixaEtaria",
        null=True,
        on_delete=models.DO_NOTHING,
        related_name="logs_dietas_autorizadas_recreio_ferias_cei",
    )

    def __str__(self) -> str:
        return (
            f'{self.escola.nome} - {self.data.strftime("%d/%m/%Y")} - '
            f"{self.classificacao.nome} - {self.quantidade} dieta(s) -- {self.faixa_etaria}"
        )

    class Meta:
        verbose_name = "Log da quantidade de dietas autorizadas por unidade escolar CEI - Recreio nas Férias"
        verbose_name_plural = "Logs da quantidade de dietas autorizadas por unidade escolar CEI - Recreio nas Férias"
        ordering = ("-data", "escola__nome")
