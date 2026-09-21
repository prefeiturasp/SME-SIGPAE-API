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
from src.dados_comuns.constants import StringsVerboseNameModels
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

    questao = models.CharField(StringsVerboseNameModels.QUESTAO.value)
    tipo_questao = MultiSelectField("Tipo de Questão", choices=TIPO_QUESTAO_CHOICES)
    pergunta_obrigatoria = models.BooleanField(
        StringsVerboseNameModels.PERGUNTA_OBRIGATORIA.value, default=False
    )
    posicao = models.PositiveSmallIntegerField(
        StringsVerboseNameModels.POSICAO.value, blank=True, null=True
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=10, default=ATIVO)

    def __str__(self):
        """Retorna o texto da questão."""
        return f"{self.questao}"

    class Meta:
        verbose_name = StringsVerboseNameModels.QUESTAO_PARA_CONFERENCIA.value
        verbose_name_plural = StringsVerboseNameModels.QUESTOES_PARA_CONFERENCIA.value

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
        verbose_name=StringsVerboseNameModels.QUESTOES_REFERENTES_A_EMBALAGEM_PRIMARIA.value,
        related_name="questoes_primarias",
    )
    questoes_secundarias = models.ManyToManyField(
        QuestaoConferencia,
        verbose_name=StringsVerboseNameModels.QUESTOES_REFERENTES_A_EMBALAGEM_SECUNDARIA.value,
        related_name="questoes_secundarias",
    )

    def __str__(self):
        """Retorna a representação textual das questões da ficha técnica."""
        return f"Questões da Ficha: {self.ficha_tecnica}"

    class Meta:
        verbose_name = StringsVerboseNameModels.QUESTOES_POR_PRODUTO.value
        verbose_name_plural = StringsVerboseNameModels.QUESTOES_POR_PRODUTOS.value


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
        StringsVerboseNameModels.TIPO.value,
        max_length=7,
        choices=TIPO_CHOICES,
    )
    descricao = models.TextField(
        StringsVerboseNameModels.DESCRICAO_2.value,
        blank=True,
        null=True,
    )

    def __str__(self):
        """Retorna o tipo e a descrição da reposição."""
        return f"{self.tipo} - {self.descricao}"

    class Meta:
        verbose_name = (
            StringsVerboseNameModels.REPOSICAO_CRONOGRAMA_DA_FICHA_DE_RECEBIMENTO.value
        )
        verbose_name_plural = (
            StringsVerboseNameModels.REPOSICOES_CRONOGRAMAS_DAS_FICHAS_DE_RECEBIMENTO.value
        )
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
        verbose_name=StringsVerboseNameModels.ETAPA_DO_CRONOGRAMA.value,
    )
    data_entrega = models.DateField(
        StringsVerboseNameModels.DATA_DE_ENTREGA.value,
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
        StringsVerboseNameModels.LOTE_S_DO_FABRICANTE_OBSERVADO_S_ESTAO_DE_ACORDO.value,
        null=True,
        blank=True,
    )
    lote_fabricante_divergencia = models.CharField(
        StringsVerboseNameModels.DESCRICAO_DA_DIVERGENCIA_NOS_LOTE_S_DO_FABRICANTE.value,
        max_length=500,
        null=True,
        blank=True,
    )
    data_fabricacao_de_acordo = models.BooleanField(
        StringsVerboseNameModels.DATA_S_DE_FABRICACAO_OBSERVADA_S_ESTAO_DE_ACORDO.value,
        null=True,
        blank=True,
    )
    data_fabricacao_divergencia = models.CharField(
        StringsVerboseNameModels.DESCRICAO_DA_DIVERGENCIA_NAS_DATA_S_DE_FABRICACAO.value,
        max_length=500,
        null=True,
        blank=True,
    )
    data_validade_de_acordo = models.BooleanField(
        StringsVerboseNameModels.DATA_S_DE_VALIDADES_OBSERVADA_S_ESTAO_DE_ACORDO.value,
        null=True,
        blank=True,
    )
    data_validade_divergencia = models.CharField(
        StringsVerboseNameModels.DESCRICAO_DA_DIVERGENCIA_NAS_DATA_S_DE_VALIDADES.value,
        max_length=500,
        null=True,
        blank=True,
    )
    numero_lote_armazenagem = models.CharField(
        StringsVerboseNameModels.NO_DO_LOTE_ARMAZENAGEM.value,
        max_length=50,
        null=True,
        blank=True,
    )
    numero_paletes = models.IntegerField(
        StringsVerboseNameModels.NO_DE_PALETES.value,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_1 = models.FloatField(
        StringsVerboseNameModels.PESO_DA_EMBALAGEM_PRIMARIA_1.value,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_2 = models.FloatField(
        StringsVerboseNameModels.PESO_DA_EMBALAGEM_PRIMARIA_2.value,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_3 = models.FloatField(
        StringsVerboseNameModels.PESO_DA_EMBALAGEM_PRIMARIA_3.value,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_4 = models.FloatField(
        StringsVerboseNameModels.PESO_DA_EMBALAGEM_PRIMARIA_4.value,
        null=True,
        blank=True,
    )

    sistema_vedacao_embalagem_secundaria = models.TextField(
        StringsVerboseNameModels.SISTEMA_DE_VEDACAO_DA_EMBALAGEM_SECUNDARIA.value,
        null=True,
        blank=True,
    )

    questoes_conferencia = models.ManyToManyField(
        QuestaoConferencia,
        through="QuestaoFichaRecebimento",
        related_name="fichas_vinculadas",
    )

    houve_ocorrencia = models.BooleanField(
        StringsVerboseNameModels.HOUVE_OCORRENCIA.value,
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
        verbose_name = StringsVerboseNameModels.FICHA_DE_RECEBIMENTO.value
        verbose_name_plural = StringsVerboseNameModels.FICHAS_DE_RECEBIMENTOS.value


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
        StringsVerboseNameModels.NO_DO_VEICULO.value,
        max_length=25,
    )
    temperatura_recebimento = models.CharField(
        StringsVerboseNameModels.TEMPERATURA_DA_AREA_DE_RECEBIMENTO_C.value,
        max_length=10,
        null=True,
        blank=True,
    )
    temperatura_produto = models.CharField(
        StringsVerboseNameModels.TEMPERATURA_DO_PRODUTO_C.value,
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
        StringsVerboseNameModels.NO_SIF_SISBI_OU_SISP.value,
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
        StringsVerboseNameModels.QUANTIDADE_DE_EMBALAGENS_DA_NOTA_FISCAL.value,
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
        StringsVerboseNameModels.QUANTIDADE_DE_EMBALAGENS_RECEBIDAS.value,
        null=True,
        blank=True,
    )
    estado_higienico_adequado = models.BooleanField(
        StringsVerboseNameModels.ESTADO_HIGIENICO_SANITARIO_ADEQUADO.value,
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
        verbose_name = StringsVerboseNameModels.VEICULO_FICHA_DE_RECEBIMENTO.value
        verbose_name_plural = (
            StringsVerboseNameModels.VEICULOS_FICHAS_DE_RECEBIMENTOS.value
        )


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
        verbose_name = StringsVerboseNameModels.ARQUIVO_FICHA_DE_RECEBIMENTO.value
        verbose_name_plural = (
            StringsVerboseNameModels.ARQUIVOS_FICHAS_DE_RECEBIMENTOS.value
        )


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
        verbose_name=StringsVerboseNameModels.FICHA_DE_RECEBIMENTO.value,
    )
    questao_conferencia = models.ForeignKey(
        QuestaoConferencia,
        on_delete=models.CASCADE,
        verbose_name=StringsVerboseNameModels.QUESTAO_DE_CONFERENCIA.value,
    )
    resposta = models.BooleanField(
        StringsVerboseNameModels.RESPOSTA_SIM_NAO.value, null=True, blank=True
    )

    tipo_questao = models.CharField(choices=TIPO_QUESTAO_CHOICES)

    class Meta:
        verbose_name = StringsVerboseNameModels.QUESTAO_POR_FICHA_DE_RECEBIMENTO.value
        verbose_name_plural = (
            StringsVerboseNameModels.QUESTOES_POR_FICHAS_DE_RECEBIMENTO.value
        )
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
        verbose_name=StringsVerboseNameModels.FICHA_DE_RECEBIMENTO.value,
    )
    documento_recebimento = models.ForeignKey(
        DocumentoDeRecebimento,
        on_delete=models.CASCADE,
        related_name="fichas_documentos",
        verbose_name=StringsVerboseNameModels.DOCUMENTO_DE_RECEBIMENTO.value,
    )
    quantidade_recebida = models.DecimalField(
        StringsVerboseNameModels.QUANTIDADE_RECEBIDA.value,
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
        verbose_name = StringsVerboseNameModels.DOCUMENTO_FICHA_DE_RECEBIMENTO.value
        verbose_name_plural = (
            StringsVerboseNameModels.DOCUMENTOS_FICHAS_DE_RECEBIMENTO.value
        )
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
        verbose_name=StringsVerboseNameModels.FICHA_DE_RECEBIMENTO.value,
    )
    tipo = models.CharField(
        StringsVerboseNameModels.TIPO_DE_OCORRENCIA.value,
        max_length=20,
        choices=TIPO_CHOICES,
    )
    relacao = models.CharField(
        StringsVerboseNameModels.RELACAO.value,
        max_length=20,
        choices=RELACAO_CHOICES,
        blank=True,
        null=True,
    )
    numero_nota = models.CharField(
        StringsVerboseNameModels.NUMERO_DA_NOTA.value,
        max_length=100,
        blank=True,
        null=True,
    )
    quantidade = models.CharField(
        StringsVerboseNameModels.QUANTIDADE.value,
        max_length=100,
        blank=True,
        null=True,
    )
    descricao = models.TextField(
        StringsVerboseNameModels.DESCRICAO_2.value,
        blank=True,
        null=True,
    )

    def __str__(self):
        """Retorna a ficha e o tipo da ocorrência."""
        return f"{self.ficha_recebimento} - {self.get_tipo_display()}"

    class Meta:
        verbose_name = StringsVerboseNameModels.OCORRENCIA_DA_FICHA_DE_RECEBIMENTO.value
        verbose_name_plural = (
            StringsVerboseNameModels.OCORRENCIAS_DAS_FICHAS_DE_RECEBIMENTO.value
        )
        ordering = ["criado_em"]
