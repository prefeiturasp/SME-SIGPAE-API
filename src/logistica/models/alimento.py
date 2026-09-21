from django.db import models

from src.dados_comuns.constants import StringsVerboseNameModels

from ...dados_comuns.behaviors import ModeloBase
from .guia import Guia


class AlimentoManager(models.Manager):
    def create_alimento(
        self, StrCodSup, StrCodPapa, StrNomAli, StrEmbala, IntQtdVol, guia
    ):
        return self.create(
            codigo_suprimento=StrCodSup,
            codigo_papa=StrCodPapa,
            nome_alimento=StrNomAli,
            embalagem=StrEmbala,
            qtd_volume=IntQtdVol,
            guia=guia,
        )

    def get_or_create_alimento(
        self, StrCodSup, StrCodPapa, StrNomAli, StrEmbala, IntQtdVol, guia
    ):
        obj, created = Alimento.objects.get_or_create(
            nome_alimento=StrNomAli,
            guia=guia,
            defaults={
                "codigo_suprimento": StrCodSup,
                "codigo_papa": StrCodPapa,
                "embalagem": StrEmbala,
                "qtd_volume": IntQtdVol,
            },
        )

        return obj, created


class Alimento(ModeloBase):
    guia = models.ForeignKey(
        Guia, on_delete=models.CASCADE, blank=True, null=True, related_name="alimentos"
    )
    codigo_suprimento = models.CharField(
        StringsVerboseNameModels.CODIGO_SUPRIMENTO.value, blank=True, max_length=100
    )
    codigo_papa = models.CharField(
        StringsVerboseNameModels.CODIGO_PAPA.value, blank=True, max_length=10
    )
    nome_alimento = models.CharField(
        StringsVerboseNameModels.NOME_DO_ALIMENTO_PRODUTO.value,
        blank=True,
        max_length=100,
    )

    objects = AlimentoManager()

    def __str__(self):
        return self.nome_alimento

    class Meta:
        verbose_name = StringsVerboseNameModels.ALIMENTO.value
        verbose_name_plural = StringsVerboseNameModels.ALIMENTOS.value


class TipoEmbalagem(ModeloBase):
    sigla = models.CharField(
        StringsVerboseNameModels.CODIGO.value, unique=True, max_length=10
    )
    descricao = models.CharField(StringsVerboseNameModels.NOME.value, max_length=100)
    ativo = models.BooleanField(StringsVerboseNameModels.ATIVO.value, default=True)

    def __str__(self):
        return f"{self.sigla} - {self.descricao} - {self.ativo}"

    class Meta:
        verbose_name = StringsVerboseNameModels.TIPO_DE_EMBALAGEM_FECHADA.value
        verbose_name_plural = (
            StringsVerboseNameModels.TIPOS_DE_EMBALAGENS_FECHADAS.value
        )


class Embalagem(ModeloBase):
    FECHADA = "FECHADA"
    FRACIONADA = "FRACIONADA"

    TIPO_EMBALAGEM_CHOICES = (
        (FECHADA, "Fechada"),
        (FRACIONADA, "Fracionada"),
    )

    descricao_embalagem = models.CharField(
        StringsVerboseNameModels.DESCRICAO_DA_EMBALAGEM.value, max_length=300
    )
    capacidade_embalagem = models.FloatField(
        StringsVerboseNameModels.CAPACIDADE_DA_EMBALAGEM.value
    )
    unidade_medida = models.CharField(
        StringsVerboseNameModels.UNIDADE_DE_MEDIDA.value, max_length=10
    )
    tipo_embalagem = models.CharField(
        choices=TIPO_EMBALAGEM_CHOICES, max_length=15, default=FECHADA
    )
    qtd_volume = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.QUANTIDADE_VOLUME.value, blank=True, null=True
    )
    qtd_a_receber = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.QUANTIDADE_A_RECEBER_FALTANTE.value,
        default=0,
        blank=True,
        null=True,
    )
    alimento = models.ForeignKey(
        Alimento,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="embalagens",
    )

    def __str__(self):
        return f"{self.descricao_embalagem}  {self.capacidade_embalagem} {self.unidade_medida}"

    class Meta:
        verbose_name = StringsVerboseNameModels.EMBALAGEM.value
        verbose_name_plural = StringsVerboseNameModels.EMBALAGENS.value
        ordering = ["criado_em", "tipo_embalagem"]
