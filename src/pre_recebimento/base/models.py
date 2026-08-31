"""Modelos do submódulo base de pré-recebimento.

Dados de referência compartilhados pelos demais submódulos de
pré-recebimento, como as unidades de medida utilizadas em cronogramas,
fichas técnicas e documentos de recebimento.
"""

from django.db import models

from src.dados_comuns.behaviors import CriadoEm, Nomeavel, TemChaveExterna


class UnidadeMedida(TemChaveExterna, Nomeavel, CriadoEm):
    """Unidade de medida utilizada nas quantidades de pré-recebimento.

    Representa a unidade (ex.: ``kg``, ``ton``, ``un``) usada para medir
    quantidades em cronogramas de entrega, fichas técnicas e documentos de
    recebimento. O nome é armazenado sempre em letras maiúsculas e a
    abreviação sempre em letras minúsculas, normalização aplicada no
    ``save``.
    """
    abreviacao = models.CharField("Abreviação", max_length=25)

    def __str__(self):
        """Retorna o nome da unidade de medida."""
        return self.nome

    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"
        unique_together = ("nome",)

    def save(self, *args, **kwargs):
        """Normaliza e persiste a unidade de medida.

        O nome é convertido para letras maiúsculas e a abreviação para
        letras minúsculas antes de salvar.
        """
        self.nome = self.nome.upper()
        self.abreviacao = self.abreviacao.lower()
        super().save(*args, **kwargs)
