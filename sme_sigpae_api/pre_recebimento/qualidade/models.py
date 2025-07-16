from django.core.validators import MinLengthValidator
from django.db import models

from ...dados_comuns.behaviors import ModeloBase


class Laboratorio(ModeloBase):
    nome = models.CharField("Nome", max_length=150, unique=True)
    cnpj = models.CharField(
        "CNPJ", validators=[MinLengthValidator(14)], max_length=14, blank=True
    )
    cep = models.CharField("CEP", max_length=8, blank=True)
    logradouro = models.CharField("Logradouro", max_length=150, blank=True)
    numero = models.CharField("Número", max_length=10, blank=True)
    complemento = models.CharField("Complemento", max_length=50, blank=True)
    bairro = models.CharField("Bairro", max_length=150, blank=True)
    cidade = models.CharField("Cidade", max_length=150, blank=True)
    estado = models.CharField("Estado", max_length=150, blank=True)
    credenciado = models.BooleanField("Está credenciado?", default=False)

    contatos = models.ManyToManyField("dados_comuns.Contato", blank=True)

    def __str__(self):
        return f"{self.nome}"

    class Meta:
        verbose_name = "Laboratório"
        verbose_name_plural = "Laboratórios"


class TipoEmbalagemQld(ModeloBase):
    nome = models.CharField("Nome", max_length=150, unique=True)
    abreviacao = models.CharField("Abreviação", max_length=15)

    def __str__(self):
        return f"{self.nome}"

    class Meta:
        verbose_name = "Tipo de Embalagem (Qualidade)"
        verbose_name_plural = "Tipos de Embalagens (Qualidade)"
