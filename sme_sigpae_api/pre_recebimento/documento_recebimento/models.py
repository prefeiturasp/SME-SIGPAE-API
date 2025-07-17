import datetime
import os

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

from sme_sigpae_api.dados_comuns.utils import convert_image_to_base64
from sme_sigpae_api.pre_recebimento.base.models import UnidadeMedida
from sme_sigpae_api.pre_recebimento.cronograma_entrega.models import Cronograma
from sme_sigpae_api.relatorios.utils import merge_pdf_com_string_template

from ...dados_comuns.behaviors import (
    Logs,
    ModeloBase,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)
from ...dados_comuns.fluxo_status import (
    FluxoDocumentoDeRecebimento,
)
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.validators import validate_file_size_10mb


class ArquivoDoTipoDeDocumento(TemChaveExterna):
    tipo_de_documento = models.ForeignKey(
        "TipoDeDocumentoDeRecebimento",
        on_delete=models.CASCADE,
        related_name="arquivos",
        blank=True,
    )
    arquivo = models.FileField(
        upload_to="documentos_de_recebimento",
        validators=[
            FileExtensionValidator(allowed_extensions=["PDF", "PNG", "JPG", "JPEG"]),
            validate_file_size_10mb,
        ],
    )
    nome = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return (
            f"{self.tipo_de_documento.tipo_documento} - {self.nome}"
            if self.tipo_de_documento
            else str(self.id)
        )

    def delete(self, *args, **kwargs):
        # Antes de excluir o objeto, exclui o arquivo associado
        if self.arquivo:
            if os.path.isfile(self.arquivo.path):
                os.remove(self.arquivo.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Arquivo do Tipo de Documento"
        verbose_name_plural = "Arquivos dos Tipos de Documentos"


class TipoDeDocumentoDeRecebimento(TemChaveExterna):
    TIPO_DOC_LAUDO = "LAUDO"
    TIPO_DOC_DECLARACAO_LEI_1512010 = "DECLARACAO_LEI_1512010"
    TIPO_DOC_CERTIFICADO_CONF_ORGANICA = "CERTIFICADO_CONF_ORGANICA"
    TIPO_DOC_RASTREABILIDADE = "RASTREABILIDADE"
    TIPO_DOC_DECLARACAO_MATERIA_ORGANICA = "DECLARACAO_MATERIA_ORGANICA"
    TIPO_DOC_OUTROS = "OUTROS"

    TIPO_DOC_CHOICES = (
        (TIPO_DOC_LAUDO, "Laudo"),
        (
            TIPO_DOC_DECLARACAO_LEI_1512010,
            "Declaração de atendimento a Lei Municipal: 15.120/10",
        ),
        (TIPO_DOC_CERTIFICADO_CONF_ORGANICA, "Certificado de conformidade orgânica"),
        (TIPO_DOC_RASTREABILIDADE, "Rastreabilidade"),
        (TIPO_DOC_DECLARACAO_MATERIA_ORGANICA, "Declaração de Matéria Láctea"),
        (TIPO_DOC_OUTROS, "Outros"),
    )

    documento_recebimento = models.ForeignKey(
        "DocumentoDeRecebimento",
        on_delete=models.CASCADE,
        blank=True,
        related_name="tipos_de_documentos",
    )
    tipo_documento = models.CharField(
        choices=TIPO_DOC_CHOICES, max_length=35, blank=True
    )
    descricao_documento = models.TextField("Descrição do Documento", blank=True)

    def __str__(self):
        if self.documento_recebimento:
            return f"{self.documento_recebimento.cronograma.numero} - {self.tipo_documento}"
        else:
            return str(self.id)

    class Meta:
        verbose_name = "Tipo de Documento de Recebimento"
        verbose_name_plural = "Tipos de Documentos de Recebimento"
        unique_together = ["documento_recebimento", "tipo_documento"]


class DocumentoDeRecebimento(
    ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoDocumentoDeRecebimento
):
    cronograma = models.ForeignKey(
        Cronograma,
        on_delete=models.PROTECT,
        related_name="documentos_de_recebimento",
    )
    numero_laudo = models.CharField("Número do Laudo", blank=True, max_length=50)
    laboratorio = models.ForeignKey(
        "Laboratorio",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        default=None,
        related_name="documentos_de_recebimento",
    )
    quantidade_laudo = models.FloatField(blank=True, null=True)
    saldo_laudo = models.FloatField(blank=True, null=True)
    numero_lote_laudo = models.CharField("Número do Laudo", blank=True, max_length=200)
    unidade_medida = models.ForeignKey(
        UnidadeMedida, on_delete=models.PROTECT, blank=True, null=True, default=None
    )
    data_final_lote = models.DateField("Data Final do Lote", blank=True, null=True)
    correcao_solicitada = models.TextField("Correção Solicitada", blank=True)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.DOCUMENTO_DE_RECEBIMENTO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    @property
    def arquivo_laudo_assinado(self):
        log_aprovacao = self.logs.filter(
            status_evento=LogSolicitacoesUsuario.DOCUMENTO_APROVADO
        ).first()

        if not log_aprovacao:
            raise ValidationError(
                "Não foi possível encontrar o log de Aprovação do Documento de Recebimento para gerar o Laudo assinado."
            )

        laudo = self.tipos_de_documentos.filter(
            tipo_documento=TipoDeDocumentoDeRecebimento.TIPO_DOC_LAUDO
        ).first()
        arquivo_laudo = laudo.arquivos.first()

        logo_sipae = convert_image_to_base64(
            "sme_sigpae_api/relatorios/static/images/logo-sigpae.png", "png"
        )

        string_template = render_to_string(
            "pre_recebimento/documentos_recebimento/rodape_assinatura_digital_laudo.html",
            {
                "logo_sigpae": logo_sipae,
                "usuario": log_aprovacao.usuario,
                "data_hora": log_aprovacao.criado_em,
            },
        )

        return merge_pdf_com_string_template(
            arquivo_pdf=arquivo_laudo.arquivo,
            string_template=string_template,
            somente_ultima_pagina=True,
        )

    def __str__(self):
        return (
            f"{self.cronograma.numero} - Laudo: {self.numero_laudo}"
            if self.cronograma
            else str(self.numero_laudo)
        )

    class Meta:
        verbose_name = "Documento de Recebimento"
        verbose_name_plural = "Documentos de Recebimento"


class DataDeFabricaoEPrazo(TemChaveExterna):
    PRAZO_30 = "30"
    PRAZO_60 = "60"
    PRAZO_90 = "90"
    PRAZO_120 = "120"
    PRAZO_180 = "180"
    PRAZO_OUTRO = "OUTRO"

    PRAZO_CHOICES = (
        (PRAZO_30, "30 dias"),
        (PRAZO_60, "60 dias"),
        (PRAZO_90, "90 dias"),
        (PRAZO_120, "120 dias"),
        (PRAZO_180, "180 dias"),
        (PRAZO_OUTRO, "Outro"),
    )

    documento_recebimento = models.ForeignKey(
        "DocumentoDeRecebimento",
        on_delete=models.CASCADE,
        blank=True,
        related_name="datas_fabricacao_e_prazos",
    )
    data_fabricacao = models.DateField("Data Fabricação", blank=True, null=True)
    data_validade = models.DateField("Data Validade", blank=True, null=True)
    data_maxima_recebimento = models.DateField(
        "Data Máxima de Recebimento", blank=True, null=True
    )
    prazo_maximo_recebimento = models.CharField(
        "Prazo Máximo para Recebimento", choices=PRAZO_CHOICES, max_length=5, blank=True
    )
    justificativa = models.TextField("Justificativa", blank=True)

    def __str__(self):
        return f'{self.documento_recebimento.cronograma.numero} - {self.data_fabricacao.strftime("%d/%m/%Y")}'

    class Meta:
        verbose_name = "Data de Fabricação e Prazo"
        verbose_name_plural = "Datas de Fabricação e Prazos"


@receiver(pre_save, sender=DataDeFabricaoEPrazo)
def data_maxima_recebimento_pre_save(instance, *_args, **_kwargs):
    obj = instance
    if (
        obj.data_fabricacao
        and obj.prazo_maximo_recebimento
        and obj.prazo_maximo_recebimento != obj.PRAZO_OUTRO
    ):
        nova_data = obj.data_fabricacao + datetime.timedelta(
            days=int(obj.prazo_maximo_recebimento)
        )
        obj.data_maxima_recebimento = nova_data
