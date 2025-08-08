from django.core.validators import FileExtensionValidator, MinLengthValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from sme_sigpae_api.pre_recebimento.base.models import UnidadeMedida

from ...dados_comuns.behaviors import (
    CriadoPor,
    Logs,
    ModeloBase,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
)
from ...dados_comuns.fluxo_status import (
    FluxoFichaTecnicaDoProduto,
)
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...dados_comuns.validators import validate_file_size_10mb
from ...produto.models import (
    Fabricante,
    InformacaoNutricional,
    Marca,
    NomeDeProdutoEdital,
)
from ...terceirizada.models import Terceirizada


class FabricanteFichaTecnica(ModeloBase):
    """Modelo para armazenar informações do fabricante específicas para uma ficha técnica."""

    fabricante = models.ForeignKey(
        Fabricante,
        on_delete=models.SET_NULL,
        related_name="fichas_tecnicas_detalhes",
        blank=True,
        null=True,
    )
    cnpj = models.CharField(
        "CNPJ",
        validators=[MinLengthValidator(14)],
        max_length=14,
        blank=True,
    )
    cep = models.CharField("CEP", max_length=8, blank=True)
    endereco = models.CharField("Endereço", max_length=160, blank=True)
    numero = models.CharField("Número", max_length=10, blank=True)
    complemento = models.CharField("Complemento", max_length=250, blank=True)
    bairro = models.CharField("Bairro", max_length=150, blank=True)
    cidade = models.CharField("Cidade", max_length=150, blank=True)
    estado = models.CharField("Estado", max_length=150, blank=True)
    email = models.EmailField("E-mail", blank=True)
    telefone = models.CharField(
        "Telefone", max_length=13, validators=[MinLengthValidator(8)], blank=True
    )

    def __str__(self):
        return f"Ficha Técnica - {self.fabricante.nome if self.fabricante else 'Fabricante'}"

    class Meta:
        verbose_name = "Fabricante da Ficha Técnica"
        verbose_name_plural = "Fabricantes das Fichas Técnicas"


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
        "Número da Ficha Técnica", blank=True, max_length=250, unique=True
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
        FabricanteFichaTecnica,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_como_fabricante",
    )
    envasador_distribuidor = models.ForeignKey(
        FabricanteFichaTecnica,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="fichas_tecnicas_como_envasador_distribuidor",
        verbose_name="Envasador/Distribuidor",
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
        max_length=250,
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
        "Nome completo do Responsável Técnico", max_length=250, blank=True
    )
    habilitacao = models.CharField("Habilitação", max_length=250, blank=True)
    numero_registro_orgao = models.CharField(
        "Nº do Registro em Órgão Competente", max_length=250, blank=True
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
    fabricante_envasador_conferido = models.BooleanField(null=True)
    fabricante_envasador_correcoes = models.TextField(blank=True)
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
    responsavel_tecnico_correcoes = models.TextField(blank=True)
    modo_preparo_conferido = models.BooleanField(null=True)
    modo_preparo_correcoes = models.TextField(blank=True)
    outras_informacoes_conferido = models.BooleanField(null=True)

    @property
    def aprovada(self):
        return (
            (
                self.fabricante_envasador_conferido is True
                and not self.fabricante_envasador_correcoes
            )
            and (
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
            and (
                self.responsavel_tecnico_conferido is True
                and not self.responsavel_tecnico_correcoes
            )
            and (
                self.modo_preparo_conferido is True and not self.modo_preparo_correcoes
            )
            and self.outras_informacoes_conferido is True
        )

    class Meta:
        verbose_name = "Análise da Ficha Técnica"
        verbose_name_plural = "Análises das Fichas Técnicas"
