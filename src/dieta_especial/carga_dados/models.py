from django.db import models

from src.dados_comuns.behaviors import (
    ArquivoCargaBase,
)
from src.dados_comuns.constants import StringsVerboseNameModels


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
    criado_em = models.DateTimeField(
        StringsVerboseNameModels.CRIADO_EM.value, auto_now_add=True, auto_now=False
    )

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = StringsVerboseNameModels.PLANILHA_DIETA_ATIVA.value
        verbose_name_plural = StringsVerboseNameModels.PLANILHAS_DIETAS_ATIVAS.value

    def __str__(self):
        return str(self.arquivo)


class ArquivoCargaDietaEspecial(ArquivoCargaBase):
    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.ARQUIVO_PARA_IMPORTACAO_DE_SOLICITACOES_DE_DIETA_ESPECIAL.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.ARQUIVOS_PARA_IMPORTACAO_DE_SOLICITACOES_DE_DIETA_ESPECIAL.value
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class ArquivoCargaAlimentosSubstitutos(ArquivoCargaBase):
    class Meta:
        verbose_name = (
            StringsVerboseNameModels.ARQUIVO_PARA_IMPORTACAO_DE_ALIMENTOS_E_ALIMENTOS_SUBSTITUTOS.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.ARQUIVOS_PARA_IMPORTACAO_DE_ALIMENTOS_E_ALIMENTOS_SUBSTITUTOS.value
        )

    def __str__(self) -> str:
        return str(self.conteudo)
