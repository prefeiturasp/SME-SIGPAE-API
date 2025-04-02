import datetime
import os

from django.core.validators import FileExtensionValidator, MinLengthValidator
from django.db import models
from django.db.models import OuterRef
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

from django.db.models import F
from django.db.models.functions import Cast

from sme_sigpae_api.dados_comuns.utils import convert_image_to_base64
from sme_sigpae_api.relatorios.utils import merge_pdf_com_string_template

from ...dados_comuns.behaviors import (
    CriadoEm,
    CriadoPor,
    Logs,
    ModeloBase,
    Nomeavel,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)
from ...dados_comuns.fluxo_status import (
    CronogramaAlteracaoWorkflow,
    FluxoAlteracaoCronograma,
    FluxoCronograma,
    FluxoDocumentoDeRecebimento,
    FluxoFichaTecnicaDoProduto,
    FluxoLayoutDeEmbalagem,
)
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.validators import validate_file_size_10mb
from ...produto.models import (
    Fabricante,
    InformacaoNutricional,
    Marca,
    NomeDeProdutoEdital,
)
from ...terceirizada.models import Contrato, Terceirizada
from .qualidade import TipoEmbalagemQld


class UnidadeMedida(TemChaveExterna, Nomeavel, CriadoEm):
    abreviacao = models.CharField("Abreviação", max_length=25)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Unidade de Medida"
        verbose_name_plural = "Unidades de Medida"
        unique_together = ("nome",)

    def save(self, *args, **kwargs):
        self.nome = self.nome.upper()
        self.abreviacao = self.abreviacao.lower()
        super().save(*args, **kwargs)


class Cronograma(ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoCronograma):
    numero = models.CharField(
        "Número do Cronograma", blank=True, max_length=50, unique=True
    )
    contrato = models.ForeignKey(
        Contrato, on_delete=models.CASCADE, blank=True, null=True
    )
    empresa = models.ForeignKey(
        Terceirizada, on_delete=models.CASCADE, blank=True, null=True
    )
    qtd_total_programada = models.FloatField(
        "Qtd Total Programada", blank=True, null=True
    )
    unidade_medida = models.ForeignKey(
        UnidadeMedida, on_delete=models.PROTECT, blank=True, null=True
    )
    armazem = models.ForeignKey(
        Terceirizada,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="cronogramas",
    )
    ficha_tecnica = models.ForeignKey(
        "FichaTecnicaDoProduto",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    tipo_embalagem_secundaria = models.ForeignKey(
        TipoEmbalagemQld,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    custo_unitario_produto = models.FloatField(
        "Custo Unitário do Produto", blank=True, null=True
    )
    observacoes = models.TextField("Observações", blank=True)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.CRONOGRAMA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    def __str__(self):
        return f"Cronograma: {self.numero} - Status: {self.get_status_display()}"

    class Meta:
        verbose_name = "Cronograma"
        verbose_name_plural = "Cronogramas"


class EtapasDoCronograma(ModeloBase):
    cronograma = models.ForeignKey(
        Cronograma,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="etapas",
    )
    numero_empenho = models.CharField("Número do Empenho", blank=True, max_length=50)
    qtd_total_empenho = models.FloatField(
        "Qtde. Total do Empenho", blank=True, null=True
    )
    etapa = models.CharField(blank=True, max_length=15)
    parte = models.CharField(blank=True, max_length=15)
    data_programada = models.DateField("Data Programada", blank=True, null=True)
    quantidade = models.FloatField(blank=True, null=True)
    total_embalagens = models.FloatField("Total de Embalagens", blank=True, null=True)

    def __str__(self):
        if self.etapa and self.parte and self.cronograma:
            return f"{self.etapa} - {self.parte} - Cronograma {self.cronograma.numero}"

        if self.cronograma:
            return f"Etapa do Cronograma {self.cronograma.numero}"

        return "Etapa sem Cronograma"

    class Meta:
        verbose_name = "Etapa do Cronograma"
        verbose_name_plural = "Etapas dos Cronogramas"

    @classmethod
    def etapas_to_json(cls):
        etapas = cls.objects.annotate(
            etapa_numero=Cast(F('etapa').split(" ")[1], models.IntegerField())
        ).order_by('etapa_numero', 'parte', 'data_programada')
        
        result = []
        for etapa in etapas:
            choice = {"uuid": etapa.etapa, "value": etapa.etapa}
            result.append(choice)
        
        return result


class ProgramacaoDoRecebimentoDoCronograma(ModeloBase):
    PALETIZADA = "PALETIZADA"
    ESTIVADA_BATIDA = "ESTIVADA_BATIDA"

    TIPO_CARGA_CHOICES = (
        (PALETIZADA, "Paletizada"),
        (ESTIVADA_BATIDA, "Estivada / Batida"),
    )

    cronograma = models.ForeignKey(
        Cronograma,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="programacoes_de_recebimento",
    )
    data_programada = models.CharField(blank=True, max_length=50)
    tipo_carga = models.CharField(choices=TIPO_CARGA_CHOICES, max_length=20, blank=True)

    def __str__(self):
        if self.data_programada:
            return self.data_programada
        else:
            return str(self.id)

    class Meta:
        verbose_name = "Programação do Recebimento do Cromograma"
        verbose_name_plural = "Programações dos Recebimentos dos Cromogramas"


class SolicitacaoAlteracaoCronogramaQuerySet(models.QuerySet):
    def em_analise(self):
        return self.filter(status=CronogramaAlteracaoWorkflow.EM_ANALISE)

    def filtrar_por_status(self, status, filtros=None, init=None, end=None):
        log = (
            LogSolicitacoesUsuario.objects.filter(uuid_original=OuterRef("uuid"))
            .order_by("-criado_em")
            .values("criado_em")[:1]
        )
        if not isinstance(status, list):
            status = [status]
        qs = (
            self.filter(status__in=status)
            .annotate(log_criado_em=log)
            .order_by("-log_criado_em")
        )
        if filtros:
            qs = self._filtrar_por_atributos_adicionais(qs, filtros)

        if init is not None and end is not None:
            return qs[init:end]
        return qs

    def _filtrar_por_atributos_adicionais(self, qs, filtros):
        if filtros:
            if "nome_fornecedor" in filtros:
                qs = qs.filter(
                    cronograma__empresa__nome_fantasia__icontains=filtros[
                        "nome_fornecedor"
                    ]
                )
            if "numero_cronograma" in filtros:
                qs = qs.filter(
                    cronograma__numero__icontains=filtros["numero_cronograma"]
                )
            if "nome_produto" in filtros:
                qs = qs.filter(
                    cronograma__ficha_tecnica__produto__nome__icontains=filtros[
                        "nome_produto"
                    ]
                )
        return qs


class SolicitacaoAlteracaoCronograma(
    ModeloBase, TemIdentificadorExternoAmigavel, FluxoAlteracaoCronograma, Logs
):
    cronograma = models.ForeignKey(
        Cronograma, on_delete=models.PROTECT, related_name="solicitacoes_de_alteracao"
    )
    qtd_total_programada = models.FloatField(
        "Qtd Total Programada", blank=True, null=True
    )
    etapas_antigas = models.ManyToManyField(
        EtapasDoCronograma, related_name="etapas_antigas"
    )
    etapas_novas = models.ManyToManyField(
        EtapasDoCronograma, related_name="etapas_novas"
    )
    programacoes_novas = models.ManyToManyField(
        ProgramacaoDoRecebimentoDoCronograma,
        related_name="programacoes_novas",
        blank=True,
    )
    justificativa = models.TextField(
        "Justificativa de solicitação pelo fornecedor", blank=True
    )
    usuario_solicitante = models.ForeignKey(
        "perfil.Usuario", on_delete=models.DO_NOTHING
    )
    numero_solicitacao = models.CharField(
        "Número da solicitação", blank=True, max_length=50, unique=True
    )

    objects = SolicitacaoAlteracaoCronogramaQuerySet.as_manager()

    def gerar_numero_solicitacao(self):
        self.numero_solicitacao = f"{str(self.pk).zfill(8)}-ALT"

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.SOLICITACAO_DE_ALTERACAO_CRONOGRAMA,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )
        return log_transicao

    def cronograma_confirma_ciencia(self, justificativa, usuario, etapas, programacoes):
        from ..api.helpers import (
            cria_etapas_de_cronograma,
            cria_programacao_de_cronograma,
        )

        self.etapas_novas.all().delete()
        etapas_criadas = cria_etapas_de_cronograma(etapas)
        self.etapas_novas.set(etapas_criadas)
        programacoes_criadas = cria_programacao_de_cronograma(programacoes)
        self.programacoes_novas.set(programacoes_criadas)
        self.cronograma_ciente(user=usuario, justificativa=justificativa)
        self.save()

    def __str__(self):
        return f"Solicitação de alteração do cronograma: {self.numero_solicitacao}"

    class Meta:
        verbose_name = "Solicitação de Alteração de Cronograma"
        verbose_name_plural = "Solicitações de Alteração de Cronograma"


@receiver(post_save, sender=SolicitacaoAlteracaoCronograma)
def gerar_numero_solicitacao(sender, instance, created, **kwargs):
    if created:
        instance.gerar_numero_solicitacao()
        instance.save()


class ImagemDoTipoDeEmbalagem(TemChaveExterna):
    tipo_de_embalagem = models.ForeignKey(
        "TipoDeEmbalagemDeLayout",
        on_delete=models.CASCADE,
        related_name="imagens",
        blank=True,
    )
    arquivo = models.FileField(
        upload_to="layouts_de_embalagens",
        validators=[
            FileExtensionValidator(allowed_extensions=["PDF", "PNG", "JPG", "JPEG"]),
            validate_file_size_10mb,
        ],
    )
    nome = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return (
            f"{self.tipo_de_embalagem.tipo_embalagem} - {self.nome}"
            if self.tipo_de_embalagem
            else str(self.id)
        )

    def delete(self, *args, **kwargs):
        # Antes de excluir o objeto, exclui o arquivo associado
        if self.arquivo:
            if os.path.isfile(self.arquivo.path):
                os.remove(self.arquivo.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Imagem do Tipo de Embalagem"
        verbose_name_plural = "Imagens dos Tipos de Embalagens"


class TipoDeEmbalagemDeLayout(TemChaveExterna):
    STATUS_APROVADO = "APROVADO"
    STATUS_REPROVADO = "REPROVADO"
    STATUS_EM_ANALISE = "EM_ANALISE"
    TIPO_EMBALAGEM_PRIMARIA = "PRIMARIA"
    TIPO_EMBALAGEM_SECUNDARIA = "SECUNDARIA"
    TIPO_EMBALAGEM_TERCIARIA = "TERCIARIA"

    STATUS_CHOICES = (
        (STATUS_APROVADO, "Aprovado"),
        (STATUS_REPROVADO, "Reprovado"),
        (STATUS_EM_ANALISE, "Em análise"),
    )

    TIPO_EMBALAGEM_CHOICES = (
        (TIPO_EMBALAGEM_PRIMARIA, "Primária"),
        (TIPO_EMBALAGEM_SECUNDARIA, "Secundária"),
        (TIPO_EMBALAGEM_TERCIARIA, "Terciária"),
    )

    layout_de_embalagem = models.ForeignKey(
        "LayoutDeEmbalagem",
        on_delete=models.CASCADE,
        blank=True,
        related_name="tipos_de_embalagens",
    )
    tipo_embalagem = models.CharField(
        choices=TIPO_EMBALAGEM_CHOICES, max_length=10, blank=True
    )
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=10, default=STATUS_EM_ANALISE
    )
    complemento_do_status = models.TextField("Complemento do status", blank=True)

    def __str__(self):
        return (
            f"{self.tipo_embalagem} - {self.status}"
            if self.tipo_embalagem
            else str(self.id)
        )

    class Meta:
        verbose_name = "Tipo de Embalagem de Layout"
        verbose_name_plural = "Tipos de Embalagens de Layout"
        unique_together = ["layout_de_embalagem", "tipo_embalagem"]


class LayoutDeEmbalagem(
    ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoLayoutDeEmbalagem
):
    ficha_tecnica = models.OneToOneField(
        "FichaTecnicaDoProduto",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="layout_embalagem",
    )
    observacoes = models.TextField("Observações", blank=True)

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.LAYOUT_DE_EMBALAGEM,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )

    @property
    def aprovado(self):
        return (
            self.tipos_de_embalagens.filter(status="APROVADO").count()
            == self.tipos_de_embalagens.count()
        )

    @property
    def eh_primeira_analise(self):
        if self.log_mais_recente is not None:
            return (
                not self.log_mais_recente.status_evento
                == LogSolicitacoesUsuario.LAYOUT_CORRECAO_REALIZADA
            )

        return True

    def __str__(self):
        try:
            return f"Layout de Embalagens {self.ficha_tecnica.numero} - {self.ficha_tecnica.produto.nome}"
        except AttributeError:
            return f"Layout de Embalagens {self.id}"

    class Meta:
        verbose_name = "Layout de Embalagem"
        verbose_name_plural = "Layouts de Embalagem"


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


class FichaTecnicaDoProduto(
    ModeloBase, TemIdentificadorExternoAmigavel, Logs, FluxoFichaTecnicaDoProduto
):
    CATEGORIA_PERECIVEIS = "PERECIVEIS"
    CATEGORIA_NAO_PERECIVEIS = "NAO_PERECIVEIS"

    CATEGORIA_CHOICES = (
        (CATEGORIA_PERECIVEIS, "Perecíveis"),
        (CATEGORIA_NAO_PERECIVEIS, "Não Perecíveis"),
    )

    MECANISMO_CERTIFICACAO = "CERTIFICACAO"
    MECANISMO_OPAC = "OPAC"
    MECANISMO_OCS = "OCS"

    MECANISMO_CONTROLE_CHOICES = (
        (MECANISMO_CERTIFICACAO, "Certificação"),
        (MECANISMO_OPAC, "OPAC"),
        (MECANISMO_OCS, "OCS"),
    )

    numero = models.CharField(
        "Número da Ficha Técnica", blank=True, max_length=50, unique=True
    )
    produto = models.ForeignKey(
        NomeDeProdutoEdital,
        on_delete=models.PROTECT,
        related_name="fichas_tecnicas",
    )
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, blank=True, null=True)
    categoria = models.CharField(choices=CATEGORIA_CHOICES, max_length=14, blank=True)
    pregao_chamada_publica = models.CharField(
        "Nº do Pregão Eletrônico", max_length=100, blank=True
    )
    empresa = models.ForeignKey(
        Terceirizada,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="fichas_tecnicas",
    )
    fabricante = models.ForeignKey(
        Fabricante,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="fichas_tecnicas",
    )
    cnpj_fabricante = models.CharField(
        "CNPJ",
        validators=[MinLengthValidator(14)],
        max_length=14,
        blank=True,
    )
    cep_fabricante = models.CharField("CEP", max_length=8, blank=True)
    endereco_fabricante = models.CharField("Endereco", max_length=160, blank=True)
    numero_fabricante = models.CharField("Número", max_length=10, blank=True)
    complemento_fabricante = models.CharField("Complemento", max_length=50, blank=True)
    bairro_fabricante = models.CharField("Bairro", max_length=150, blank=True)
    cidade_fabricante = models.CharField("Cidade", max_length=150, blank=True)
    estado_fabricante = models.CharField("Estado", max_length=150, blank=True)
    email_fabricante = models.EmailField(blank=True)
    telefone_fabricante = models.CharField(
        max_length=13, validators=[MinLengthValidator(8)], blank=True
    )
    prazo_validade = models.CharField("Prazo de Validade", max_length=150, blank=True)
    numero_registro = models.CharField(
        "Nº do Registro do Rótulo", max_length=150, blank=True
    )
    agroecologico = models.BooleanField("É agroecológico?", null=True)
    organico = models.BooleanField("É orgânico?", null=True)
    mecanismo_controle = models.CharField(
        choices=MECANISMO_CONTROLE_CHOICES, max_length=12, blank=True
    )
    componentes_produto = models.CharField(
        "Componentes do Produto", max_length=250, blank=True
    )
    alergenicos = models.BooleanField("Pode conter alergênicos?", null=True)
    ingredientes_alergenicos = models.CharField(
        "Ingredientes/aditivos alergênicos", max_length=150, blank=True
    )
    gluten = models.BooleanField("Contém glúten?", null=True)
    lactose = models.BooleanField("Contém lactose?", null=True)
    lactose_detalhe = models.CharField("Detalhar Lactose", max_length=150, blank=True)
    porcao = models.CharField("Porção", max_length=100, blank=True, null=True)
    unidade_medida_porcao = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_unidade_porcao",
    )
    valor_unidade_caseira = models.CharField(
        "Unidade Caseira",
        max_length=100,
        blank=True,
        null=True,
    )
    unidade_medida_caseira = models.CharField(
        "Unidade de Medida Caseira",
        max_length=100,
        blank=True,
    )
    prazo_validade_descongelamento = models.CharField(
        "Prazo de Validade Descongelamento",
        help_text="Prazo de Validade após o descongelamento e mantido sob refrigeração",
        max_length=50,
        blank=True,
    )
    condicoes_de_conservacao = models.TextField(
        "Condições de conservação",
        help_text="Condições de conservação e Prazo máximo para consumo após a abertura da embalagem primária",
        blank=True,
    )
    temperatura_congelamento = models.FloatField(
        "Temperatura de Congelamento do Produto",
        blank=True,
        null=True,
    )
    temperatura_veiculo = models.FloatField(
        "Temperatura Interna do Veículo para Transporte",
        blank=True,
        null=True,
    )
    condicoes_de_transporte = models.TextField("Condições de Transporte", blank=True)
    embalagem_primaria = models.TextField("Embalagem Primária", blank=True)
    embalagem_secundaria = models.TextField("Embalagem Secundária", blank=True)
    embalagens_de_acordo_com_anexo = models.BooleanField(
        "Embalagens de Acordo com Anexo?",
        help_text="Declaro que as embalagens primária e secundária em que serão entregues o produto estarão de acordo "
        "com as especificações do Anexo I do Edital",
        null=True,
    )
    material_embalagem_primaria = models.TextField(
        "Material da Embalagem Primária", blank=True
    )
    produto_eh_liquido = models.BooleanField("O produto é líquido?", null=True)
    volume_embalagem_primaria = models.FloatField(
        blank=True, null=True, help_text="Volume do Produto na Embalagem Primária"
    )
    unidade_medida_volume_primaria = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_volume_primaria",
    )
    peso_liquido_embalagem_primaria = models.FloatField(
        blank=True, null=True, help_text="Peso Líquido do Produto na Embalagem Primária"
    )
    unidade_medida_primaria = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_unidade_primaria",
    )
    peso_liquido_embalagem_secundaria = models.FloatField(
        blank=True,
        null=True,
        help_text="Peso Líquido do Produto na Embalagem Secundária",
    )
    unidade_medida_secundaria = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_unidade_secundaria",
    )
    peso_embalagem_primaria_vazia = models.FloatField(blank=True, null=True)
    unidade_medida_primaria_vazia = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_primaria_vazia",
    )
    peso_embalagem_secundaria_vazia = models.FloatField(blank=True, null=True)
    unidade_medida_secundaria_vazia = models.ForeignKey(
        UnidadeMedida,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_secundaria_vazia",
    )
    variacao_percentual = models.FloatField(blank=True, null=True)
    sistema_vedacao_embalagem_secundaria = models.TextField(
        "Sistema de Vedação da Embalagem Secundária", blank=True
    )
    rotulo_legivel = models.BooleanField(
        "Rotulo Legível?",
        help_text="Declaro que no rótulo da embalagem primária e, se for o caso, da secundária, constarão, de forma "
        "legível e indelével, todas as informações solicitadas do Anexo I do Edital",
        null=True,
    )
    nome_responsavel_tecnico = models.CharField(
        "Nome completo do Responsável Técnico", max_length=100, blank=True
    )
    habilitacao = models.CharField("Habilitação", max_length=100, blank=True)
    numero_registro_orgao = models.CharField(
        "Nº do Registro em Órgão Competente", max_length=50, blank=True
    )
    arquivo = models.FileField(
        upload_to="fichas_tecnicas",
        validators=[
            FileExtensionValidator(allowed_extensions=["PDF"]),
            validate_file_size_10mb,
        ],
        null=True,
    )
    modo_de_preparo = models.TextField("Modo de Preparo do Produto", blank=True)
    informacoes_adicionais = models.TextField("Informações Adicionais", blank=True)

    def __str__(self):
        return f"{self.numero} - {self.produto.nome}" if self.produto else self.numero

    class Meta:
        verbose_name = "Ficha Técnica do Produto"
        verbose_name_plural = "Fichas Técnicas dos Produtos"

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        justificativa = kwargs.get("justificativa", "")
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.FICHA_TECNICA_DO_PRODUTO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )
        return log_transicao

    def gerar_numero_ficha_tecnica(self):
        self.numero = f"FT{str(self.pk).zfill(3)}"


@receiver(post_save, sender=FichaTecnicaDoProduto)
def gerar_numero_ficha_tecnica(sender, instance, created, **kwargs):
    if created:
        instance.gerar_numero_ficha_tecnica()
        instance.save()


class InformacoesNutricionaisFichaTecnica(TemChaveExterna):
    ficha_tecnica = models.ForeignKey(
        FichaTecnicaDoProduto,
        on_delete=models.CASCADE,
        related_name="informacoes_nutricionais",
    )
    informacao_nutricional = models.ForeignKey(
        InformacaoNutricional,
        on_delete=models.DO_NOTHING,
    )
    quantidade_por_100g = models.CharField(max_length=10)
    quantidade_porcao = models.CharField(max_length=10)
    valor_diario = models.CharField(max_length=10)

    def __str__(self):
        nome_produto = self.ficha_tecnica.produto.nome
        informacao_nutricional = self.informacao_nutricional.nome
        return (
            f"{nome_produto} - {informacao_nutricional} =>"
            + f" quantidade por 100g: {self.quantidade_por_100g}"
            + f" quantidade por porção: {self.quantidade_porcao}"
            + f" valor diario: {self.valor_diario}"
        )

    class Meta:
        verbose_name = "Informação Nutricional da Ficha Técnica"
        verbose_name_plural = "Informações Nutricionais da Ficha Técnica"


class AnaliseFichaTecnica(ModeloBase, CriadoPor):
    ficha_tecnica = models.ForeignKey(
        FichaTecnicaDoProduto,
        on_delete=models.CASCADE,
        related_name="analises",
    )
    detalhes_produto_conferido = models.BooleanField(null=True)
    detalhes_produto_correcoes = models.TextField(blank=True)
    informacoes_nutricionais_conferido = models.BooleanField(null=True)
    informacoes_nutricionais_correcoes = models.TextField(blank=True)
    conservacao_conferido = models.BooleanField(null=True)
    conservacao_correcoes = models.TextField(blank=True)
    temperatura_e_transporte_conferido = models.BooleanField(null=True)
    temperatura_e_transporte_correcoes = models.TextField(blank=True)
    armazenamento_conferido = models.BooleanField(null=True)
    armazenamento_correcoes = models.TextField(blank=True)
    embalagem_e_rotulagem_conferido = models.BooleanField(null=True)
    embalagem_e_rotulagem_correcoes = models.TextField(blank=True)
    responsavel_tecnico_conferido = models.BooleanField(null=True)
    modo_preparo_conferido = models.BooleanField(null=True)
    outras_informacoes_conferido = models.BooleanField(null=True)

    @property
    def aprovada(self):
        return (
            (
                self.detalhes_produto_conferido is True
                and not self.detalhes_produto_correcoes
            )
            and (
                self.informacoes_nutricionais_conferido is True
                and not self.informacoes_nutricionais_correcoes
            )
            and (self.conservacao_conferido is True and not self.conservacao_correcoes)
            and (
                self.temperatura_e_transporte_conferido in [True, None]
                and not self.temperatura_e_transporte_correcoes
            )
            and (
                self.armazenamento_conferido is True
                and not self.armazenamento_correcoes
            )
            and (
                self.embalagem_e_rotulagem_conferido is True
                and not self.embalagem_e_rotulagem_correcoes
            )
            and self.responsavel_tecnico_conferido is True
            and self.modo_preparo_conferido is True
            and self.outras_informacoes_conferido is True
        )

    class Meta:
        verbose_name = "Análise da Ficha Técnica"
        verbose_name_plural = "Análises das Fichas Técnicas"
