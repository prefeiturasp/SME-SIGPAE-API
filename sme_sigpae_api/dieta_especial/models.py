from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models

from ..dados_comuns.behaviors import (
    ArquivoCargaBase,
    Ativavel,
    CriadoEm,
    CriadoPor,
    Nomeavel,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)
from ..escola.models import Aluno
from .solicitacao_dieta_especial.models import SolicitacaoDietaEspecial


class SolicitacoesDietaEspecialAtivasInativasPorAluno(models.Model):
    aluno = models.OneToOneField(Aluno, on_delete=models.DO_NOTHING, primary_key=True)
    ativas = models.IntegerField()
    inativas = models.IntegerField()

    class Meta:
        managed = False
        db_table = "dietas_ativas_inativas_por_aluno"


class Alimento(Nomeavel, TemChaveExterna, Ativavel):
    TIPO_CHOICES = (("E", "Edital"), ("P", "Proprio"))
    SO_ALIMENTOS = "SO_ALIMENTOS"
    SO_SUBSTITUTOS = "SO_SUBSTITUTOS"
    AMBOS = "AMBOS"
    TIPO_LISTAGEM_PROTOCOLO = (
        (SO_ALIMENTOS, "Aparece somente na listagem de alimentos"),
        (SO_SUBSTITUTOS, "Aparece somente na listagem de alimentos substitutos"),
        (AMBOS, "Aparece nas listagem de alimentos e substitutos"),
    )

    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, default="E")
    marca = models.ForeignKey(
        "produto.Marca", on_delete=models.PROTECT, blank=True, null=True
    )
    outras_informacoes = models.CharField(max_length=255, blank=True)
    tipo_listagem_protocolo = models.CharField(
        max_length=15, choices=TIPO_LISTAGEM_PROTOCOLO, default=SO_ALIMENTOS
    )

    class Meta:
        ordering = ("nome",)
        unique_together = ("nome", "marca")

    def __str__(self):
        return self.nome


class SubstituicaoAlimento(models.Model):
    TIPO_CHOICES = [("I", "Isento"), ("S", "Substituir")]
    solicitacao_dieta_especial = models.ForeignKey(
        SolicitacaoDietaEspecial, on_delete=models.CASCADE
    )
    alimento = models.ForeignKey(
        Alimento, on_delete=models.PROTECT, blank=True, null=True
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, blank=True)
    substitutos = models.ManyToManyField(
        "produto.Produto",
        related_name="substitutos",
        blank=True,
        help_text="produtos substitutos",
    )
    alimentos_substitutos = models.ManyToManyField(
        Alimento, related_name="alimentos_substitutos", blank=True
    )


class PlanilhaDietasAtivas(models.Model):
    """Importa dados de planilha de Dietas Ativas específicas.

    Requer uma planilha com o De Para entre Código Escola e Código EOL da Escola.
    """

    arquivo = models.FileField(
        blank=True, null=True, help_text="Arquivo com escolas e dietas"
    )  # noqa DJ01
    arquivo_unidades_da_rede = models.FileField(
        blank=True, null=True, help_text="Arquivo unidades_da_rede...xlsx"
    )  # noqa DJ01
    resultado = models.FileField(
        blank=True, null=True, help_text="Arquivo com o resultado"
    )  # noqa DJ01
    tempfile = models.CharField(
        max_length=100, null=True, blank=True, help_text="JSON temporario"
    )  # noqa DJ01
    criado_em = models.DateTimeField("criado em", auto_now_add=True, auto_now=False)

    class Meta:
        ordering = ("-criado_em",)
        verbose_name = "Planilha Dieta Ativa"
        verbose_name_plural = "Planilhas Dietas Ativas"

    def __str__(self):
        return str(self.arquivo)


class AlimentoSubstituto(models.Model):
    substituicao_alimento_protocolo_padrao = models.ForeignKey(
        "SubstituicaoAlimentoProtocoloPadrao", on_delete=models.SET_NULL, null=True
    )
    alimento = models.ForeignKey(
        Alimento, on_delete=models.SET_NULL, null=True, blank=True
    )


class ProtocoloPadraoDietaEspecial(
    TemChaveExterna, CriadoEm, CriadoPor, TemIdentificadorExternoAmigavel, Ativavel
):
    # Mantive para termos um histórico acessível pelo admin
    history = AuditlogHistoryField()

    # Status Choice
    STATUS_LIBERADO = "LIBERADO"
    STATUS_NAO_LIBERADO = "NAO_LIBERADO"

    STATUS_NOMES = {
        STATUS_LIBERADO: "Liberado",
        STATUS_NAO_LIBERADO: "Não Liberado",
    }

    STATUS_CHOICES = (
        (STATUS_LIBERADO, STATUS_NOMES[STATUS_LIBERADO]),
        (STATUS_NAO_LIBERADO, STATUS_NOMES[STATUS_NAO_LIBERADO]),
    )

    nome_protocolo = models.TextField("Nome do Protocolo")

    orientacoes_gerais = models.TextField("Orientações Gerais", blank=True)

    status = models.CharField(
        "Status da guia",
        max_length=25,
        choices=STATUS_CHOICES,
        default=STATUS_NAO_LIBERADO,
    )

    outras_informacoes = models.TextField("Outras Informações", blank=True)

    editais = models.ManyToManyField(
        "terceirizada.Edital", related_name="protocolos_padroes_dieta_especial"
    )

    historico = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ("nome_protocolo",)
        verbose_name = "Protocolo padrão de dieta especial"
        verbose_name_plural = "Protocolos padrões de dieta especial"

    def __str__(self):
        return str(self.nome_protocolo)


class SubstituicaoAlimentoProtocoloPadrao(models.Model):
    history = AuditlogHistoryField()

    TIPO_CHOICES = [("I", "Isento"), ("S", "Substituir")]
    protocolo_padrao = models.ForeignKey(
        ProtocoloPadraoDietaEspecial,
        on_delete=models.CASCADE,
        related_name="substituicoes",
    )
    alimento = models.ForeignKey(
        Alimento, on_delete=models.PROTECT, blank=True, null=True
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, blank=True)
    substitutos = models.ManyToManyField(
        "produto.Produto",
        related_name="substitutos_protocolo_padrao",
        blank=True,
        help_text="produtos substitutos",
    )
    alimentos_substitutos = models.ManyToManyField(
        Alimento,
        related_name="alimentos_substitutos_protocolo_padrao",
        blank=True,
        through="AlimentoSubstituto",
    )

    class Meta:
        verbose_name = "Substituição de alimento para protocolo padrão de dieta"
        verbose_name_plural = (
            "Substituições de alimentos para protocolos padrões de dietas"
        )

    def __str__(self):
        return f"substituição protocolo padrão: {self.protocolo_padrao}, tipo: {self.tipo}."


auditlog.register(ProtocoloPadraoDietaEspecial)
auditlog.register(SubstituicaoAlimentoProtocoloPadrao)
auditlog.register(SubstituicaoAlimentoProtocoloPadrao.alimentos_substitutos.through)
auditlog.register(AlimentoSubstituto)


class ArquivoCargaDietaEspecial(ArquivoCargaBase):
    resultado = models.FileField(blank=True, default="")

    class Meta:
        verbose_name = "Arquivo para importação de solicitações de Dieta Especial"
        verbose_name_plural = (
            "Arquivos para importação de solicitações de Dieta Especial"
        )

    def __str__(self) -> str:
        return str(self.conteudo)


class ArquivoCargaAlimentosSubstitutos(ArquivoCargaBase):
    class Meta:
        verbose_name = "Arquivo para importação de Alimentos e Alimentos substitutos"
        verbose_name_plural = (
            "Arquivos para importação de Alimentos e Alimentos substitutos"
        )

    def __str__(self) -> str:
        return str(self.conteudo)
