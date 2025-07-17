import os

from django.core.validators import FileExtensionValidator
from django.db import models
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto

from ...dados_comuns.behaviors import (
    Logs,
    ModeloBase,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)
from ...dados_comuns.fluxo_status import (
    FluxoLayoutDeEmbalagem,
)
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.validators import validate_file_size_10mb


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
        FichaTecnicaDoProduto,
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
