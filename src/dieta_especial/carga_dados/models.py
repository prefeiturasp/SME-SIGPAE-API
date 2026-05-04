from django.db import models

from src.dados_comuns.behaviors import (
    ArquivoCargaBase,
)


class PlanilhaDietasAtivas(models.Model):
    """Importa dados de planilha de Dietas Ativas específicas.

    Requer uma planilha com o De Para entre Código Escola e Código EOL da Escola.
    """

    arquivo = models.FileField(
        blank=True, null=True, help_text="Arquivo com escolas e dietas"
    )  # noqa DJ01
    arquivo_unidades_da_rede = models.FileField(
        blank=True, null=True, help_text="Arquivo unidades_da_rede...xlsx"
    )  # noqa DJ01
    resultado = models.FileField(
        blank=True, null=True, help_text="Arquivo com o resultado"
    )  # noqa DJ01
    tempfile = models.CharField(
        max_length=100, null=True, blank=True, help_text="JSON temporario"
    )  # noqa DJ01
    criado_em = models.DateTimeField("criado em", auto_now_add=True, auto_now=False)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Planilha Dieta Ativa"
        verbose_name_plural = "Planilhas Dietas Ativas"

    def __str__(self):
        return str(self.arquivo)


class ArquivoCargaDietaEspecial(ArquivoCargaBase):
    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = "Arquivo para importação de solicitações de Dieta Especial"
        verbose_name_plural = (
            "Arquivos para importação de solicitações de Dieta Especial"
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class ArquivoCargaAlimentosSubstitutos(ArquivoCargaBase):
    class Meta:
        verbose_name = "Arquivo para importação de Alimentos e Alimentos substitutos"
        verbose_name_plural = (
            "Arquivos para importação de Alimentos e Alimentos substitutos"
        )

    def __str__(self) -> str:
        return str(self.conteudo)
