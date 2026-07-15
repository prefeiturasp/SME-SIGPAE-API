from django.db import models

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
        "Código suprimento", blank=True, max_length=100
    )
    codigo_papa = models.CharField("Código papa", blank=True, max_length=10)
    nome_alimento = models.CharField(
        "Nome do alimento/produto", blank=True, max_length=100
    )

    objects = AlimentoManager()

    def __str__(self):
        return self.nome_alimento

    class Meta:
        verbose_name = "Alimento"
        verbose_name_plural = "Alimentos"


class TipoEmbalagem(ModeloBase):
    sigla = models.CharField("Código", unique=True, max_length=10)
    descricao = models.CharField("Nome", max_length=100)
    ativo = models.BooleanField("Ativo?", default=True)

    def __str__(self):
        return f"{self.sigla} - {self.descricao} - {self.ativo}"

    class Meta:
        verbose_name = "Tipo de Embalagem Fechada"
        verbose_name_plural = "Tipos de Embalagens Fechadas"


class Embalagem(ModeloBase):
    FECHADA = "FECHADA"
    FRACIONADA = "FRACIONADA"

    TIPO_EMBALAGEM_CHOICES = (
        (FECHADA, "Fechada"),
        (FRACIONADA, "Fracionada"),
    )

    descricao_embalagem = models.CharField("Descrição da Embalagem", max_length=300)
    capacidade_embalagem = models.FloatField("Capacidade da Embalagem")
    unidade_medida = models.CharField("Unidade de Medida", max_length=10)
    tipo_embalagem = models.CharField(
        choices=TIPO_EMBALAGEM_CHOICES, max_length=15, default=FECHADA
    )
    qtd_volume = models.PositiveSmallIntegerField(
        "Quantidade/Volume", blank=True, null=True
    )
    qtd_a_receber = models.PositiveSmallIntegerField(
        "Quantidade a receber faltante", default=0, blank=True, null=True
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
        verbose_name = "Embalagem"
        verbose_name_plural = "Embalagens"
        ordering = ["criado_em", "tipo_embalagem"]
