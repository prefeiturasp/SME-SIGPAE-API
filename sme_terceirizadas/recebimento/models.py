from django.core.exceptions import ValidationError
from django.db import models
from multiselectfield import MultiSelectField

from sme_terceirizadas.pre_recebimento.models import FichaTecnicaDoProduto
from sme_terceirizadas.pre_recebimento.models.cronograma import EtapasDoCronograma

from ..dados_comuns.behaviors import ModeloBase


class QuestaoConferencia(ModeloBase):
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
        return f"{self.questao}"

    class Meta:
        verbose_name = "Questão para Conferência"
        verbose_name_plural = "Questões para Conferência"

    def clean(self):
        super().clean()
        if self.pergunta_obrigatoria and not self.posicao:
            raise ValidationError(
                {"posicao": "Posição é obrigatória se a pergunta for obrigatória."}
            )


class QuestoesPorProduto(ModeloBase):
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
        return f"Questões da Ficha: {self.ficha_tecnica}"

    class Meta:
        verbose_name = "Questões por Produto"
        verbose_name_plural = "Questões por Produtos"


class FichaDeRecebimento(ModeloBase):
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
    numero_paletes = models.CharField(
        "Nº de Paletes",
        max_length=50,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_1 = models.CharField(
        "Peso da Embalagem Primária (1)",
        max_length=25,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_2 = models.CharField(
        "Peso da Embalagem Primária (2)",
        max_length=25,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_3 = models.CharField(
        "Peso da Embalagem Primária (3)",
        max_length=25,
        null=True,
        blank=True,
    )
    peso_embalagem_primaria_4 = models.CharField(
        "Peso da Embalagem Primária (4)",
        max_length=25,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        try:
            return f"Ficha de Recebimento - {str(self.etapa)}"

        except AttributeError:
            return f"Ficha de Recebimento {self.id}"

    class Meta:
        verbose_name = "Ficha de Recebimento"
        verbose_name_plural = "Fichas de Recebimentos"


class VeiculoFichaDeRecebimento(models.Model):
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
    quantidade_nota_fiscal = models.CharField(
        max_length=15,
        null=True,
        blank=True,
    )
    embalagens_nota_fiscal = models.CharField(
        "Quantidade de Embalagens da Nota Fiscal",
        max_length=15,
        null=True,
        blank=True,
    )
    quantidade_recebida = models.CharField(
        max_length=15,
        null=True,
        blank=True,
    )
    embalagens_recebidas = models.CharField(
        "Quantidade de Embalagens da Recebidas",
        max_length=15,
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
        return f"{self.numero} - {self.ficha_recebimento}"

    class Meta:
        verbose_name = "Veículo Ficha de Recebimento"
        verbose_name_plural = "Veículos Fichas de Recebimentos"
