from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from src.dados_comuns.behaviors import CriadoPor, ModeloBase, TemLogs
from src.dados_comuns.constants import StringsVerboseNameModels
from src.dados_comuns.fluxo_status import FluxoTermoRecebimentoProvisorio
from src.escola.models import Escola
from src.pre_recebimento.cronograma_entrega.models import Cronograma
from src.terceirizada.models import Contrato, Terceirizada


class TermoRecebimentoProvisorio(
    ModeloBase, CriadoPor, TemLogs, FluxoTermoRecebimentoProvisorio
):
    """Termo de Recebimento Provisório do módulo Pós-Recebimento.

    Registra a formalização do recebimento provisório de produtos de uma
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
    TERMO_ASSINADO = "TERMO_ASSINADO"

    STATUS_CHOICES = (
        (RASCUNHO, "Rascunho"),
        (ENVIADO_FISCAIS, "Enviado Fiscais"),
        (TERMO_ASSINADO, "Termo Assinado"),
    )

    empresa = models.ForeignKey(
        Terceirizada,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.EMPRESA.value,
        related_name="termos_recebimento_provisorio",
    )
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.CONTRATO.value,
        related_name="termos_recebimento_provisorio",
    )
    cronogramas = models.ManyToManyField(
        Cronograma,
        through="CronogramaTermoRecebimentoProvisorio",
        verbose_name=StringsVerboseNameModels.CRONOGRAMAS.value,
        related_name="termos_recebimento_provisorio",
        blank=True,
    )
    fiscal_1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.FISCAL_1.value,
        related_name="termos_recebimento_provisorio_fiscal_1",
    )
    fiscal_2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.FISCAL_2.value,
        related_name="termos_recebimento_provisorio_fiscal_2",
    )
    fiscal_3 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.FISCAL_3.value,
        related_name="termos_recebimento_provisorio_fiscal_3",
    )
    valor_contrato = models.DecimalField(
        StringsVerboseNameModels.VALOR_DO_CONTRATO.value,
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    texto_termo = models.TextField(StringsVerboseNameModels.TEXTO_DO_TERMO.value)
    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        verbose_name=StringsVerboseNameModels.ALTERADO_POR.value,
        related_name="termos_recebimento_provisorio_alterados",
    )

    def __str__(self):
        return (
            f"Termo de Recebimento Provisório - "
            f"{self.empresa.nome_fantasia} - Contrato: {self.contrato.numero}"
        )

    @property
    def etapa_fiscais_concluida(self):
        """A etapa de assinatura dos Fiscais do Contrato está concluída?

        Concluída quando todos os fiscais distintos já registraram a
        assinatura ``FISCAL_CONTRATO``. O cadastro permite o mesmo usuário
        em mais de um dos três papéis e cada usuário assina uma única vez,
        então a assinatura do usuário repetido cobre todos os papéis dele.
        """
        fiscais = {self.fiscal_1_id, self.fiscal_2_id, self.fiscal_3_id}
        assinantes = set(self.assinaturas.values_list("usuario_id", flat=True))
        return fiscais <= assinantes

    def eh_fiscal(self, usuario):
        """O usuário é um dos três Fiscais do Contrato do termo?"""
        return usuario in (self.fiscal_1, self.fiscal_2, self.fiscal_3)

    def usuario_ja_assinou_fiscal(self, usuario):
        """O usuário já assinou o termo?"""
        return self.assinaturas.filter(usuario=usuario).exists()

    def pode_assinar(self, usuario):
        """O usuário pode assinar o termo como Fiscal do Contrato agora?

        True apenas para um dos três fiscais, enquanto o termo estiver
        aguardando a assinatura dos fiscais e o fiscal ainda não tiver
        assinado.
        """
        return (
            self.status == TermoRecebimentoProvisorio.ENVIADO_FISCAIS
            and self.eh_fiscal(usuario)
            and not self.usuario_ja_assinou_fiscal(usuario)
        )

    class Meta:
        verbose_name = "Termo de Recebimento Provisório"
        verbose_name_plural = "Termos de Recebimento Provisório"


class CronogramaTermoRecebimentoProvisorio(models.Model):
    """Cronograma vinculado a um Termo de Recebimento Provisório.

    Cada cronograma do termo possui sua própria quantidade total recebida.
    """

    termo = models.ForeignKey(
        TermoRecebimentoProvisorio,
        on_delete=models.CASCADE,
        verbose_name=StringsVerboseNameModels.TERMO_DE_RECEBIMENTO_PROVISORIO.value,
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
        verbose_name = "Cronograma do Termo de Recebimento Provisório"
        verbose_name_plural = "Cronogramas do Termo de Recebimento Provisório"
        unique_together = [("termo", "cronograma")]


class AssinaturaTermoRecebimentoProvisorio(ModeloBase):
    """Assinatura de um Fiscal do Contrato no Termo, uma por usuário."""

    termo = models.ForeignKey(
        TermoRecebimentoProvisorio,
        on_delete=models.CASCADE,
        verbose_name=StringsVerboseNameModels.TERMO_DE_RECEBIMENTO_PROVISORIO.value,
        related_name="assinaturas",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.USUARIO.value,
        related_name="assinaturas_termo_recebimento_provisorio",
    )

    def __str__(self):
        return f"Assinatura de {self.usuario.nome} no Termo {self.termo.uuid}"

    class Meta:
        verbose_name = "Assinatura do Termo de Recebimento Provisório"
        verbose_name_plural = "Assinaturas dos Termos de Recebimento Provisório"
        unique_together = [("termo", "usuario")]


class MemorandoOcorrencia(ModeloBase, CriadoPor):
    """Ocorrência registrada pela Unidade Educacional no Pós-Recebimento.

    Registra a categoria, o produto e o tipo de ocorrência informados pela
    escola. Os lotes envolvidos ficam em ``LoteMemorandoOcorrencia``. Nesta
    história são contempladas as categorias Não Perecíveis, Perecíveis -
    Resfriados e Congelados, FLV e Leve Leite, todas com os mesmos campos.
    """

    CATEGORIA_NAO_PERECIVEIS = "NAO_PERECIVEIS"
    CATEGORIA_PERECIVEIS_RESFRIADOS_CONGELADOS = "PERECIVEIS_RESFRIADOS_CONGELADOS"
    CATEGORIA_FLV = "FLV"
    CATEGORIA_LEVE_LEITE = "LEVE_LEITE"

    CATEGORIA_CHOICES = (
        (CATEGORIA_NAO_PERECIVEIS, "Não Perecíveis"),
        (
            CATEGORIA_PERECIVEIS_RESFRIADOS_CONGELADOS,
            "Perecíveis - Resfriados e Congelados",
        ),
        (CATEGORIA_FLV, "FLV"),
        (CATEGORIA_LEVE_LEITE, "Leve Leite"),
    )

    TIPO_RECLAMACAO_QUALIDADE = "RECLAMACAO_QUALIDADE"
    TIPO_RETIRADA_ALIMENTO_IMPROPRIO = "RETIRADA_ALIMENTO_IMPROPRIO"
    TIPO_DEVOLUCAO_ALIMENTO_PROPRIO = "DEVOLUCAO_ALIMENTO_PROPRIO"

    TIPO_OCORRENCIA_CHOICES = (
        (TIPO_RECLAMACAO_QUALIDADE, "Reclamação de Qualidade"),
        (
            TIPO_RETIRADA_ALIMENTO_IMPROPRIO,
            "Retirada de Alimento Impróprio para o Consumo",
        ),
        (
            TIPO_DEVOLUCAO_ALIMENTO_PROPRIO,
            "Devolução de Alimento Próprio para o Consumo",
        ),
    )

    escola = models.ForeignKey(
        Escola,
        on_delete=models.PROTECT,
        verbose_name=StringsVerboseNameModels.ESCOLA.value,
        related_name="memorandos_ocorrencia",
    )
    categoria = models.CharField(
        StringsVerboseNameModels.CATEGORIA.value,
        max_length=40,
        choices=CATEGORIA_CHOICES,
    )
    produto = models.CharField(
        StringsVerboseNameModels.PRODUTO.value,
        max_length=255,
    )
    tipo_ocorrencia = models.CharField(
        StringsVerboseNameModels.TIPO_DE_OCORRENCIA.value,
        max_length=40,
        choices=TIPO_OCORRENCIA_CHOICES,
    )

    def __str__(self):
        return f"Memorando de Ocorrência - {self.produto} - {self.escola.nome}"

    class Meta:
        verbose_name = StringsVerboseNameModels.MEMORANDO_DE_OCORRENCIA.value
        verbose_name_plural = "Memorandos de Ocorrência"


class LoteMemorandoOcorrencia(ModeloBase):
    """Lote vinculado a um Memorando de Ocorrência."""

    memorando = models.ForeignKey(
        MemorandoOcorrencia,
        on_delete=models.CASCADE,
        verbose_name=StringsVerboseNameModels.MEMORANDO_DE_OCORRENCIA.value,
        related_name="lotes",
    )
    lote = models.CharField(
        StringsVerboseNameModels.LOTE.value,
        max_length=100,
    )
    marca = models.CharField(
        StringsVerboseNameModels.MARCA.value,
        max_length=100,
    )
    data_fabricacao = models.DateField(
        StringsVerboseNameModels.DATA_DE_FABRICACAO.value,
    )
    data_validade = models.DateField(
        StringsVerboseNameModels.DATA_DE_VALIDADE.value,
    )
    quantidade_problema_devolucao = models.DecimalField(
        StringsVerboseNameModels.QUANTIDADE_COM_PROBLEMA_DEVOLUCAO.value,
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    ordem = models.PositiveIntegerField("Ordem", default=1)

    def __str__(self):
        return f"Lote {self.lote} do Memorando {self.memorando.uuid}"

    class Meta:
        verbose_name = "Lote do Memorando de Ocorrência"
        verbose_name_plural = "Lotes do Memorando de Ocorrência"
        ordering = ["ordem", "id"]
