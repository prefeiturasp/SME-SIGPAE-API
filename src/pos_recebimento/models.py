from django.conf import settings
from django.db import models

from src.dados_comuns.behaviors import CriadoPor, ModeloBase
from src.dados_comuns.constants import StringsVerboseNameModels
from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.terceirizada.models import Contrato, Terceirizada


class TermoRecebimentoDefinitivo(ModeloBase, CriadoPor):
    """Termo de Recebimento Definitivo do módulo Pós-Recebimento.

    Registra a formalização do recebimento definitivo de produtos de uma
    empresa/contrato, vinculando um ou mais cronogramas, os fiscais
    (perfil DILOG_QUALIDADE) responsáveis e o texto do termo.

    Regra de negócio: a empresa deve possuir ao menos uma ficha de
    recebimento com status "Assinado CODAE" (FichaDeRecebimentoWorkflow.ASSINADA).
    A regra é aplicada na listagem de empresas disponíveis e validada
    novamente na criação do termo via API. A criação via API persiste o
    termo sempre com status ENVIADO_FISCAIS (fluxo "Salvar e Enviar").
    """

    RASCUNHO = "RASCUNHO"
    ENVIADO_FISCAIS = "ENVIADO_FISCAIS"
    ENVIADO_DILOG = "ENVIADO_DILOG"
    ENVIADO_COORDENADOR = "ENVIADO_COORDENADOR"
    ENVIADO_FORNECEDOR = "ENVIADO_FORNECEDOR"
    ASSINADO_FORNECEDOR = "ASSINADO_FORNECEDOR"

    STATUS_CHOICES = (
        (RASCUNHO, "Rascunho"),
        (ENVIADO_FISCAIS, "Enviado Fiscais"),
        (ENVIADO_DILOG, "Enviado DILOG"),
        (ENVIADO_COORDENADOR, "Enviado Coordenador"),
        (ENVIADO_FORNECEDOR, "Enviado Fornecedor"),
        (ASSINADO_FORNECEDOR, "Assinado Fornecedor"),
    )

    # Status exibidos como "Recebido" para o fornecedor (todo o fluxo de
    # envio até a assinatura).
    STATUS_RECEBIDO_FORNECEDOR = [
        ENVIADO_FISCAIS,
        ENVIADO_DILOG,
        ENVIADO_COORDENADOR,
        ENVIADO_FORNECEDOR,
    ]

    empresa = models.ForeignKey(
        Terceirizada,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.EMPRESA.value,
        related_name="termos_recebimento_definitivo",
    )
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.CONTRATO.value,
        related_name="termos_recebimento_definitivo",
    )
    cronogramas = models.ManyToManyField(
        Cronograma,
        through="CronogramaTermoRecebimentoDefinitivo",
        verbose_name=StringsVerboseNameModels.CRONOGRAMAS.value,
        related_name="termos_recebimento_definitivo",
        blank=True,
    )
    fiscal_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.FISCAL_1.value,
        related_name="termos_recebimento_definitivo_fiscal_1",
    )
    fiscal_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.FISCAL_2.value,
        related_name="termos_recebimento_definitivo_fiscal_2",
    )
    fiscal_3 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.FISCAL_3.value,
        related_name="termos_recebimento_definitivo_fiscal_3",
    )
    valor_contrato = models.DecimalField(
        StringsVerboseNameModels.VALOR_DO_CONTRATO.value,
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    texto_termo = models.TextField(StringsVerboseNameModels.TEXTO_DO_TERMO.value)
    status = models.CharField(
        StringsVerboseNameModels.STATUS.value,
        max_length=20,
        choices=STATUS_CHOICES,
        default=RASCUNHO,
    )
    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        verbose_name=StringsVerboseNameModels.ALTERADO_POR.value,
        related_name="termos_recebimento_definitivo_alterados",
    )

    def __str__(self):
        return (
            f"Termo de Recebimento Definitivo - "
            f"{self.empresa.nome_fantasia} - Contrato: {self.contrato.numero}"
        )

    class Meta:
        verbose_name = StringsVerboseNameModels.TERMO_DE_RECEBIMENTO_DEFINITIVO.value
        verbose_name_plural = (
            StringsVerboseNameModels.TERMOS_DE_RECEBIMENTO_DEFINITIVO.value
        )


class CronogramaTermoRecebimentoDefinitivo(models.Model):
    """Cronograma vinculado a um Termo de Recebimento Definitivo.

    Cada cronograma do termo possui sua própria quantidade total recebida.
    """

    termo = models.ForeignKey(
        TermoRecebimentoDefinitivo,
        on_delete=models.CASCADE,
        verbose_name=StringsVerboseNameModels.TERMO_DE_RECEBIMENTO_DEFINITIVO.value,
        related_name="cronogramas_termo",
    )
    cronograma = models.ForeignKey(
        Cronograma,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.CRONOGRAMA.value,
    )
    quantidade_total_recebida = models.DecimalField(
        StringsVerboseNameModels.QUANTIDADE_TOTAL_RECEBIDA.value,
        max_digits=15,
        decimal_places=2,
    )

    def __str__(self):
        return f"Cronograma {self.cronograma.numero} do Termo {self.termo.uuid}"

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.CRONOGRAMA_DO_TERMO_DE_RECEBIMENTO_DEFINITIVO.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.CRONOGRAMAS_DO_TERMO_DE_RECEBIMENTO_DEFINITIVO.value
        )
        unique_together = [("termo", "cronograma")]
