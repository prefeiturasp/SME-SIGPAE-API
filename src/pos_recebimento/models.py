from django.conf import settings
from django.db import models

from src.dados_comuns.behaviors import CriadoPor, ModeloBase
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

    empresa = models.ForeignKey(
        Terceirizada,
        on_delete=models.PROTECT,
        verbose_name="Empresa",
        related_name="termos_recebimento_definitivo",
    )
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.PROTECT,
        verbose_name="Contrato",
        related_name="termos_recebimento_definitivo",
    )
    cronogramas = models.ManyToManyField(
        Cronograma,
        through="CronogramaTermoRecebimentoDefinitivo",
        verbose_name="Cronogramas",
        related_name="termos_recebimento_definitivo",
        blank=True,
    )
    fiscal_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Fiscal 1",
        related_name="termos_recebimento_definitivo_fiscal_1",
    )
    fiscal_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Fiscal 2",
        related_name="termos_recebimento_definitivo_fiscal_2",
    )
    fiscal_3 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Fiscal 3",
        related_name="termos_recebimento_definitivo_fiscal_3",
    )
    valor_contrato = models.DecimalField(
        "Valor do Contrato",
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    texto_termo = models.TextField("Texto do Termo")
    status = models.CharField(
        "Status",
        max_length=20,
        choices=STATUS_CHOICES,
        default=RASCUNHO,
    )
    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        verbose_name="Alterado por",
        related_name="termos_recebimento_definitivo_alterados",
    )

    def __str__(self):
        return (
            f"Termo de Recebimento Definitivo - "
            f"{self.empresa.nome_fantasia} - Contrato: {self.contrato.numero}"
        )

    class Meta:
        verbose_name = "Termo de Recebimento Definitivo"
        verbose_name_plural = "Termos de Recebimento Definitivo"


class CronogramaTermoRecebimentoDefinitivo(models.Model):
    """Cronograma vinculado a um Termo de Recebimento Definitivo.

    Cada cronograma do termo possui sua própria quantidade total recebida.
    """

    termo = models.ForeignKey(
        TermoRecebimentoDefinitivo,
        on_delete=models.CASCADE,
        verbose_name="Termo de Recebimento Definitivo",
        related_name="cronogramas_termo",
    )
    cronograma = models.ForeignKey(
        Cronograma,
        on_delete=models.PROTECT,
        verbose_name="Cronograma",
    )
    quantidade_total_recebida = models.DecimalField(
        "Quantidade Total Recebida",
        max_digits=15,
        decimal_places=2,
    )

    def __str__(self):
        return f"Cronograma {self.cronograma.numero} do Termo {self.termo.uuid}"

    class Meta:
        verbose_name = "Cronograma do Termo de Recebimento Definitivo"
        verbose_name_plural = "Cronogramas do Termo de Recebimento Definitivo"
        unique_together = [("termo", "cronograma")]
