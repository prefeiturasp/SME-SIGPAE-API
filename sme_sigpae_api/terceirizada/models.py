import datetime

from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.db.utils import IntegrityError
from django_prometheus.models import ExportModelOperationsMixin

from sme_sigpae_api.dieta_especial.managers import EditalManager

from ..cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from ..cardapio.alteracao_tipo_alimentacao_cei.models import AlteracaoCardapioCEI
from ..cardapio.inversao_dia_cardapio.models import InversaoCardapio
from ..cardapio.suspensao_alimentacao.models import GrupoSuspensaoAlimentacao
from ..dados_comuns.behaviors import (
    Ativavel,
    IntervaloDeDia,
    Nomeavel,
    TemChaveExterna,
    TemIdentificadorExternoAmigavel,
    TemVinculos,
)
from ..dados_comuns.constants import ADMINISTRADOR_EMPRESA
from ..dados_comuns.utils import queryset_por_data
from ..escola.models import DiretoriaRegional, Lote
from ..inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
)
from ..kit_lanche.models import (
    SolicitacaoKitLancheAvulsa,
    SolicitacaoKitLancheCEIAvulsa,
    SolicitacaoKitLancheUnificada,
)
from ..perfil.models.usuario import Usuario


class Edital(ExportModelOperationsMixin("edital"), TemChaveExterna):
    numero = models.CharField(
        "Edital No", max_length=100, help_text="Número do Edital", unique=True
    )
    tipo_contratacao = models.CharField("Tipo de contratação", max_length=100)
    processo = models.CharField(
        "Processo Administrativo",
        max_length=100,
        help_text="Processo administrativo do edital",
    )
    objeto = models.TextField("objeto resumido")
    eh_imr = models.BooleanField("É IMR?", default=False)

    objects = EditalManager()

    def __str__(self):
        return f"{self.numero}"

    class Meta:
        verbose_name = "Edital"
        verbose_name_plural = "Editais"


# TODO: remover esse modelo (deprecado)
class Nutricionista(
    ExportModelOperationsMixin("nutricionista"), TemChaveExterna, Nomeavel
):
    # TODO: verificar a diferença dessa pra nutricionista da CODAE

    crn_numero = models.CharField("Nutricionista crn", max_length=160, blank=True)
    terceirizada = models.ForeignKey(
        "Terceirizada",
        on_delete=models.CASCADE,
        related_name="nutricionistas",
        blank=True,
        null=True,
    )
    admin = models.BooleanField(
        "É Administrador por parte das Terceirizadas?", default=False
    )
    # TODO: retornar aqui quando tiver um perfil definido
    contatos = models.ManyToManyField("dados_comuns.Contato", blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Nutricionista"
        verbose_name_plural = "Nutricionistas"
        ordering = ["-admin"]


class Terceirizada(
    ExportModelOperationsMixin("terceirizada"),
    TemChaveExterna,
    Ativavel,
    TemIdentificadorExternoAmigavel,
    TemVinculos,
):
    # Tipo de servico
    TERCEIRIZADA = "TERCEIRIZADA"
    DISTRIBUIDOR_ARMAZEM = "DISTRIBUIDOR_ARMAZEM"
    FORNECEDOR = "FORNECEDOR"
    FORNECEDOR_E_DISTRIBUIDOR = "FORNECEDOR_E_DISTRIBUIDOR"

    TIPO_SERVICO_CHOICES = (
        (TERCEIRIZADA, "Terceirizada"),
        (DISTRIBUIDOR_ARMAZEM, "Distribuidor (Armazém)"),
        (FORNECEDOR, "Fornecedor"),
        (FORNECEDOR_E_DISTRIBUIDOR, "Fornecedor e Distribuidor"),
    )

    # Tipo Empresa Choice
    CONVENCIONAL = "CONVENCIONAL"
    AGRICULTURA_FAMILIAR = "AGRICULTURA_FAMILIAR"

    TIPO_EMPRESA_CHOICES = (
        (CONVENCIONAL, "Convencional"),
        (AGRICULTURA_FAMILIAR, "Agricultura Familiar"),
        (TERCEIRIZADA, "Terceirizada"),
    )
    # Tipo Alimento Choice
    TIPO_ALIMENTO_CONGELADOS = "CONGELADOS_E_RESFRIADOS"
    TIPO_ALIMENTO_FLVO = "FLVO"
    TIPO_ALIMENTO_PAES_E_BOLO = "PAES_E_BOLO"
    TIPO_ALIMENTO_SECOS = "SECOS"
    # opção se faz necessária para atender o fluxo do alimentação terceirizada
    TIPO_ALIMENTO_TERCEIRIZADA = "TERCEIRIZADA"

    TIPO_ALIMENTO_NOMES = {
        TIPO_ALIMENTO_CONGELADOS: "Congelados e resfriados",
        TIPO_ALIMENTO_FLVO: "FLVO",
        TIPO_ALIMENTO_PAES_E_BOLO: "Pães & bolos",
        TIPO_ALIMENTO_SECOS: "Secos",
        TIPO_ALIMENTO_TERCEIRIZADA: "Terceirizada",
    }

    TIPO_ALIMENTO_CHOICES = (
        (TIPO_ALIMENTO_CONGELADOS, TIPO_ALIMENTO_NOMES[TIPO_ALIMENTO_CONGELADOS]),
        (TIPO_ALIMENTO_FLVO, TIPO_ALIMENTO_NOMES[TIPO_ALIMENTO_FLVO]),
        (TIPO_ALIMENTO_PAES_E_BOLO, TIPO_ALIMENTO_NOMES[TIPO_ALIMENTO_PAES_E_BOLO]),
        (TIPO_ALIMENTO_SECOS, TIPO_ALIMENTO_NOMES[TIPO_ALIMENTO_SECOS]),
    )

    nome_fantasia = models.CharField("Nome fantasia", max_length=160, blank=True)
    razao_social = models.CharField("Razao social", max_length=160, blank=True)
    cnpj = models.CharField("CNPJ", validators=[MinLengthValidator(14)], max_length=14)
    representante_legal = models.CharField(
        "Representante legal", max_length=160, blank=True
    )
    representante_telefone = models.CharField(
        "Representante contato (telefone)", max_length=160, blank=True
    )
    representante_email = models.CharField(
        "Representante contato (email)", max_length=160, blank=True
    )
    endereco = models.CharField("Endereco", max_length=160, blank=True)
    cep = models.CharField("CEP", max_length=8, blank=True)
    bairro = models.CharField("Bairro", max_length=150, blank=True)
    cidade = models.CharField("Cidade", max_length=150, blank=True)
    estado = models.CharField("Estado", max_length=150, blank=True)
    numero = models.CharField("Número", max_length=10, blank=True)
    complemento = models.CharField("Complemento", max_length=50, blank=True)
    responsavel_nome = models.CharField("Responsável", max_length=160, blank=True)
    responsavel_email = models.CharField(
        "Responsável contato (email)", max_length=160, blank=True
    )
    responsavel_cpf = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        unique=True,  # noqa DJ01
        validators=[MinLengthValidator(11)],
    )
    responsavel_telefone = models.CharField(
        "Responsável contato (telefone)", max_length=160, blank=True
    )
    responsavel_cargo = models.CharField("Responsável cargo", max_length=50, blank=True)
    tipo_empresa = models.CharField(
        choices=TIPO_EMPRESA_CHOICES, max_length=25, default=TERCEIRIZADA
    )
    tipo_servico = models.CharField(
        choices=TIPO_SERVICO_CHOICES, max_length=25, default=TERCEIRIZADA
    )
    tipo_alimento = models.CharField(
        choices=TIPO_ALIMENTO_CHOICES, max_length=25, default=TIPO_ALIMENTO_TERCEIRIZADA
    )
    criado_em = models.DateTimeField("Criado em", editable=False, auto_now_add=True)

    # TODO: criar uma tabela central (Instituição) para agregar Escola, DRE, Terc e CODAE???
    # e a partir dai a instituição que tem contatos e endereço?
    # o mesmo para pessoa fisica talvez?
    contatos = models.ManyToManyField("dados_comuns.Contato", blank=True)

    @property
    def editais(self):
        return list(
            set(
                self.contratos.filter(edital__isnull=False, encerrado=False)
                .values_list("edital__uuid", flat=True)
                .distinct()
            )
        )

    @property
    def vinculos_que_podem_ser_finalizados(self):
        return self.vinculos.filter(
            Q(data_inicial=None, data_final=None, ativo=False)
            | Q(  # noqa W504 esperando ativacao
                data_inicial__isnull=False, data_final=None, ativo=True
            )  # noqa W504 ativo
        ).exclude(perfil__nome=ADMINISTRADOR_EMPRESA)

    @property
    def quantidade_alunos(self):
        quantidade_total = 0
        for lote in self.lotes.all():
            quantidade_total += lote.quantidade_alunos
        return quantidade_total

    @property
    def nome(self):
        return self.nome_fantasia

    @property
    def eh_distribuidor(self):
        return self.tipo_servico in [
            self.DISTRIBUIDOR_ARMAZEM,
            self.FORNECEDOR_E_DISTRIBUIDOR,
        ]

    @property
    def eh_fornecedor(self):
        return self.tipo_servico in [self.FORNECEDOR, self.FORNECEDOR_E_DISTRIBUIDOR]

    @property
    def eh_terceirizada(self):
        return self.tipo_servico == self.TERCEIRIZADA

    @property
    def inclusoes_continuas_autorizadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            escola__lote__in=self.lotes.all(),
            status__in=[
                InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
                InclusaoAlimentacaoContinua.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inclusoes_normais_autorizadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            escola__lote__in=self.lotes.all(),
            status__in=[
                GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
                GrupoInclusaoAlimentacaoNormal.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inclusoes_continuas_reprovadas(self):
        return InclusaoAlimentacaoContinua.objects.filter(
            escola__lote__in=self.lotes.all(),
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_NEGOU_PEDIDO,
        )

    @property
    def solicitacao_kit_lanche_avulsa_autorizadas(self):
        return SolicitacaoKitLancheAvulsa.objects.filter(
            escola__lote__in=self.lotes.all(),
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheAvulsa.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def inclusoes_normais_reprovadas(self):
        return GrupoInclusaoAlimentacaoNormal.objects.filter(
            escola__lote__in=self.lotes.all(),
            status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_NEGOU_PEDIDO,
        )

    # TODO: talvez fazer um manager genérico pra fazer esse filtro

    def inclusoes_continuas_das_minhas_escolas_no_prazo_vencendo(self, filtro_aplicado):
        if filtro_aplicado == "hoje":
            # TODO: rever filtro hoje que nao é mais usado
            inclusoes_continuas = InclusaoAlimentacaoContinua.objects
        else:  # se o filtro nao for hoje, filtra o padrao
            inclusoes_continuas = InclusaoAlimentacaoContinua.vencidos
        return inclusoes_continuas.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def inclusoes_continuas_das_minhas_escolas_no_prazo_limite(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_7_dias":
            inclusoes_continuas = InclusaoAlimentacaoContinua.desta_semana
        else:
            inclusoes_continuas = InclusaoAlimentacaoContinua.objects  # type: ignore
        return inclusoes_continuas.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def inclusoes_continuas_das_minhas_escolas_no_prazo_regular(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_30_dias":
            inclusoes_continuas = InclusaoAlimentacaoContinua.deste_mes
        elif filtro_aplicado == "daqui_a_7_dias":
            inclusoes_continuas = InclusaoAlimentacaoContinua.desta_semana  # type: ignore
        else:
            inclusoes_continuas = InclusaoAlimentacaoContinua.objects  # type: ignore
        return inclusoes_continuas.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def inclusoes_normais_das_minhas_escolas_no_prazo_vencendo(self, filtro_aplicado):
        if filtro_aplicado == "hoje":
            # TODO: rever filtro hoje que nao é mais usado
            inclusoes_normais = GrupoInclusaoAlimentacaoNormal.objects
        else:
            inclusoes_normais = GrupoInclusaoAlimentacaoNormal.vencidos
        return inclusoes_normais.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def inclusoes_normais_das_minhas_escolas_no_prazo_limite(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_7_dias":
            inclusoes_normais = GrupoInclusaoAlimentacaoNormal.desta_semana
        else:
            inclusoes_normais = GrupoInclusaoAlimentacaoNormal.objects  # type: ignore
        return inclusoes_normais.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def inclusoes_normais_das_minhas_escolas_no_prazo_regular(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_30_dias":
            inclusoes_normais = GrupoInclusaoAlimentacaoNormal.deste_mes
        elif filtro_aplicado == "daqui_a_7_dias":
            inclusoes_normais = GrupoInclusaoAlimentacaoNormal.desta_semana  # type: ignore
        else:
            inclusoes_normais = GrupoInclusaoAlimentacaoNormal.objects  # type: ignore
        return inclusoes_normais.filter(
            status=InclusaoAlimentacaoContinua.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def alteracoes_cardapio_das_minhas_escolas_no_prazo_vencendo(self, filtro_aplicado):
        if filtro_aplicado == "hoje":
            # TODO: rever filtro hoje que nao é mais usado
            alteracoes_cardapio = AlteracaoCardapio.objects
        else:
            alteracoes_cardapio = AlteracaoCardapio.vencidos
        return alteracoes_cardapio.filter(
            status=AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def alteracoes_cardapio_das_minhas_escolas_no_prazo_limite(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_7_dias":
            alteracoes_cardapio = AlteracaoCardapio.desta_semana
        else:
            alteracoes_cardapio = AlteracaoCardapio.objects  # type: ignore
        return alteracoes_cardapio.filter(
            status=AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def alteracoes_cardapio_das_minhas_escolas_no_prazo_regular(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_30_dias":
            alteracoes_cardapio = AlteracaoCardapio.deste_mes
        elif filtro_aplicado == "daqui_a_7_dias":
            alteracoes_cardapio = AlteracaoCardapio.desta_semana  # type: ignore
        else:
            alteracoes_cardapio = AlteracaoCardapio.objects  # type: ignore
        return alteracoes_cardapio.filter(
            status=AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def alteracoes_cardapio_das_minhas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapio)
        return queryset.filter(
            status__in=[
                AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
                AlteracaoCardapio.workflow_class.CODAE_QUESTIONADO,
            ],
            escola__lote__in=self.lotes.all(),
        )

    def alteracoes_cardapio_cei_das_minhas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, AlteracaoCardapioCEI)
        return queryset.filter(
            status__in=[
                AlteracaoCardapioCEI.workflow_class.CODAE_AUTORIZADO,
                AlteracaoCardapioCEI.workflow_class.CODAE_QUESTIONADO,
            ],
            escola__lote__in=self.lotes.all(),
        )

    def grupos_inclusoes_alimentacao_normal_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, GrupoInclusaoAlimentacaoNormal)
        return queryset.filter(
            status=AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def inclusoes_alimentacao_de_cei_das_minhas_escolas(self, filtro_aplicado):
        return self.filtra_solicitacoes_minhas_escolas_a_validar_por_data(
            filtro_aplicado, InclusaoAlimentacaoDaCEI
        )

    def inclusoes_alimentacao_continua_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, InclusaoAlimentacaoContinua)
        return queryset.filter(
            status=AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
            escola__lote__in=self.lotes.all(),
        )

    def suspensoes_alimentacao_das_minhas_escolas(self, filtro_aplicado):
        queryset = queryset_por_data(filtro_aplicado, GrupoSuspensaoAlimentacao)
        return queryset.filter(
            status=GrupoSuspensaoAlimentacao.workflow_class.INFORMADO,
            escola__lote__in=self.lotes.all(),
        )

    @property
    def alteracoes_cardapio_autorizadas(self):
        return AlteracaoCardapio.objects.filter(
            escola__lote__in=self.lotes.all(),
            status__in=[
                AlteracaoCardapio.workflow_class.CODAE_AUTORIZADO,
                AlteracaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    @property
    def alteracoes_cardapio_reprovadas(self):
        return AlteracaoCardapio.objects.filter(
            escola__lote__in=self.lotes.all(),
            status=AlteracaoCardapio.workflow_class.CODAE_NEGOU_PEDIDO,
        )

    #
    # Inversão de dia de cardápio
    #

    def inversoes_cardapio_das_minhas_escolas(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_7_dias":
            inversoes_cardapio = InversaoCardapio.desta_semana
        elif filtro_aplicado == "daqui_a_30_dias":
            inversoes_cardapio = InversaoCardapio.deste_mes  # type: ignore
        else:
            inversoes_cardapio = InversaoCardapio.objects  # type: ignore
        return inversoes_cardapio.filter(
            escola__lote__in=self.lotes.all(),
            status=InversaoCardapio.workflow_class.CODAE_AUTORIZADO,
        )

    @property
    def inversoes_cardapio_autorizadas(self):
        return InversaoCardapio.objects.filter(
            escola__lote__in=self.lotes.all(),
            status__in=[
                InversaoCardapio.workflow_class.CODAE_AUTORIZADO,
                InversaoCardapio.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        )

    #
    # Solicitação Unificada
    #

    def solicitacoes_unificadas_das_minhas_escolas(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_7_dias":
            solicitacoes_unificadas = SolicitacaoKitLancheUnificada.desta_semana
        elif filtro_aplicado == "daqui_a_30_dias":
            solicitacoes_unificadas = SolicitacaoKitLancheUnificada.deste_mes  # type: ignore
        else:
            solicitacoes_unificadas = SolicitacaoKitLancheUnificada.objects  # type: ignore
        return solicitacoes_unificadas.filter(
            escolas_quantidades__escola__lote__in=self.lotes.all(),
            status=SolicitacaoKitLancheUnificada.workflow_class.CODAE_AUTORIZADO,
        ).distinct()

    @property
    def solicitacoes_unificadas_autorizadas(self):
        return SolicitacaoKitLancheUnificada.objects.filter(
            escolas_quantidades__escola__lote__in=self.lotes.all(),
            status__in=[
                SolicitacaoKitLancheUnificada.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheUnificada.workflow_class.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
        ).distinct()

    def solicitacoes_kit_lanche_das_minhas_escolas_a_validar(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_7_dias":
            solicitacoes_kit_lanche = SolicitacaoKitLancheAvulsa.desta_semana
        elif filtro_aplicado == "daqui_a_30_dias":
            solicitacoes_kit_lanche = SolicitacaoKitLancheAvulsa.deste_mes  # type: ignore
        else:
            solicitacoes_kit_lanche = SolicitacaoKitLancheAvulsa.objects  # type: ignore
        return solicitacoes_kit_lanche.filter(
            escola__lote__in=self.lotes.all(),
            status__in=[
                SolicitacaoKitLancheAvulsa.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheAvulsa.workflow_class.CODAE_QUESTIONADO,
            ],
        )

    def solicitacoes_kit_lanche_cei_das_minhas_escolas_a_validar(self, filtro_aplicado):
        if filtro_aplicado == "daqui_a_7_dias":
            solicitacoes_kit_lanche = SolicitacaoKitLancheCEIAvulsa.desta_semana
        elif filtro_aplicado == "daqui_a_30_dias":
            solicitacoes_kit_lanche = SolicitacaoKitLancheCEIAvulsa.deste_mes  # type: ignore
        else:
            solicitacoes_kit_lanche = SolicitacaoKitLancheCEIAvulsa.objects  # type: ignore
        return solicitacoes_kit_lanche.filter(
            escola__lote__in=self.lotes.all(),
            status__in=[
                SolicitacaoKitLancheCEIAvulsa.workflow_class.CODAE_AUTORIZADO,
                SolicitacaoKitLancheCEIAvulsa.workflow_class.CODAE_QUESTIONADO,
            ],
        )

    def emails_por_modulo(self, modulo_nome):
        return list(
            self.emails_terceirizadas.filter(modulo__nome=modulo_nome).values_list(
                "email", flat=True
            )
        )

    @staticmethod
    def todos_emails_por_modulo(modulo_nome):
        return list(
            EmailTerceirizadaPorModulo.objects.filter(
                modulo__nome=modulo_nome
            ).values_list("email", flat=True)
        )

    def __str__(self):
        return f"{self.nome_fantasia}"

    class Meta:
        verbose_name = "Terceirizada"
        verbose_name_plural = "Terceirizadas"


class Modalidade(ExportModelOperationsMixin("modalidade"), TemChaveExterna, Nomeavel):
    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Modalidade"
        verbose_name_plural = "Modalidades"


class Contrato(ExportModelOperationsMixin("contato"), TemChaveExterna):
    numero = models.CharField("No do contrato", max_length=100, unique=True)
    processo = models.CharField(
        "Processo Administrativo",
        max_length=100,
        help_text="Processo administrativo do contrato",
    )
    data_proposta = models.DateField("Data da proposta", blank=True, null=True)
    lotes = models.ManyToManyField(Lote, related_name="contratos_do_lote", blank=True)
    terceirizada = models.ForeignKey(
        Terceirizada,
        on_delete=models.PROTECT,
        related_name="contratos",
        blank=True,
        null=True,
    )
    edital = models.ForeignKey(
        Edital,
        on_delete=models.CASCADE,
        related_name="contratos",
        blank=True,
        null=True,
    )
    diretorias_regionais = models.ManyToManyField(
        DiretoriaRegional, related_name="contratos_da_diretoria_regional", blank=True
    )
    encerrado = models.BooleanField("Encerrado?", default=False)
    data_hora_encerramento = models.DateTimeField(
        "Data e hora do encerramento", null=True, default=None
    )
    ata = models.CharField("No da Ata", max_length=100, blank=True)
    modalidade = models.ForeignKey(
        Modalidade,
        on_delete=models.PROTECT,
        related_name="contratos",
        blank=True,
        null=True,
    )
    numero_pregao = models.CharField(
        "Nº do Pregão Eletrônico", max_length=100, blank=True
    )
    numero_chamada_publica = models.CharField(
        "Nº da Chamada Pública", max_length=100, blank=True
    )

    def __str__(self):
        return f"Contrato:{self.numero} Processo: {self.processo}"

    @property
    def pregao_chamada_publica(self):
        # Verificar com essa função irá se comportar com os novos valores de modalidade
        if self.modalidade and self.modalidade.nome == "Pregão Eletrônico":
            return self.numero_pregao
        elif self.modalidade and self.modalidade.nome == "Chamada Pública":
            return self.numero_chamada_publica
        else:
            return self.numero_chamada_publica

    @classmethod
    def encerra_contrato(cls, uuid):
        contrato = cls.objects.get(uuid=uuid)
        if contrato.encerrado:
            raise IntegrityError(
                "Contrato já encerrado. Não é possivel encerrar novamente!"
            )
        contrato.encerrado = True
        contrato.data_hora_encerramento = datetime.datetime.now()
        contrato.save()

        dados_encerramento = {
            "encerrado": contrato.encerrado,
            "data_hora_encerramento": contrato.data_hora_encerramento.strftime(
                "%d/%m/%Y - %H:%M"
            ),
        }

        return dados_encerramento

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"


class VigenciaContrato(
    ExportModelOperationsMixin("vigencia_contrato"), TemChaveExterna, IntervaloDeDia
):
    ATIVO = "ativo"
    VENCIDO = "vencido"
    PROXIMO_AO_VENCIMENTO = "proximo_ao_vencimento"
    ENCERRADO = "encerrado"

    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.CASCADE,
        related_name="vigencias",
        null=True,
        blank=True,
    )

    @property
    def status(self) -> str:
        hoje = datetime.date.today()
        daqui_30_dias = datetime.date.today() + datetime.timedelta(days=30)
        if self.contrato.encerrado:
            return self.ENCERRADO
        elif not self.data_final:
            return self.ATIVO

        if self.data_final < hoje and not self.contrato.encerrado:
            return self.VENCIDO
        elif hoje <= self.data_final <= daqui_30_dias and not self.contrato.encerrado:
            return self.PROXIMO_AO_VENCIMENTO
        else:
            return self.ATIVO

    def __str__(self) -> str:
        return (
            f"Contrato:{self.contrato.numero} {self.data_inicial} a {self.data_final}"
        )

    class Meta:
        verbose_name = "Vigência de contrato"
        verbose_name_plural = "Vigências de contrato"


class Modulo(ExportModelOperationsMixin("modulo"), TemChaveExterna):
    nome = models.CharField("Nome", max_length=100)

    def __str__(self):
        return f"{self.nome}"

    class Meta:
        verbose_name = "Módulo"
        verbose_name_plural = "Módulos"


class EmailTerceirizadaPorModulo(
    ExportModelOperationsMixin("email_terceirizada_por_modulo"), TemChaveExterna
):
    email = models.EmailField("E-mail")
    terceirizada = models.ForeignKey(
        Terceirizada, on_delete=models.CASCADE, related_name="emails_terceirizadas"
    )
    modulo = models.ForeignKey(
        Modulo, on_delete=models.CASCADE, related_name="emails_terceirizadas"
    )
    criado_em = models.DateTimeField("Criado em", editable=False, auto_now_add=True)
    criado_por = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="emails_terceirizadas"
    )

    def __str__(self):
        return f"{self.email} - {self.terceirizada.nome_fantasia} - {self.modulo.nome}"

    class Meta:
        verbose_name = "E-mail de Terceirizada por Módulos"
        verbose_name_plural = "E-mails de Terceirizadas por Módulos"
        unique_together = ("email", "terceirizada", "modulo")
