"""Modelos do módulo de recebimento.

Formaliza o recebimento físico dos produtos entregues contra as etapas
dos cronogramas: a ficha de recebimento registra a conformidade da
entrega (lotes, datas, pesos, vedações), os veículos e notas fiscais, as
respostas às questões de conferência, as ocorrências (falta/recusa) e os
anexos.
"""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from multiselectfield import MultiSelectField

from src.dados_comuns.behaviors import (
    Logs,
    ModeloBase,
    TemArquivosDeletaveis,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)
from src.dados_comuns.fluxo_status import FluxoFichaDeRecebimento
from src.dados_comuns.models import LogSolicitacoesUsuario
from src.dados_comuns.validators import validate_file_size_10mb
from src.pre_recebimento.cronograma_entrega.models import EtapasDoCronograma
from src.pre_recebimento.documento_recebimento.models import (
    DocumentoDeRecebimento,
)
from src.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto


class QuestaoConferencia(ModeloBase):
    """Questão de conferência utilizada nas fichas de recebimento.

    Compõe o catálogo de perguntas de inspeção (embalagem primária e/ou
    secundária) respondidas durante o recebimento. Pode ser marcada como
    obrigatória, exigindo então uma ``posicao`` para ordenação.
    """
    # Tipo Questão Choice
    TIPO_QUESTAO_PRIMARIA = "PRIMARIA"
    TIPO_QUESTAO_SECUNDARIA = "SECUNDARIA"

    TIPO_QUESTAO_NOMES = {
        TIPO_QUESTAO_PRIMARIA: "Primária",
        TIPO_QUESTAO_SECUNDARIA: "Secundária",
    }

    TIPO_QUESTAO_CHOICES = (
        (TIPO_QUESTAO_PRIMARIA, TIPO_QUESTAO_NOMES[TIPO_QUESTAO_PRIMARIA]),
        (TIPO_QUESTAO_SECUNDARIA, TIPO_QUESTAO_NOMES[TIPO_QUESTAO_SECUNDARIA]),
    )

    # status choice
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"

    STATUS_CHOICES = (
        (ATIVO, "Ativo"),
        (INATIVO, "Inativo"),
    )

    questao = models.CharField("Questão")
    tipo_questao = MultiSelectField("Tipo de Questão", choices=TIPO_QUESTAO_CHOICES)
    pergunta_obrigatoria = models.BooleanField("Pergunta Obrigatória?", default=False)
    posicao = models.PositiveSmallIntegerField("Posição", blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default=ATIVO)

    def __str__(self):
        """Retorna o texto da questão."""
        return f"{self.questao}"

    class Meta:
        verbose_name = "Questão para Conferência"
        verbose_name_plural = "Questões para Conferência"

    def clean(self):
        """Valida que a posição é informada quando a pergunta é obrigatória.

        Raises:
            ValidationError: Se ``pergunta_obrigatoria`` for ``True`` e
                ``posicao`` não estiver preenchida.
        """
        super().clean()
        if self.pergunta_obrigatoria and not self.posicao:
            raise ValidationError(
                {"posicao": "Posição é obrigatória se a pergunta for obrigatória."}
            )


class QuestoesPorProduto(ModeloBase):
    """Vínculo entre a ficha técnica do produto e as questões de conferência.

    Define, para cada ficha técnica, quais questões de embalagem primária e
    secundária devem ser respondidas na ficha de recebimento do produto.
    """

    ficha_tecnica = models.OneToOneField(
        FichaTecnicaDoProduto,
        on_delete=models.CASCADE,
        related_name="questoes_conferencia",
    )
    questoes_primarias = models.ManyToManyField(
        QuestaoConferencia,
        verbose_name="Questões referentes à Embalagem Primária",
        related_name="questoes_primarias",
    )
    questoes_secundarias = models.ManyToManyField(
        QuestaoConferencia,
        verbose_name="Questões referentes à Embalagem Secundária",
        related_name="questoes_secundarias",
    )

    def __str__(self):
        """Retorna a representação textual das questões da ficha técnica."""
        return f"Questões da Ficha: {self.ficha_tecnica}"

    class Meta:
        verbose_name = "Questões por Produto"
        verbose_name_plural = "Questões por Produtos"


class ReposicaoCronogramaFichaRecebimento(ModeloBase):
    """Tipo de reposição de cronograma escolhido na ficha de recebimento.

    Define a forma de compensação quando há produtos faltantes ou recusados
    no recebimento: repor os produtos, fazer carta de crédito do valor pago
    ou outros.
    """

    TIPO_CHOICES = (
        ("Repor", "Repor os produtos faltantes/recusados"),
        ("Credito", "Fazer uma carta de crédito do valor pago"),
        ("Outros", "Outros"),
    )

    tipo = models.CharField(
        "Tipo",
        max_length=7,
        choices=TIPO_CHOICES,
    )
    descricao = models.TextField(
        "Descrição",
        blank=True,
        null=True,
    )

    def __str__(self):
        """Retorna o tipo e a descrição da reposição."""
        return f"{self.tipo} - {self.descricao}"

    class Meta:
        verbose_name = "Reposição Cronograma da Ficha de Recebimento"
        verbose_name_plural = "Reposições Cronogramas das Fichas de Recebimento"
        ordering = ["criado_em"]


class FichaDeRecebimento(
    ModeloBase, FluxoFichaDeRecebimento, TemIdentificadorExternoAmigavel, Logs
):
    """Ficha de recebimento: registro central do recebimento físico.

    Confirma a entrega dos produtos contra uma etapa do cronograma,
    registrando a conformidade dos lotes do fabricante, datas de fabricação
    e validade, número do lote de armazenagem, paletes, pesos das
    embalagens primárias, sistema de vedação da embalagem secundária, as
    respostas às questões de conferência, os veículos e notas fiscais, as
    ocorrências (falta/recusa/outros), os anexos e a reposição de
    cronograma.

    O status é gerenciado pelo ``FluxoFichaDeRecebimento``: a ficha inicia
    como ``RASCUNHO`` e é assinada (``ASSINADA``) pela transição
    ``inicia_fluxo``; uma ficha assinada pode voltar para ``RASCUNHO``
    (``volta_para_rascunho``) ao ser editada.
    """

    etapa = models.ForeignKey(
        EtapasDoCronograma,
        on_delete=models.PROTECT,
        related_name="ficha_recebimento",
        verbose_name="Etapa do Cronograma",
    )
    data_entrega = models.DateField(
        "Data de Entrega",
        null=True,
        blank=True,
    )

    documentos_recebimento = models.ManyToManyField(
        DocumentoDeRecebimento,
        through="DocumentoFichaDeRecebimento",
        through_fields=("ficha_recebimento", "documento_recebimento"),
        related_name="fichas_recebimentos",
    )
    lote_fabricante_de_acordo = models.BooleanField(
        "Lote(s) do Fabricante Observado(s) estão de acordo?",
        null=True,
        blank=True,
    )
    lote_fabricante_divergencia = models.CharField(
        "Descrição da divergência nos Lote(s) do Fabricante",
        max_length=500,
        null=True,
        blank=True,
    )
    data_fabricacao_de_acordo = models.BooleanField(
        "Data(s) de Fabricação Observada(s) estão de acordo?",
        null=True,
        blank=True,
    )
    data_fabricacao_divergencia = models.CharField(
        "Descrição da divergência nas Data(s) de Fabricação",
        max_length=500,
        null=True,
        blank=True,
    )
    data_validade_de_acordo = models.BooleanField(
        "Data(s) de Validades Observada(s) estão de acordo?",
        null=True,
        blank=True,
    )
    data_validade_divergencia = models.CharField(
        "Descrição da divergência nas Data(s) de Validades",
        max_length=500,
        null=True,
        blank=True,
    )
    numero_lote_armazenagem = models.CharField(
        "Nº do Lote Armazenagem",
        max_length=50,
        null=True,
        blank=True,
    )
    numero_paletes = models.IntegerField(
        "Nº de Paletes",
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_1 = models.FloatField(
        "Peso da Embalagem Primária (1)", null=True, blank=True
    )
    peso_embalagem_primaria_2 = models.FloatField(
        "Peso da Embalagem Primária (2)", null=True, blank=True
    )
    peso_embalagem_primaria_3 = models.FloatField(
        "Peso da Embalagem Primária (3)", null=True, blank=True
    )
    peso_embalagem_primaria_4 = models.FloatField(
        "Peso da Embalagem Primária (4)", null=True, blank=True
    )

    sistema_vedacao_embalagem_secundaria = models.TextField(
        "Sistema de Vedação da Embalagem Secundária",
        null=True,
        blank=True,
    )

    questoes_conferencia = models.ManyToManyField(
        QuestaoConferencia,
        through="QuestaoFichaRecebimento",
        related_name="fichas_vinculadas",
    )

    houve_ocorrencia = models.BooleanField(
        "Houve Ocorrência?",
        null=True,
        blank=True,
    )

    observacoes_conferencia = models.TextField(
        null=True,
        blank=True,
    )

    observacao = models.TextField(
        null=True,
        blank=True,
    )

    reposicao_cronograma = models.ForeignKey(
        ReposicaoCronogramaFichaRecebimento,
        on_delete=models.PROTECT,
        related_name="reposicao_cronograma",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        """Retorna a representação textual da ficha de recebimento."""
        try:
            return f"Ficha de Recebimento - {str(self.etapa)}"

        except AttributeError:
            return f"Ficha de Recebimento {self.id}"

    def salvar_log_transicao(self, status_evento, usuario, **kwargs):
        """Registra o log de transição de status da ficha.

        Cria um ``LogSolicitacoesUsuario`` com o tipo
        ``FICHA_RECEBIMENTO``, incluindo a justificativa quando houver.

        Args:
            status_evento: Evento de status a registrar.
            usuario: Usuário que executou a transição.
            **kwargs: Pode conter ``justificativa``.

        Returns:
            O registro de log criado.
        """
        justificativa = kwargs.get("justificativa", "")
        log_transicao = LogSolicitacoesUsuario.objects.create(
            descricao=str(self),
            status_evento=status_evento,
            solicitacao_tipo=LogSolicitacoesUsuario.FICHA_RECEBIMENTO,
            usuario=usuario,
            uuid_original=self.uuid,
            justificativa=justificativa,
        )
        return log_transicao

    class Meta:
        verbose_name = "Ficha de Recebimento"
        verbose_name_plural = "Fichas de Recebimentos"


class VeiculoFichaDeRecebimento(models.Model):
    """Veículo e nota fiscal de uma ficha de recebimento.

    Registra, por veículo entregue, as temperaturas de recebimento e do
    produto, placa, lacre, número SIF/SISBI/SISP, número da nota fiscal,
    quantidades e embalagens da nota versus recebidas, estado higiênico-
    sanitário e uso de termógrafo.
    """

    ficha_recebimento = models.ForeignKey(
        FichaDeRecebimento,
        on_delete=models.CASCADE,
        related_name="veiculos",
    )
    numero = models.CharField(
        "Nº do Veículo",
        max_length=25,
    )
    temperatura_recebimento = models.CharField(
        "Temperatura da Área de Recebimento (°C)",
        max_length=10,
        null=True,
        blank=True,
    )
    temperatura_produto = models.CharField(
        "Temperatura do Produto (°C)",
        max_length=10,
        null=True,
        blank=True,
    )
    placa = models.CharField(
        max_length=15,
        null=True,
        blank=True,
    )
    lacre = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    numero_sif_sisbi_sisp = models.CharField(
        "Nº SIF, SISBI ou SISP",
        max_length=100,
        null=True,
        blank=True,
    )
    numero_nota_fiscal = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    quantidade_nota_fiscal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    embalagens_nota_fiscal = models.IntegerField(
        "Quantidade de Embalagens da Nota Fiscal",
        null=True,
        blank=True,
    )
    quantidade_recebida = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
    )
    embalagens_recebidas = models.IntegerField(
        "Quantidade de Embalagens Recebidas",
        null=True,
        blank=True,
    )
    estado_higienico_adequado = models.BooleanField(
        "Estado Higiênico-Sanitário adequado?",
        null=True,
        blank=True,
    )
    termografo = models.BooleanField(
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        """Retorna o número do veículo e a ficha de recebimento."""
        return f"{self.numero} - {self.ficha_recebimento}"

    class Meta:
        verbose_name = "Veículo Ficha de Recebimento"
        verbose_name_plural = "Veículos Fichas de Recebimentos"


class ArquivoFichaRecebimento(TemChaveExterna, TemArquivosDeletaveis):
    """Arquivo anexado a uma ficha de recebimento.

    Aceita arquivos ``PDF``, ``PNG``, ``JPG`` e ``JPEG``, com tamanho
    máximo de 10MB (``validate_file_size_10mb``). Os arquivos são enviados
    como base64 pela API e convertidos para ``ContentFile`` no helper de
    criação. A exclusão do registro também remove o arquivo físico do
    armazenamento (``TemArquivosDeletaveis``).
    """

    ficha_recebimento = models.ForeignKey(
        FichaDeRecebimento,
        on_delete=models.CASCADE,
        related_name="arquivos",
    )
    arquivo = models.FileField(
        upload_to="arquivos_fichas_de_recebimentos",
        validators=[
            FileExtensionValidator(allowed_extensions=["PDF", "PNG", "JPG", "JPEG"]),
            validate_file_size_10mb,
        ],
    )
    nome = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    def __str__(self):
        """Retorna o nome do arquivo e a ficha de recebimento."""
        return (
            f"{self.nome} - {self.ficha_recebimento}"
            if self.nome
            else f"Arquivo {self.ficha_recebimento}"
        )

    class Meta:
        verbose_name = "Arquivo Ficha de Recebimento"
        verbose_name_plural = "Arquivos Fichas de Recebimentos"


class QuestaoFichaRecebimento(ModeloBase):
    """Resposta a uma questão de conferência em uma ficha de recebimento.

    Registra a resposta (Sim/Não) dada a cada questão de conferência na
    ficha, com o tipo de embalagem (primária ou secundária). A combinação
    de ficha, questão e tipo é única (``unique_together``).
    """
    TIPO_QUESTAO_PRIMARIA = "PRIMARIA"
    TIPO_QUESTAO_SECUNDARIA = "SECUNDARIA"

    TIPO_QUESTAO_NOMES = {
        TIPO_QUESTAO_PRIMARIA: "Primária",
        TIPO_QUESTAO_SECUNDARIA: "Secundária",
    }

    TIPO_QUESTAO_CHOICES = (
        (TIPO_QUESTAO_PRIMARIA, TIPO_QUESTAO_NOMES[TIPO_QUESTAO_PRIMARIA]),
        (TIPO_QUESTAO_SECUNDARIA, TIPO_QUESTAO_NOMES[TIPO_QUESTAO_SECUNDARIA]),
    )

    ficha_recebimento = models.ForeignKey(
        FichaDeRecebimento,
        on_delete=models.CASCADE,
        verbose_name="Ficha de Recebimento",
    )
    questao_conferencia = models.ForeignKey(
        QuestaoConferencia,
        on_delete=models.CASCADE,
        verbose_name="Questão de Conferência",
    )
    resposta = models.BooleanField("Resposta (Sim/Não)", null=True, blank=True)

    tipo_questao = models.CharField(choices=TIPO_QUESTAO_CHOICES)

    class Meta:
        verbose_name = "Questão por Ficha de Recebimento"
        verbose_name_plural = "Questões por Fichas de Recebimento"
        unique_together = ("ficha_recebimento", "questao_conferencia", "tipo_questao")

    def __str__(self):
        """Retorna a questão e a ficha de recebimento."""
        return f"{self.questao_conferencia.questao} - {self.ficha_recebimento}"


class DocumentoFichaDeRecebimento(ModeloBase):
    """Vínculo entre a ficha de recebimento e o documento de recebimento.

    Modelo intermediário (through) da relação M:N entre fichas e documentos
    de recebimento, registrando a ``quantidade_recebida`` de cada documento
    na ficha. A combinação ficha + documento é única
    (``unique_together``).
    """

    ficha_recebimento = models.ForeignKey(
        FichaDeRecebimento,
        on_delete=models.CASCADE,
        related_name="documentos_ficha",
        verbose_name="Ficha de Recebimento",
    )
    documento_recebimento = models.ForeignKey(
        DocumentoDeRecebimento,
        on_delete=models.CASCADE,
        related_name="fichas_documentos",
        verbose_name="Documento de Recebimento",
    )
    quantidade_recebida = models.DecimalField(
        "Quantidade Recebida",
        max_digits=15,
        decimal_places=2,
        help_text="Quantidade recebida do documento",
        null=True,
        blank=True,
    )

    def __str__(self):
        """Retorna o documento, a ficha e a quantidade recebida."""
        return f"{self.documento_recebimento} - {self.ficha_recebimento} ({self.quantidade_recebida})"

    class Meta:
        verbose_name = "Documento Ficha de Recebimento"
        verbose_name_plural = "Documentos Fichas de Recebimento"
        unique_together = ("ficha_recebimento", "documento_recebimento")


class OcorrenciaFichaRecebimento(ModeloBase):
    """Ocorrência registrada durante o recebimento.

    Registra faltas (``FALTA``), recusas (``RECUSA``) ou outros motivos
    (``OUTROS_MOTIVOS``), com a relação (cronograma, nota fiscal, total ou
    parcial), número da nota, quantidade e descrição. Apenas uma ocorrência
    do tipo ``RECUSA`` é permitida por ficha (validado no helper de
    criação).
    """
    TIPO_FALTA = "FALTA"
    TIPO_RECUSA = "RECUSA"
    TIPO_OUTROS = "OUTROS_MOTIVOS"

    TIPO_CHOICES = (
        (TIPO_FALTA, "Falta"),
        (TIPO_RECUSA, "Recusa"),
        (TIPO_OUTROS, "Outros Motivos"),
    )

    RELACAO_CRONOGRAMA = "CRONOGRAMA"
    RELACAO_NOTA_FISCAL = "NOTA_FISCAL"
    RELACAO_TOTAL = "TOTAL"
    RELACAO_PARCIAL = "PARCIAL"

    RELACAO_CHOICES = (
        (RELACAO_CRONOGRAMA, "Cronograma"),
        (RELACAO_NOTA_FISCAL, "Nota Fiscal"),
        (RELACAO_TOTAL, "Total"),
        (RELACAO_PARCIAL, "Parcial"),
    )

    ficha_recebimento = models.ForeignKey(
        FichaDeRecebimento,
        on_delete=models.CASCADE,
        related_name="ocorrencias",
        verbose_name="Ficha de Recebimento",
    )
    tipo = models.CharField(
        "Tipo de Ocorrência",
        max_length=20,
        choices=TIPO_CHOICES,
    )
    relacao = models.CharField(
        "Relação",
        max_length=20,
        choices=RELACAO_CHOICES,
        blank=True,
        null=True,
    )
    numero_nota = models.CharField(
        "Número da Nota",
        max_length=100,
        blank=True,
        null=True,
    )
    quantidade = models.CharField(
        "Quantidade",
        max_length=100,
        blank=True,
        null=True,
    )
    descricao = models.TextField(
        "Descrição",
        blank=True,
        null=True,
    )

    def __str__(self):
        """Retorna a ficha e o tipo da ocorrência."""
        return f"{self.ficha_recebimento} - {self.get_tipo_display()}"

    class Meta:
        verbose_name = "Ocorrência da Ficha de Recebimento"
        verbose_name_plural = "Ocorrências das Fichas de Recebimento"
        ordering = ["criado_em"]
